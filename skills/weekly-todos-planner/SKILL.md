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

An end-to-end weekly planning skill that turns your calendar and Obsidian todos into a ready-to-import Outlook schedule.

**What it does, step by step:**
1. **Parses your calendar** — accepts a screenshot, a markdown file, or a PDF; extracts all meetings with their dates, times, and acceptance status (accepted vs. tentative)
2. **Retrieves your top 10 todos** — pulls the highest-urgency tasks from your Obsidian vault using the obsidian-todotxt urgency scorer
3. **Finds free slots** — merges overlapping meetings, applies your working hours, and identifies usable free windows (and tentative windows as backup)
4. **Schedules todos into slots** — fills slots in urgency order, respects a minimum slot size so no tiny gaps are used, and caps how many fragments a single todo can be split into
5. **Handles overflow** — if todos can't all fit, asks which meetings you'd decline or downgrade, then re-slots; any remaining overflow is documented
6. **Lets you adjust** — shows the draft plan and accepts natural language edits before finalising
7. **Generates .ics files** — one per slot, ready to double-click and import into Outlook as editable appointments

---

## Configuration

Edit these values here to change defaults for all future runs:

```
WORKING_HOURS_START = 10:00
WORKING_HOURS_END   = 20:00
WORKING_DAYS        = Mon, Tue, Wed, Thu, Fri
MIN_SLOT_MINUTES    = 15
MAX_SPLITS_PER_TODO = 4
```

- `MIN_SLOT_MINUTES` — ignore any free window shorter than this. Gaps under 30 min are dead time, not schedulable focus blocks.
- `MAX_SPLITS_PER_TODO` — if scheduling a todo would require more than this many non-contiguous fragments, treat it as unschedulable and move it to overflow rather than producing a fragmented mess.

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

### OOO / leave / vacation entries

Before building the output table, filter out any calendar entry whose topic matches patterns like:

- "OOO", "Out of Office", "Out of office"
- "Leave", "Annual leave", "Sick leave", "PTO"
- "Vacation", "Holiday", "Off"
- Any all-day or multi-day block with similar wording

These are informational markers, not real meetings. **Do not include them in the meetings table and do not treat them as busy time.** If the entire day is marked OOO, treat that day as fully free within working hours (the person is away but the slots are still available for planning purposes — they can adjust after import).

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

Save the verified meetings table from Section 1 as `meetings.json` in the output directory:

```json
[
  {"date": "2026-06-16", "start": "09:00", "end": "10:00", "status": "accepted"},
  {"date": "2026-06-17", "start": "14:00", "end": "15:30", "status": "tentative"}
]
```

Then run the bundled slot-finder — **do not write custom interval-merging code**:

```bash
python3 "${OBSIDIAN_VAULT}/.claude/skills/weekly-todos-planner/scripts/find_free_slots.py" \
  "<output_dir>/meetings.json" \
  "WORKING_HOURS_START" "WORKING_HOURS_END" \
  > "<output_dir>/free_slots.json"
```

The script merges overlapping meetings, respects working hours, and outputs per-day `free` and `tentative` windows with minute totals. Read the JSON and report: "You have **X h** of free time and **Y h** of tentative time across the week."

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

Save the todos (after duration estimation and user confirmation) as `todos.json` in the output directory — sorted highest urgency score first:

```json
[
  {"description": "Write Q2 report", "priority": "A", "due": "2026-06-20", "duration": 60, "score": 58},
  {"description": "Review vendor RFI", "priority": "B", "due": "2026-06-22", "duration": 30, "score": 29}
]
```

Then run the bundled scheduler — **do not write custom scheduling code**:

```bash
python3 "${OBSIDIAN_VAULT}/.claude/skills/weekly-todos-planner/scripts/schedule_todos.py" \
  "<output_dir>/free_slots.json" \
  "<output_dir>/todos.json" \
  "MIN_SLOT_MINUTES" "MAX_SPLITS_PER_TODO" \
  > "<output_dir>/scheduled.json"
```

The scheduler:
- Fills free slots first, tentative slots as fallback
- Skips any window smaller than `MIN_SLOT_MINUTES` (default 30) — gaps under this are dead time, not focus time
- Refuses to split a todo into more than `MAX_SPLITS_PER_TODO` (default 3) fragments — over-fragmented todos go to overflow instead
- Outputs `scheduled` (list of placed slots) and `unscheduled` (overflow todos)

If `unscheduled` is non-empty, enter the **overflow negotiation loop** below before showing the draft plan.

### Overflow negotiation loop

When todos overflow, show the user which todos couldn't be scheduled and which meetings could be freed up:

```
These todos couldn't be scheduled — there isn't enough free time this week:

  • [todo A] — needs 60 min
  • [todo B] — needs 90 min

Your calendar has the following meetings that could potentially be freed up:

  | Date       | Start | End   | Topic                  | Current Status |
  |------------|-------|-------|------------------------|----------------|
  | 2026-06-17 | 14:00 | 15:30 | Product review         | tentative      |
  | 2026-06-18 | 11:00 | 12:00 | Weekly sync            | accepted       |

Would you like to decline or mark any of these as tentative to make room?
(e.g. "decline Product review", "mark Weekly sync tentative", or "no changes")
```

On each user response:
- **"decline [meeting]"** — remove it from the meetings table; its blocks become `free`.
- **"mark [meeting] tentative"** — update its status to `tentative`; its blocks shift from `busy` to `tentative`.
- **"no changes"** / "done" — exit the loop.

After each update, re-classify all blocks (Section 3 logic) with the updated meeting table and re-attempt slotting the remaining overflow todos. If new slots open up, fill them. If todos are still unscheduled, show the refreshed overflow list and repeat.

Exit when either all todos are scheduled, or the user indicates they don't want to free up any more meetings. Any todos that remain unscheduled at this point are carried forward as **unscheduled overflow** and documented in the final summary (Section 6).

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

Iterate over every entry in `scheduled.json` and call the bundled script — **never write custom ICS generation code**:

```bash
python3 "${OBSIDIAN_VAULT}/.claude/skills/weekly-todos-planner/scripts/create_outlook_calendar_draft.py" \
  --summary "[description]" \
  --description "Focus block. Priority: [priority]. Due: [due]." \
  --location "" \
  --start "YYYY-MM-DDTHH:MM" \
  --end "YYYY-MM-DDTHH:MM" \
  --output "<output_dir>/YYYY-MM-DD-HHMM-<slug>.ics"
```

**Filename rules**:
- Slug = lowercase description, non-alphanumeric → hyphens, collapse repeated hyphens, truncate at 40 chars
- Time portion = `HHMM` (four digits, **no colons** — colons are not valid in filenames on macOS/Windows)
- Multi-part suffix: `-1-of-N`, `-2-of-N` etc. appended to both slug and `--summary`

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

If any todos remained unscheduled after the overflow negotiation loop, append an **Unscheduled** section to the summary and save it as `week-plan-summary.md` in the output directory:

```markdown
## Unscheduled Todos

These tasks could not be fitted into the week and will need to carry over
or be addressed another way:

| Priority | Due        | Description              | Needed  |
|----------|------------|--------------------------|---------|
| A        | 2026-06-20 | Prepare board deck       | 90 min  |
| B        | —          | Research vendor options  | 90 min  |
```
