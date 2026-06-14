#!/usr/bin/env python3
"""
find_free_slots.py — merge overlapping meetings and find free windows within working hours.

Usage:
    python3 find_free_slots.py <meetings.json> <start_hhmm> <end_hhmm>

meetings.json format:
    [
      {"date": "2026-06-16", "start": "10:00", "end": "11:00", "status": "accepted"},
      ...
    ]

Outputs JSON to stdout:
    {
      "2026-06-16": {
        "free":      [{"start": "11:00", "end": "12:30", "minutes": 90}, ...],
        "tentative": [{"start": "14:00", "end": "15:00", "minutes": 60}, ...],
        "free_total": 90,
        "tentative_total": 60
      },
      ...
    }
"""

import sys
import json


def hm_to_min(hm: str) -> int:
    h, m = map(int, hm.split(":"))
    return h * 60 + m


def min_to_hm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def merge_intervals(intervals):
    """Merge a list of (start, end) int tuples into non-overlapping sorted intervals."""
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [intervals[0]]
    for s, e in intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def find_free_windows(busy_merged, tentative_merged, work_start, work_end):
    """Return free and tentative windows within [work_start, work_end)."""
    # All busy or tentative are "occupied" for the purposes of free calculation
    all_occupied = merge_intervals(busy_merged + tentative_merged)

    # Free = gaps in all_occupied within working hours
    free = []
    cursor = work_start
    for s, e in all_occupied:
        s = max(s, work_start)
        e = min(e, work_end)
        if cursor < s:
            free.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < work_end:
        free.append((cursor, work_end))

    # Tentative = gaps in busy_merged that overlap with tentative_merged
    busy_only = merge_intervals(busy_merged)
    busy_cursor = work_start
    potential_tentative = []
    for s, e in busy_only:
        s = max(s, work_start)
        e = min(e, work_end)
        if busy_cursor < s:
            potential_tentative.append((busy_cursor, s))
        busy_cursor = max(busy_cursor, e)
    if busy_cursor < work_end:
        potential_tentative.append((busy_cursor, work_end))

    # Intersect potential_tentative with tentative_merged
    tentative = []
    for ps, pe in potential_tentative:
        for ts, te in tentative_merged:
            lo = max(ps, ts)
            hi = min(pe, te)
            if lo < hi:
                tentative.append((lo, hi))
    tentative = merge_intervals(tentative)

    return free, tentative


def windows_to_dicts(windows):
    return [
        {"start": min_to_hm(s), "end": min_to_hm(e), "minutes": e - s}
        for s, e in windows
    ]


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: find_free_slots.py <meetings.json> <start_HH:MM> <end_HH:MM>",
            file=sys.stderr,
        )
        sys.exit(1)

    meetings_path = sys.argv[1]
    work_start = hm_to_min(sys.argv[2])
    work_end = hm_to_min(sys.argv[3])

    with open(meetings_path) as f:
        meetings = json.load(f)

    # Group by date
    by_date = {}
    for m in meetings:
        by_date.setdefault(m["date"], {"accepted": [], "tentative": []})
        s = hm_to_min(m["start"])
        e = hm_to_min(m["end"])
        # Clamp to working hours for busy calculation; slots outside are ignored
        if e <= work_start or s >= work_end:
            continue
        status = m.get("status", "accepted").lower()
        if status == "tentative":
            by_date[m["date"]]["tentative"].append((s, e))
        else:
            by_date[m["date"]]["accepted"].append((s, e))

    result = {}
    for date_str, buckets in sorted(by_date.items()):
        busy_merged = merge_intervals(buckets["accepted"])
        tentative_merged = merge_intervals(buckets["tentative"])
        free, tentative = find_free_windows(
            busy_merged, tentative_merged, work_start, work_end
        )
        result[date_str] = {
            "free": windows_to_dicts(free),
            "tentative": windows_to_dicts(tentative),
            "free_total": sum(e - s for s, e in free),
            "tentative_total": sum(e - s for s, e in tentative),
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
