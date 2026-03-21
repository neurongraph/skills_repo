#!/usr/bin/env python3
"""
Obsidian Tasks Utility Functions

Helper functions for parsing, creating, and managing Obsidian task lines
using the native Obsidian Tasks emoji-based metadata format.

Projects are identified via hierarchical tags in the form #Project/Name
(e.g. #Project/Frontend, #Project/Alpha). This enables Task Genius plugin views.
Wikilinks are NOT used for project association.

Native format reference: https://publish.obsidian.md/tasks
Dependency: obsidian-cli skill for vault operations.
"""

from datetime import datetime, timedelta
import re
from typing import Optional, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Native Obsidian Tasks emoji constants
# ---------------------------------------------------------------------------

EMOJI_DUE = "\U0001f4c5"           # 📅
EMOJI_SCHEDULED = "\u23f3"         # ⏳
EMOJI_START = "\U0001f6eb"         # 🛫
EMOJI_DONE = "\u2705"              # ✅
EMOJI_CREATED = "\u2795"           # ➕
EMOJI_CANCELLED = "\u274c"         # ❌
EMOJI_RECURRENCE = "\U0001f501"    # 🔁
EMOJI_PRIORITY_HIGHEST = "\u23eb"  # ⏫
EMOJI_PRIORITY_HIGH = "\U0001f53c" # 🔼
EMOJI_PRIORITY_LOW = "\U0001f53d"  # 🔽
EMOJI_PRIORITY_LOWEST = "\u23ec"   # ⏬

# Map priority name → emoji  ("normal"/"medium" → no emoji)
PRIORITY_TO_EMOJI: Dict[str, str] = {
    "highest": EMOJI_PRIORITY_HIGHEST,
    "high":    EMOJI_PRIORITY_HIGH,
    "low":     EMOJI_PRIORITY_LOW,
    "lowest":  EMOJI_PRIORITY_LOWEST,
}

# Reverse map: emoji → priority name
EMOJI_TO_PRIORITY: Dict[str, str] = {v: k for k, v in PRIORITY_TO_EMOJI.items()}

# Date emojis mapped to their result-dict field names
_DATE_EMOJIS: Dict[str, str] = {
    EMOJI_DUE:       "due_date",
    EMOJI_START:     "start_date",
    EMOJI_SCHEDULED: "scheduled_date",
    EMOJI_DONE:      "done_date",
    EMOJI_CREATED:   "created_date",
    EMOJI_CANCELLED: "cancelled_date",
}

# All metadata emojis — used to detect where the description ends
_ALL_META_EMOJIS = [
    EMOJI_DUE, EMOJI_SCHEDULED, EMOJI_START, EMOJI_DONE,
    EMOJI_CREATED, EMOJI_CANCELLED, EMOJI_RECURRENCE,
    EMOJI_PRIORITY_HIGHEST, EMOJI_PRIORITY_HIGH,
    EMOJI_PRIORITY_LOW, EMOJI_PRIORITY_LOWEST,
]

# Alternation pattern for use in regex lookaheads
_META_PATTERN = "|".join(re.escape(e) for e in _ALL_META_EMOJIS)

# ---------------------------------------------------------------------------
# Date utilities
# ---------------------------------------------------------------------------


