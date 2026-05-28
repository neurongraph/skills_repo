#!/usr/bin/env python3
"""
Get top k todos from todo.txt file using composite urgency scoring.
Urgency = priority_score * 3 + proximity_score

Priority score: A=26, B=25, ... Z=1, none=0
Proximity score: linear 60→0 from -30 days overdue to +30 days future (clamped)

Usage:
  python3 get_top_todos.py <path_to_todo_file> [k]
"""

import re
import sys
from datetime import date, datetime
from pathlib import Path

def compute_urgency(priority, due_date, today):
    priority_score = 0
    if priority:
        priority_score = 27 - (ord(priority) - ord('A') + 1)

    if due_date is None:
        proximity_score = 0
    else:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        days_until = (due - today).days
        proximity_score = max(0, min(60, 30 - days_until))

    return priority_score * 3 + proximity_score

def is_pure_url(line):
    stripped = line.strip()
    return stripped.startswith("https://") and "@" not in stripped and "+" not in stripped and "due:" not in stripped

def get_top_todos(todo_file_path, k=10):
    today = date.today()

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    tasks = []
    for line in lines:
        line = line.rstrip()
        if not line or line.startswith("---") or line.startswith("## @") or line.startswith("### +"):
            continue
        if is_pure_url(line):
            continue
        if line.startswith("x "):
            continue

        priority_match = re.match(r'^\(([A-Z])\)\s+(.*)', line)
        if priority_match:
            priority = priority_match.group(1)
            desc = priority_match.group(2)
        else:
            priority = None
            desc = line

        due_match = re.search(r'due:(\d{4}-\d{2}-\d{2})', desc)
        due_date = due_match.group(1) if due_match else None

        urgency = compute_urgency(priority, due_date, today)

        tasks.append({
            'line': line,
            'priority': priority,
            'due_date': due_date,
            'desc': desc,
            'urgency': urgency
        })

    tasks.sort(key=lambda x: x['urgency'], reverse=True)

    return tasks[:k]

def format_output(tasks, today):
    output = [f"Top {len(tasks)} Todos (scored {today})\n"]
    output.append(f"| # | Priority | Due Date | Score | Description |")
    output.append(f"|---|----------|----------|-------|-------------|")
    for i, task in enumerate(tasks, 1):
        priority = task['priority'] if task['priority'] else "—"
        due = task['due_date'] if task['due_date'] else "—"
        desc = task['desc']
        output.append(f"| {i} | {priority} | {due} | {task['urgency']} | {desc} |")
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 get_top_todos.py <path_to_todo_file> [k]")
        sys.exit(1)

    todo_file = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) >= 3 else 10

    if not Path(todo_file).exists():
        print(f"Error: File not found: {todo_file}", file=sys.stderr)
        sys.exit(1)

    tasks = get_top_todos(todo_file, k)
    print(format_output(tasks, date.today()))
