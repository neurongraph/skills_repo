---
name: weekly-todos-planner
description: >
  Plan your work week by slotting top-priority Obsidian todos into free
  calendar slots. The user provides their weekly calendar as a screenshot,
  a markdown file, or a PDF — the skill extracts existing meetings from
  any of these, retrieves the top 10 urgent todos, and schedules them into
  free time. Trigger on "plan my week", "schedule my todos", "block time
  for my tasks", "fit my tasks into next week", or "help me plan next week".
  Always use this skill — not general scheduling advice — when a calendar
  (in any form: image, .md, or .pdf) is provided alongside a request to
  plan or prioritize work.
compatibility: >
  Requires the obsidian-todotxt skill to be installed (uses its get_top_todos.py).
  Bundled detect-vault.sh and create_outlook_calendar_draft.py are invoked directly.
---

# Weekly Todos Planner

Takes a screenshot of your weekly calendar, extracts existing meetings, retrieves your top 10 urgent Obsidian todos, slots them into free time, and produces .ics files you can import directly into Outlook.

---

## Configuration

Edit these values here to change working hours for all future runs:

```
WORKING_HOURS_START = 10:00
WORKING_HOURS_END   = 20:00
WORKING_DAYS        = Mon, Tue, Wed, Thu, Fri
```

> **Process isolation:** Each bash tool call runs in a separate shell process. Re-source `$OBSIDIAN_VAULT/.env` at the top of any bash script that needs env vars from that file.

---

## 0. Startup

### 0a. Read configuration

Read the `## Configuration` block above and hold these values for use in Section 3:
- `WORKING_HOURS_START` (default: `10:00`)
- `WORKING_HOURS_END` (default: `20:00`)
- `WORKING_DAYS` (default: Mon–Fri)

### 0b. Detect vault root

```bash
bash "$HOME/.maam/registries/surjit_skills/skills/weekly-todos-planner/scripts/detect-vault.sh"
```

- **COUNT=0** — stop. Tell the user: "Could not find an Obsidian vault in `$PWD` or any parent directory. Please run from inside your vault."
- **COUNT=1** — use the single printed path as `OBSIDIAN_VAULT`.
- **COUNT≥2** — present the numbered list and ask the user which vault to use.

Report: `✓ Vault root: <OBSIDIAN_VAULT>`

### 0c. Load environment variables

```bash
set -a
source "$OBSIDIAN_VAULT/.env" 2>/dev/null || true
set +a
```

### 0d. Resolve todoPath

Read `$OBSIDIAN_VAULT/.obsidian/plugins/obsidian-todotxt/data.json`. Extract `todoPath` and resolve to `$OBSIDIAN_VAULT/<todoPath>`. If the file is absent, ask the user for the path to `todo.md`.

### 0e. Output directory

Ask the user: "Where should I save the .ics files? (default: `~/Desktop/week-plan/`)"

Create the directory if it does not exist.

---

## 1. Parse the Calendar Input

The user provides their weekly calendar in one of three forms. Detect which applies and follow the corresponding path. All paths produce the same output: a markdown meetings table.

### Input type detection

| What the user provides | Input type |
|---|---|
| An image file or inline screenshot | **Screenshot** |
| A `.md` or `.txt` file path | **Markdown file** |
| A `.pdf` file path | **PDF** |

If the input type is ambiguous, ask: "Is this a screenshot, a markdown file, or a PDF?"

---

### Path A — Screenshot (image)

The calendar is a grid with days as columns, times as rows, and meetings overlaid as boxes.

Using vision, extract:
- **Week dates** — read the column headers to determine which week is shown (e.g. Mon Jun 16 – Fri Jun 20, 2026).
- **Meeting blocks** — for each visible box:
  - **Date**: which day column it sits in
  - **Start time**: aligned to the top row boundary of the box
  - **End time**: aligned to the bottom row boundary of the box
  - **Topic**: text visible inside the box
  - **Status**:
    - Solid / fully opaque box with strong border → `accepted`
    - Light / semi-transparent box with dotted or dashed border → `tentative`

---

### Path B — Markdown file

Read the file at the provided path. The file may use any reasonable structure (table, bullet list, headings per day, etc.). Extract from it:
- **Date** for each meeting (absolute date or inferred from a day heading)
- **Start time** and **End time**
- **Topic** / title of the meeting
- **Status**: look for explicit labels like "tentative", "(T)", "?" or similar markers; default to `accepted` if not indicated

If the file already uses the target table format (Date / Start / End / Topic / Status columns), use it directly after verifying all required columns are present.

---

### Path C — PDF

Convert the PDF to markdown first using `uvx`, then parse the result exactly as Path B:

```bash
uvx --with "markitdown[all]" markitdown /path/to/calendar.pdf -o /tmp/weekly-calendar-converted.md
```

If that fails, fall back to reading the PDF directly with the Read tool and extract meeting fields manually (Date, Start, End, Topic, Status) from whatever structure is present.

---

### Unified output

Regardless of input type, produce this markdown table and save it as `week-meetings.md` in the output directory from Section 0e:

```markdown
| Date       | Start | End   | Topic                     | Status    |
|------------|-------|-------|---------------------------|-----------|
| 2026-06-16 | 09:00 | 10:00 | Team standup              | accepted  |
| 2026-06-17 | 14:00 | 15:30 | Product review            | tentative |
```