def parse_natural_date(date_str: str, base_date: Optional[datetime] = None) -> str:
    """
    Convert natural language date to ISO format (YYYY-MM-DD).

    Args:
        date_str:  Natural language date like "today", "tomorrow", "next Friday", etc.
        base_date: Reference date (defaults to today).

    Returns:
        ISO formatted date string (YYYY-MM-DD), or the input unchanged if unrecognised.
    """
    if base_date is None:
        base_date = datetime.now()

    date_str = date_str.lower().strip()

    # Already ISO format — pass through
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    if date_str == "today":
        return base_date.strftime("%Y-%m-%d")
    if date_str == "tomorrow":
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
    if date_str == "yesterday":
        return (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
    if date_str == "next week":
        return (base_date + timedelta(days=7)).strftime("%Y-%m-%d")

    # "in N days"
    match = re.match(r"in (\d+) days?", date_str)
    if match:
        days = int(match.group(1))
        return (base_date + timedelta(days=days)).strftime("%Y-%m-%d")

    # "next <weekday>"
    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    match = re.match(r"next (\w+)", date_str)
    if match:
        weekday = match.group(1).lower()
        if weekday in weekday_map:
            target_weekday = weekday_map[weekday]
            days_ahead = (target_weekday - base_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # "Month DD" — assumes current year
    match = re.match(r"(\w+) (\d{1,2})$", date_str)
    if match:
        month_str, day_str = match.groups()
        try:
            parsed = datetime.strptime(
                f"{month_str} {day_str} {base_date.year}", "%B %d %Y"
            )
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Unrecognised — return as-is
    return date_str


def _resolve_date(date_str: Optional[str]) -> Optional[str]:
    """Resolve natural language date to ISO format if needed."""
    if date_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return parse_natural_date(date_str)
    return date_str


# ---------------------------------------------------------------------------
# Task building
# ---------------------------------------------------------------------------


def build_task(
    description: str,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    projects: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    links: Optional[List[str]] = None,
    recurrence: Optional[str] = None,
    start_date: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    completed: bool = False,
    done_date: Optional[str] = None,
    created_date: Optional[str] = None,
) -> str:
    """
    Build a complete Obsidian task string using the native emoji metadata format.

    Native format (recommended metadata order)::

        - [ ] Description [[wikilink]] #Project/Name #tag 🔼 🔁 every week 🛫 start ⏳ scheduled 📅 due ✅ done

    Projects are rendered as #Project/<Name> tags (e.g. passing "ICA" → "#Project/Frontend").
    If the project value already starts with "Project/" or "#Project/" it is normalised
    accordingly. This enables Task Genius plugin views.

    Args:
        description:    Task description text.
        due_date:       Due date (📅) — YYYY-MM-DD or natural language.
        priority:       "highest", "high", "low", or "lowest". Omit for normal (no emoji).
        projects:       Project names rendered as #Project/<Name> tags.
                        Accepts bare names ("ICA"), "Project/Frontend", or "#Project/Frontend".
        tags:           Additional tags with or without leading #.
        links:          Raw wikilink strings for subtask links, e.g. "[[Note#Section]]".
        recurrence:     Recurrence pattern, e.g. "every day", "every Monday".
        start_date:     Start date (🛫) — YYYY-MM-DD or natural language.
        scheduled_date: Scheduled date (⏳) — YYYY-MM-DD or natural language.
        completed:      Whether the task is done — sets [x] and auto-fills done_date.
        done_date:      Done date (✅) — YYYY-MM-DD; defaults to today if completed=True.
        created_date:   Created date (➕) — YYYY-MM-DD.

    Returns:
        Formatted Obsidian task line.
    """
    checkbox = "[x]" if completed else "[ ]"

    # Resolve natural language dates to ISO
    due_date = _resolve_date(due_date)
    start_date = _resolve_date(start_date)
    scheduled_date = _resolve_date(scheduled_date)
    done_date = _resolve_date(done_date)
    created_date = _resolve_date(created_date)

    if completed and not done_date:
        done_date = datetime.now().strftime("%Y-%m-%d")

    # Description part: free text + subtask wikilinks + #Project/Name tags + other #tags
    desc_parts = [description]
    if links:
        desc_parts.extend(links)
    if projects:
        for p in projects:
            # Normalise to #Project/Name
            p = p.lstrip("#")
            if not p.startswith("Project/"):
                p = f"Project/{p}"
            desc_parts.append(f"#{p}")
    if tags:
        for tag in tags:
            desc_parts.append(tag if tag.startswith("#") else f"#{tag}")
    desc_str = " ".join(desc_parts)

    # Metadata in recommended Obsidian Tasks order:
    # priority → recurrence → start → scheduled → due → done → created
    metadata: List[str] = []

    if priority and priority.lower() in PRIORITY_TO_EMOJI:
        metadata.append(PRIORITY_TO_EMOJI[priority.lower()])
    if recurrence:
        metadata.append(f"{EMOJI_RECURRENCE} {recurrence}")
    if start_date:
        metadata.append(f"{EMOJI_START} {start_date}")
    if scheduled_date:
        metadata.append(f"{EMOJI_SCHEDULED} {scheduled_date}")
    if due_date:
        metadata.append(f"{EMOJI_DUE} {due_date}")
    if done_date:
        metadata.append(f"{EMOJI_DONE} {done_date}")
    if created_date:
        metadata.append(f"{EMOJI_CREATED} {created_date}")

    task = f"- {checkbox} {desc_str}"
    if metadata:
        task += " " + " ".join(metadata)

    return task


# ---------------------------------------------------------------------------
# Task parsing
# ---------------------------------------------------------------------------


def parse_task(task_line: str) -> Dict:
    """
    Parse an Obsidian task line (native emoji format) into its components.

    The description is captured as everything between the checkbox and the
    first metadata emoji, so [[wikilinks]] and #tags within the description
    are preserved correctly.

    Args:
        task_line: Complete task line from an Obsidian note.

    Returns:
        Dictionary with parsed task components.
    """
    result: Dict = {
        "raw":            task_line,
        "completed":      False,
        "description":    "",
        "due_date":       None,
        "priority":       None,
        "projects":       [],
        "tags":           [],
        "links":          [],
        "recurrence":     None,
        "start_date":     None,
        "scheduled_date": None,
        "done_date":      None,
        "created_date":   None,
        "cancelled_date": None,
    }

    # Completion status ([x] or [X])
    result["completed"] = bool(re.search(r"- \[[xX]\]", task_line))

    # Description: text between checkbox and the first metadata emoji.
    # Lookahead on specific emoji characters means [[wikilinks]] with ']'
    # characters are never truncated.
    desc_match = re.search(
        rf"- \[.\] (.+?)(?=\s*(?:{_META_PATTERN})|$)",
        task_line,
    )
    if desc_match:
        raw_desc = desc_match.group(1).strip()
        result["description"] = raw_desc

        # Extract [[wikilinks]] from description (subtask links only, not projects)
        result["links"].extend(re.findall(r"\[\[([^\]]+)\]\]", raw_desc))

    # Extract #tags from ENTIRE task line — tags may appear before or after metadata emojis
    all_tags = re.findall(r"#(\w+(?:/\w+)*)", task_line)
    result["tags"].extend(all_tags)

    # Projects are #Project/<Name> tags — case-insensitive, normalised to "Project/<Name>"
    for tag in all_tags:
        if tag.lower().startswith("project/"):
            normalised = "Project/" + tag[tag.index("/") + 1:]
            if normalised not in result["projects"]:
                result["projects"].append(normalised)

    # Extract each date emoji → ISO date value
    for emoji, key in _DATE_EMOJIS.items():
        m = re.search(rf"{re.escape(emoji)}\s*(\d{{4}}-\d{{2}}-\d{{2}})", task_line)
        if m:
            result[key] = m.group(1)

    # Extract priority emoji (first match wins)
    for emoji, name in EMOJI_TO_PRIORITY.items():
        if emoji in task_line:
            result["priority"] = name
            break

    # Extract recurrence: text after 🔁 up to next metadata emoji or EOL
    recur_match = re.search(
        rf"{re.escape(EMOJI_RECURRENCE)}\s*(.+?)(?=\s*(?:{_META_PATTERN})|$)",
        task_line,
    )
    if recur_match:
        result["recurrence"] = recur_match.group(1).strip()

    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_VALID_DATE_RE = re.compile(
    r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
)

_DATE_EMOJI_LABELS: Dict[str, str] = {
    EMOJI_DUE:       "due",
    EMOJI_START:     "start",
    EMOJI_SCHEDULED: "scheduled",
    EMOJI_DONE:      "done",
    EMOJI_CREATED:   "created",
    EMOJI_CANCELLED: "cancelled",
}


def validate_task_syntax(task_line: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an Obsidian task line using native emoji syntax rules.

    Args:
        task_line: Task line to validate.

    Returns:
        (is_valid, error_message) — error_message is None when valid.
    """
    # Must have a checkbox
    if not re.search(r"- \[.\]", task_line):
        return False, "Missing checkbox — expected '- [ ]' or '- [x]'"

    # Each date emoji must be followed by a valid YYYY-MM-DD date
    for emoji, label in _DATE_EMOJI_LABELS.items():
        for date_str in re.findall(rf"{re.escape(emoji)}\s*(\S+)", task_line):
            if not _VALID_DATE_RE.match(date_str):
                return False, (
                    f"Invalid {label} date '{date_str}' — use YYYY-MM-DD format"
                )

    # At most one priority emoji
    priority_count = sum(
        1 for e in [
            EMOJI_PRIORITY_HIGHEST, EMOJI_PRIORITY_HIGH,
            EMOJI_PRIORITY_LOW, EMOJI_PRIORITY_LOWEST,
        ]
        if e in task_line
    )
    if priority_count > 1:
        return False, "Multiple priority emojis detected — use at most one"

    return True, None


# ---------------------------------------------------------------------------
# Next-action scoring
# ---------------------------------------------------------------------------


def suggest_next_actions(task_lines: List[str]) -> List[Dict]:
    """
    Parse task lines and return incomplete tasks sorted by urgency score.

    Urgency scoring:
        Priority:   highest +15 · high +10 · normal +5 · low +2 · lowest +1
        Overdue:    +20
        Due today:  +15
        Due <= 3d:  +10
        Due <= 7d:  +5

    Args:
        task_lines: List of raw task line strings.

    Returns:
        Incomplete tasks sorted by urgency_score descending.
    """
    priority_scores = {"highest": 15, "high": 10, "low": 2, "lowest": 1}
    today = datetime.now().date()
    next_actions = []

    for task in (parse_task(line) for line in task_lines):
        if task["completed"]:
            continue

        score = priority_scores.get(task["priority"] or "", 5)  # 5 = normal

        if task["due_date"]:
            try:
                due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                days_until = (due - today).days
                if days_until < 0:
                    score += 20
                elif days_until == 0:
                    score += 15
                elif days_until <= 3:
                    score += 10
                elif days_until <= 7:
                    score += 5
            except ValueError:
                pass

        task["urgency_score"] = score
        next_actions.append(task)

    next_actions.sort(key=lambda x: x["urgency_score"], reverse=True)
    return next_actions


# ---------------------------------------------------------------------------
# Date label helper
# ---------------------------------------------------------------------------


def due_label(due_date_str: Optional[str], today=None) -> str:
    """
    Return a human-readable relative due date label.

    Examples:
        "overdue by 3 days"
        "due today"
        "due tomorrow"
        "due in 5 days"
        ""  (no due date)
    """
    if not due_date_str:
        return ""
    if today is None:
        today = datetime.now().date()
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        return ""
    delta = (due - today).days
    if delta < 0:
        return f"overdue by {-delta} day{'s' if -delta != 1 else ''}"
    if delta == 0:
        return "due today"
    if delta == 1:
        return "due tomorrow"
    return f"due in {delta} days"


# ---------------------------------------------------------------------------
# Demo / roundtrip check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    task = build_task(
        description="Review design document",
        due_date="tomorrow",
        priority="high",
        projects=["Alpha"],   # rendered as #Project/Alpha
        tags=["design", "review"],
    )
    print("Built task :", task)

    parsed = parse_task(task)
    print("Parsed task:", parsed)
    print("Projects   :", parsed["projects"])  # ["Project/Alpha"]

    valid, error = validate_task_syntax(task)
    print(f"Validation : valid={valid}, error={error}")

    # Roundtrip: rebuild from parsed components and compare.
    # Note: parsed["description"] already contains embedded #tags,
    # so do NOT pass projects/tags separately — they would be appended twice.
    rebuilt = build_task(
        description=parsed["description"],
        due_date=parsed["due_date"],
        priority=parsed["priority"],
    )
    print("Roundtrip  :", rebuilt)
    print("Match      :", task == rebuilt)
