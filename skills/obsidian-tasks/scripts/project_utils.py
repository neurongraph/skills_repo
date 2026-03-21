#!/usr/bin/env python3
"""
Obsidian Tasks — Project Utilities

Functions for discovering, grouping, and summarising tasks by project.
A "project" is identified by a #Project/<Name> hierarchical tag in a task line
(e.g. #Project/Frontend, #Project/Alpha). The project key stored internally is the
tag path without the leading # (e.g. "Project/Frontend").

This format enables Task Genius plugin views in Obsidian.

Complements task_utils.py — import both together.
Dependency: obsidian-cli skill for vault operations.
"""

from datetime import datetime
from typing import Dict, List, Optional

from task_utils import parse_task, suggest_next_actions


# ---------------------------------------------------------------------------
# Project discovery
# ---------------------------------------------------------------------------


def list_projects(task_lines: List[str]) -> List[str]:
    """
    Return a sorted list of all distinct project names found in task_lines.

    A project is any #Project/<Name> tag in a task (e.g. #Project/Frontend → "Project/Frontend").

    Args:
        task_lines: List of raw task line strings.

    Returns:
        Sorted list of unique project name strings (e.g. ["Project/Alpha", "Project/Frontend"]).
    """
    projects: set = set()
    for task in (parse_task(line) for line in task_lines):
        projects.update(task["projects"])
    return sorted(projects)


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------


