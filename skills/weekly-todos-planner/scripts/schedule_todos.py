#!/usr/bin/env python3
"""
schedule_todos.py — slot todos into free calendar windows.

Usage:
    python3 schedule_todos.py <free_slots.json> <todos.json> <min_slot_min> <max_splits>

free_slots.json: output of find_free_slots.py

todos.json format:
    [
      {
        "description": "Write Q2 report",
        "priority": "A",
        "due": "2026-06-20",
        "duration": 60,
        "score": 58
      },
      ...
    ]
    Todos must already be sorted highest-score first.

Outputs JSON to stdout:
    {
      "scheduled": [
        {
          "date": "2026-06-16",
          "start": "10:00",
          "end": "11:00",
          "description": "Write Q2 report",
          "priority": "A",
          "due": "2026-06-20",
          "part": 1,
          "of": 1,
          "slot_type": "free"
        },
        ...
      ],
      "unscheduled": [
        {
          "description": "...",
          "priority": "B",
          "due": "...",
          "duration": 90,
          "score": 24
        }
      ]
    }
"""

import sys
import json


def hm_to_min(hm: str) -> int:
    h, m = map(int, hm.split(":"))
    return h * 60 + m


def min_to_hm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def slot_todo(todo, free_windows_by_date, min_slot, max_splits, slot_type):
    """
    Try to slot a todo across available windows. Returns list of slot dicts on
    success, or None if it cannot be scheduled within the split limit.

    Windows are consumed in-place from free_windows_by_date[date].
    """
    remaining = todo["duration"]
    used = []  # list of (date, window_idx, start_min, end_min)

    for date_str in sorted(free_windows_by_date.keys()):
        windows = free_windows_by_date[date_str]
        for i, win in enumerate(windows):
            if remaining <= 0:
                break
            w_start = hm_to_min(win["start"])
            w_end = hm_to_min(win["end"])
            available = w_end - w_start
            if available < min_slot:
                continue  # window too small to be useful
            take = min(available, remaining)
            if take < min_slot:
                continue  # what we'd take is too small to be useful
            used.append((date_str, i, w_start, w_start + take))
            remaining -= take
        if remaining <= 0:
            break

    if remaining > 0:
        return None  # couldn't fit

    if len(used) > max_splits:
        return None  # too fragmented

    # Commit: consume the used portions from the windows
    # Work backwards through used to avoid index shifting issues
    for date_str, win_idx, slot_start, slot_end in used:
        windows = free_windows_by_date[date_str]
        win = windows[win_idx]
        w_start = hm_to_min(win["start"])
        w_end = hm_to_min(win["end"])

        # Replace this window with any remainder
        new_windows = windows[:win_idx]
        if slot_start > w_start:
            new_windows.append({"start": min_to_hm(w_start), "end": min_to_hm(slot_start),
                                 "minutes": slot_start - w_start})
        if slot_end < w_end:
            new_windows.append({"start": min_to_hm(slot_end), "end": min_to_hm(w_end),
                                 "minutes": w_end - slot_end})
        new_windows.extend(windows[win_idx + 1:])
        free_windows_by_date[date_str] = new_windows

    total_parts = len(used)
    slots = []
    for part_idx, (date_str, _, slot_start, slot_end) in enumerate(used):
        slots.append({
            "date": date_str,
            "start": min_to_hm(slot_start),
            "end": min_to_hm(slot_end),
            "description": todo["description"],
            "priority": todo.get("priority", "—"),
            "due": todo.get("due", "—"),
            "score": todo.get("score", 0),
            "part": part_idx + 1,
            "of": total_parts,
            "slot_type": slot_type,
        })
    return slots


def main():
    if len(sys.argv) < 5:
        print(
            "Usage: schedule_todos.py <free_slots.json> <todos.json> <min_slot_min> <max_splits>",
            file=sys.stderr,
        )
        sys.exit(1)

    free_slots_path = sys.argv[1]
    todos_path = sys.argv[2]
    min_slot = int(sys.argv[3])
    max_splits = int(sys.argv[4])

    with open(free_slots_path) as f:
        free_slots_data = json.load(f)

    with open(todos_path) as f:
        todos = json.load(f)

    # Build mutable copies of free and tentative windows
    free_by_date = {d: list(v["free"]) for d, v in free_slots_data.items()}
    tentative_by_date = {d: list(v["tentative"]) for d, v in free_slots_data.items()}

    scheduled = []
    unscheduled = []

    for todo in todos:
        # Try free slots first
        slots = slot_todo(todo, free_by_date, min_slot, max_splits, "free")
        if slots is None:
            # Fall back to tentative slots
            slots = slot_todo(todo, tentative_by_date, min_slot, max_splits, "tentative")
        if slots is not None:
            scheduled.extend(slots)
        else:
            unscheduled.append(todo)

    print(json.dumps({"scheduled": scheduled, "unscheduled": unscheduled}, indent=2))


if __name__ == "__main__":
    main()