Ask: "Here are the meetings I found. Does this look right? Any corrections before I plan?"

Wait for confirmation or corrections, then continue.

---

## 2. Retrieve Top 10 Todos

Run the obsidian-todotxt urgency scorer:

```bash
python3 "${OBSIDIAN_VAULT}/.claude/skills/obsidian-todotxt/scripts/get_top_todos.py" "$todoPath" 10
```

Show the resulting urgency table (columns: #, Priority, Due Date, Score, Description).

Ask: "These are your top 10 todos by urgency. Any you'd like to add, remove, or reprioritize before I schedule them?"

Wait for the user's response before continuing.

---

## 3. Find Free Slots

Using the `WORKING_HOURS_START`, `WORKING_HOURS_END`, and `WORKING_DAYS` from the Configuration block:

1. Build a complete 30-minute block grid for each working day of the calendar week (e.g. Mon 10:00, 10:30, 11:00 … 19:30).
2. Classify each block against the meeting table from Section 1:
   - `busy` — the block overlaps an **accepted** meeting
   - `tentative` — the block overlaps a **tentative** meeting (and is not busy)
   - `free` — no overlap with any meeting
3. Group consecutive `free` blocks into **free windows** (e.g. "Mon 11:00–13:00, 120 min").
4. Group consecutive `tentative` blocks into **tentative windows** (backup capacity).
5. Report totals: "You have **X h** of free time and **Y h** of tentative time across the week."

---

## 4. Slot Todos into the Calendar

Process todos in urgency score order (highest score first).

### Duration estimation

Estimate how long each todo will take based on keywords in the description:

| Signals in description | Estimated duration |
|---|---|
| "review", "read", "check", "scan", "look at" | 30 min |
| "write", "draft", "send", "prepare", "update", "call", "meet" | 60 min |
| "design", "build", "implement", "research", "plan", "create", "analyse", "analyze" | 90 min |

If the description doesn't clearly match any category, ask: "How long do you think '[todo description]' will take? (30 min / 1h / 1.5h / 2h)"

### Slot assignment

Work through todos one by one, filling from the earliest available slot forward:

1. **Prefer free over tentative.** Only use tentative slots once all free slots are consumed. When you start using tentative time, note it: "I'm now scheduling into tentative meeting slots."
2. **Single slot** — if the estimated duration fits in one contiguous free window, assign it directly.
3. **Multi-slot split** — if the duration exceeds the longest remaining contiguous window, split the todo across multiple slots. Name each part: `"[description] (1 of N)"`, `"(2 of N)"`, etc. The number N is fixed upfront based on total duration ÷ available window size (rounding up to 30-min chunks).
4. **Cannot schedule** — if a todo cannot be placed in any free or tentative slot, list it separately: "These todos couldn't fit this week and may carry to next week: [list]."

### Draft plan output

```markdown
## Proposed Week Plan: Jun 16–20, 2026

| Day | Time        | Todo                                  | Duration | Slot Type |
|-----|-------------|---------------------------------------|----------|-----------|
| Mon | 11:00–12:00 | Write Q2 summary report (1 of 2)     | 60 min   | free      |
| Mon | 13:00–14:00 | Write Q2 summary report (2 of 2)     | 60 min   | free      |
| Tue | 10:00–10:30 | Review stakeholder slides             | 30 min   | free      |
| Wed | 15:00–16:30 | Research vendor options               | 90 min   | tentative |
```

---

## 5. User Review & Adjustments

Present the draft plan and ask: "How does this look? You can tell me to move a todo to a different day/time, skip one, change a duration, or split differently."

Accept natural language edits:
- "Move the report writing to Thursday morning" → shift both slots to Thursday
- "Skip vendor research" → remove it from the plan
- "Make the report one 2-hour block on Friday afternoon" → merge into a single slot, re-slot others as needed

Re-apply edits and show the revised table. Repeat this loop until the user says the plan looks good (e.g. "Looks good", "That works", "Go ahead").

---

## 6. Generate .ics Files

For each confirmed todo slot, run the bundled calendar draft script:

```bash
python3 "${OBSIDIAN_VAULT}/.claude/skills/weekly-todos-planner/scripts/create_outlook_calendar_draft.py" \
  --summary "[todo description]" \
  --description "Focus block. Priority: [A/B/—]. Due: [YYYY-MM-DD or —]." \
  --location "" \
  --start "YYYY-MM-DDTHH:MM" \
  --end "YYYY-MM-DDTHH:MM" \
  --output "<output_dir>/YYYY-MM-DD-HHMM-<slug>.ics"
```

**Filename slug**: lowercase the todo description, replace spaces and non-alphanumeric characters with hyphens, truncate at 40 characters.

**Multi-slot suffix**: append `-1-of-N`, `-2-of-N`, etc. to both the `--summary` and the filename.

**Example filenames**:
```
2026-06-16-1100-write-q2-summary-report-1-of-2.ics
2026-06-16-1300-write-q2-summary-report-2-of-2.ics
2026-06-17-1000-review-stakeholder-slides.ics
```

After all files are created, print a session summary:

```
✓ 7 .ics files created in ~/Desktop/week-plan/

  2026-06-16-1100-write-q2-summary-report-1-of-2.ics
  2026-06-16-1300-write-q2-summary-report-2-of-2.ics
  2026-06-17-1000-review-stakeholder-slides.ics
  ...

Double-click each file to open as an editable appointment in Outlook.
```