def group_tasks_by_project(task_lines: List[str]) -> Dict[str, List[Dict]]:
    """
    Group parsed tasks by project name.

    Tasks with no project link are grouped under "No Project".
    Tasks linked to multiple projects appear under each one.

    Args:
        task_lines: List of raw task line strings.

    Returns:
        Dict mapping project name → list of parsed task dicts.
        Projects are sorted alphabetically; "No Project" is last.
    """
    groups: Dict[str, List[Dict]] = {}

    for task in (parse_task(line) for line in task_lines):
        if task["projects"]:
            for project in task["projects"]:
                groups.setdefault(project, []).append(task)
        else:
            groups.setdefault("No Project", []).append(task)

    # Sort alphabetically, "No Project" always last
    return dict(
        sorted(groups.items(), key=lambda kv: ("\xff" if kv[0] == "No Project" else kv[0]))
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def project_summary(task_lines: List[str]) -> List[Dict]:
    """
    Return a per-project summary with task counts.

    Args:
        task_lines: List of raw task line strings.

    Returns:
        List of summary dicts, sorted by open-task count descending:

            {
                "project": str,   # project name
                "total":   int,   # all tasks (open + done)
                "open":    int,   # incomplete tasks
                "done":    int,   # completed tasks
                "overdue": int,   # incomplete tasks past their due date
            }
    """
    groups = group_tasks_by_project(task_lines)
    today = datetime.now().date()
    summaries = []

    for project, tasks in groups.items():
        done = sum(1 for t in tasks if t["completed"])
        open_count = len(tasks) - done
        overdue = 0

        for task in tasks:
            if task["completed"]:
                continue
            if task["due_date"]:
                try:
                    due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                    if due < today:
                        overdue += 1
                except ValueError:
                    pass

        summaries.append({
            "project": project,
            "total":   len(tasks),
            "open":    open_count,
            "done":    done,
            "overdue": overdue,
        })

    # Sort by open count desc, then overdue desc as tiebreaker
    summaries.sort(key=lambda x: (x["open"], x["overdue"]), reverse=True)
    return summaries


# ---------------------------------------------------------------------------
# Per-project task queries
# ---------------------------------------------------------------------------


def open_tasks_for_project(
    task_lines: List[str],
    project_name: str,
) -> List[Dict]:
    """
    Return incomplete tasks for a specific project, sorted by urgency score.

    Matches tasks that contain the #Project/<project_name> tag.
    project_name may be passed as "ICA", "Project/Frontend", or "#Project/Frontend" —
    all are normalised to match "#Project/<Name>" in the task line.

    Args:
        task_lines:   List of raw task line strings.
        project_name: Project name, e.g. "ICA", "Project/Frontend", or "#Project/Frontend".

    Returns:
        Incomplete parsed task dicts sorted by urgency (highest first).
    """
    tag = _normalise_project_tag(project_name).lower()
    matching = [line for line in task_lines if tag in line.lower()]
    return suggest_next_actions(matching)


def done_tasks_for_project(
    task_lines: List[str],
    project_name: str,
) -> List[Dict]:
    """
    Return completed tasks for a specific project, sorted by done date descending.

    Args:
        task_lines:   List of raw task line strings.
        project_name: Project name, e.g. "ICA", "Project/Frontend", or "#Project/Frontend".

    Returns:
        Completed parsed task dicts sorted by done_date (most recent first).
    """
    tag = _normalise_project_tag(project_name)
    matching = [line for line in task_lines if tag in line]
    tasks = [t for t in (parse_task(line) for line in matching) if t["completed"]]
    tasks.sort(key=lambda t: t["done_date"] or "", reverse=True)
    return tasks


def _normalise_project_tag(project_name: str) -> str:
    """Normalise a project name to its #Project/<Name> tag string for matching."""
    name = project_name.lstrip("#")
    if not name.startswith("Project/"):
        name = f"Project/{name}"
    return f"#{name}"


# ---------------------------------------------------------------------------
# Formatted output helpers
# ---------------------------------------------------------------------------


def format_project_summary(task_lines: List[str]) -> str:
    """
    Return a formatted string listing all projects with their task counts.

    Example output::

        Projects (3)
        ─────────────────────────────
        Backend Infra        2 open  1 done  1 overdue
        Website Redesign     2 open  1 done  0 overdue
        ─────────────────────────────
        No Project           1 open  0 done  0 overdue

    Args:
        task_lines: List of raw task line strings.

    Returns:
        Multi-line formatted string.
    """
    summaries = project_summary(task_lines)
    if not summaries:
        return "No projects found."

    # Separate "No Project" from named projects for display
    named = [s for s in summaries if s["project"] != "No Project"]
    unlinked = [s for s in summaries if s["project"] == "No Project"]

    col_width = max((len(s["project"]) for s in summaries), default=10) + 2
    divider = "\u2500" * (col_width + 30)

    lines = [f"Projects ({len(named)})", divider]
    for s in named:
        overdue_str = f"  \u26a0\ufe0f {s['overdue']} overdue" if s["overdue"] else ""
        lines.append(
            f"  {s['project']:<{col_width}}"
            f"{s['open']} open  {s['done']} done{overdue_str}"
        )
    if unlinked:
        lines.append(divider)
        for s in unlinked:
            lines.append(
                f"  {s['project']:<{col_width}}"
                f"{s['open']} open  {s['done']} done"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = [
        "- [ ] Design homepage #Project/WebRedesign 🔼 📅 2026-03-22",
        "- [ ] Write copy #Project/WebRedesign 📅 2026-03-25",
        "- [x] Kick-off meeting #Project/WebRedesign ✅ 2026-03-18",
        "- [ ] Set up CI #Project/BackendInfra 🔼 📅 2026-03-20",
        "- [ ] Write tests #Project/BackendInfra",
        "- [ ] Send weekly update",
    ]

    print("=== Projects ===")
    for p in list_projects(sample):
        print(f"  {p}")

    print("\n=== Summary ===")
    print(format_project_summary(sample))

    print("\n=== WebRedesign — open tasks by urgency ===")
    for t in open_tasks_for_project(sample, "WebRedesign"):
        print(f"  [{t['urgency_score']:2d}] {t['description']}  due={t['due_date']}")

    print("\n=== WebRedesign — completed tasks ===")
    for t in done_tasks_for_project(sample, "WebRedesign"):
        print(f"  ✅ {t['description']}  done={t['done_date']}")
