#!/usr/bin/env python3
"""
filter_tasks.py — filter and display Obsidian tasks from JSON input.

Reads the JSON produced by `obsidian tasks format=json` on stdin and applies
the requested filter, then prints matching raw task lines to stdout.

Usage:
  obsidian tasks todo format=json | python3 filter_tasks.py [option]
  obsidian tasks format=json      | python3 filter_tasks.py --projects
  obsidian tasks format=json      | python3 filter_tasks.py --project-summary

Options:
  --today           Tasks due today
  --overdue         Tasks past their due date
  --no-due          Tasks with no due date set
  --due-soon [N]    Tasks due within N days (default 7)
  --priority LEVEL  Filter by priority: highest, high, normal, low, lowest
  --urgent          High/highest priority + overdue/due-today tasks, urgency-sorted
  --next-action     All incomplete tasks sorted by urgency score (default)
  --project NAME    Incomplete tasks tagged #Project/NAME, urgency-sorted
  --projects        List all distinct project names found in tasks
  --project-summary Summary table: project · open · done · overdue
  --recurring       Tasks with a recurrence pattern
"""

import json
import sys
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

# Allow importing task_utils / project_utils from the same scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))
from task_utils import parse_task, suggest_next_actions, due_label
from project_utils import list_projects, format_project_summary, open_tasks_for_project


def load_lines() -> list[str]:
    """Read JSON from stdin and return a list of raw task line strings.

    The obsidian CLI may emit warning/info lines before the JSON payload.
    We strip those by finding the first '[' that starts a JSON array.
    """
    raw = sys.stdin.read()

    # Find the start of the JSON array, skipping any CLI warning lines
    start = raw.find("[")
    if start == -1:
        print("filter_tasks.py: no JSON array found in stdin", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw[start:])
    except json.JSONDecodeError as exc:
        print(f"filter_tasks.py: could not parse JSON from stdin: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("filter_tasks.py: expected a JSON array from stdin", file=sys.stderr)
        sys.exit(1)

    # Each item has a "text" field with the raw task line
    return [item["text"] for item in data if "text" in item]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter Obsidian tasks JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--today",          action="store_true",        help="Tasks due today")
    parser.add_argument("--overdue",        action="store_true",        help="Tasks past due date")
    parser.add_argument("--no-due",         action="store_true",        help="Tasks with no due date")
    parser.add_argument("--due-soon",       type=int, nargs="?", const=7, metavar="DAYS",
                                                                        help="Due within N days (default 7)")
    parser.add_argument("--priority",       metavar="LEVEL",            help="highest | high | normal | low | lowest")
    parser.add_argument("--urgent",         action="store_true",        help="High/highest priority + overdue/due-today")
    parser.add_argument("--next-action",    action="store_true",        help="All tasks sorted by urgency score")
    parser.add_argument("--project",        metavar="NAME",             help="Open tasks tagged #Project/NAME (accepts bare name, Project/NAME, or #Project/NAME)")
    parser.add_argument("--projects",       action="store_true",        help="List project names")
    parser.add_argument("--project-summary",action="store_true",        help="Project summary table")
    parser.add_argument("--recurring",      action="store_true",        help="Tasks with recurrence")
    args = parser.parse_args()

    lines = load_lines()
    today = datetime.now().date()

    # ── Project-level commands ───────────────────────────────────────────────

    if args.projects:
        for p in list_projects(lines):
            print(p)
        return

    if args.project_summary:
        print(format_project_summary(lines))
        return

    if args.project:
        tasks = open_tasks_for_project(lines, args.project)
        for t in tasks:
            label = due_label(t.get("due_date"))
            suffix = f"  ({label})" if label else ""
            print(f"[{t['urgency_score']:2d}] {t['raw']}{suffix}")
        return

    # ── next-action / default ────────────────────────────────────────────────

    no_filter_given = not any([
        args.today, args.overdue, args.no_due, args.due_soon is not None,
        args.priority, args.urgent, args.recurring,
    ])

    if args.next_action or no_filter_given:
        tasks = suggest_next_actions(lines)
        for t in tasks:
            label = due_label(t.get("due_date"))
            suffix = f"  ({label})" if label else ""
            print(f"[{t['urgency_score']:2d}] {t['raw']}{suffix}")
        return

    # ── Per-task filters ─────────────────────────────────────────────────────

    parsed = [parse_task(line) for line in lines]

    if args.today:
        today_str = today.strftime("%Y-%m-%d")
        filtered = [t for t in parsed if t["due_date"] == today_str]

    elif args.overdue:
        filtered = [
            t for t in parsed
            if t["due_date"] and _parse_date(t["due_date"]) < today
        ]

    elif args.no_due:
        filtered = [t for t in parsed if not t["due_date"]]

    elif args.due_soon is not None:
        cutoff = today + timedelta(days=args.due_soon)
        filtered = [
            t for t in parsed
            if t["due_date"] and today <= _parse_date(t["due_date"]) <= cutoff
        ]

    elif args.priority:
        level = args.priority.lower()
        filtered = [t for t in parsed if t["priority"] == level]

    elif args.urgent:
        filtered = [
            t for t in parsed
            if t["priority"] in ("high", "highest")
            or (t["due_date"] and _parse_date(t["due_date"]) <= today)
        ]
        # Reuse urgency scoring for ordering
        scored = suggest_next_actions([t["raw"] for t in filtered])
        for t in scored:
            label = due_label(t.get("due_date"))
            suffix = f"  ({label})" if label else ""
            print(f"[{t['urgency_score']:2d}] {t['raw']}{suffix}")
        return

    elif args.recurring:
        filtered = [t for t in parsed if t["recurrence"]]

    else:
        filtered = parsed

    for t in filtered:
        print(t["raw"])


def _parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string, returning a very-far-future date on failure."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return date(9999, 12, 31)


if __name__ == "__main__":
    main()
