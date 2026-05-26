#!/usr/bin/env python3
"""
Get top 6 todos from todo.txt file.
Returns the top 3 by priority and top 3 by due date (combining and deduplicating).

Usage:
  python3 get_top_todos.py <path_to_todo_file>
"""

import re
import sys
from pathlib import Path

def get_top_todos(todo_file_path):
    """Parse todo file and return top 6 todos (3 by priority, 3 by due date)."""

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    tasks = []
    for line in lines:
        line = line.rstrip()
        # Skip empty lines, headers, separators, URLs
        if not line or line.startswith("---") or line.startswith("## @") or line.startswith("### +") or line.startswith("https://"):
            continue

        # Skip completed tasks
        if line.startswith("x "):
            continue

        # Extract priority
        priority_match = re.match(r'^\(([A-Z])\)\s+(.*)', line)
        if priority_match:
            priority = priority_match.group(1)
            desc = priority_match.group(2)
            priority_num = ord(priority)  # A=65, B=66, etc.
        else:
            priority = None
            priority_num = 90  # Z = lowest priority
            desc = line

        # Extract due date
        due_match = re.search(r'due:(\d{4}-\d{2}-\d{2})', desc)
        if due_match:
            due_date = due_match.group(1)
        else:
            due_date = "9999-12-31"

        tasks.append({
            'line': line,
            'priority': priority,
            'priority_num': priority_num,
            'due_date': due_date,
            'desc': desc
        })

    # Top 3 by priority (A > B > C > ...)
    top_priority = sorted(tasks, key=lambda x: x['priority_num'])[:3]

    # Top 3 by due date (earliest first)
    top_duedate = sorted(tasks, key=lambda x: x['due_date'])[:3]

    # Combine and deduplicate
    seen = set()
    top_6 = []
    for task in top_priority + top_duedate:
        task_id = task['line']
        if task_id not in seen:
            seen.add(task_id)
            top_6.append(task)

    return top_6[:6]

def format_output(top_6):
    """Format tasks as markdown list."""
    output = ["📋 Top 6 Todos to Focus On\n"]
    for i, task in enumerate(top_6, 1):
        priority_str = f"**({task['priority']})**" if task['priority'] else ""
        due_str = f" — due: {task['due_date']}" if task['due_date'] != "9999-12-31" else ""
        output.append(f"{i}. {priority_str} {task['desc']}{due_str}")
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 get_top_todos.py <path_to_todo_file>")
        sys.exit(1)

    todo_file = sys.argv[1]

    if not Path(todo_file).exists():
        print(f"Error: File not found: {todo_file}", file=sys.stderr)
        sys.exit(1)

    top_6 = get_top_todos(todo_file)
    print(format_output(top_6))
