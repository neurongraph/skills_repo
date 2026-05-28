# obsidian-todo-action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `obsidian-todo-action` skill and extend `obsidian-todotxt` so the user can pick a single todo from a top-k list and run a full actioning session — generating sub-tasks, email drafts, calendar invites, a timestamped action note, and updating `project.md`.

**Architecture:** Two-skill system. `obsidian-todotxt` owns the entry point: it displays the top-k ranked todos (Workflow F) and asks which one to action (new Workflow G), then hands off to `obsidian-todo-action`. The action skill reads the selected todo, its sibling todos in the same project, and `project.md` to decide between Context-First Analysis (Mode B, rich context) or Linear Interview (Mode A, sparse context), then generates all artifacts into the project folder.

**Tech Stack:** Markdown SKILL.md instruction files; Python reference scripts for Outlook draft generation (`.emltpl`, `.ics`) via macOS AppleScript / file-based methods.

---

## File Map

| Action | Path |
|--------|------|
| Modify | `skills/obsidian-todotxt/SKILL.md` |
| Create | `skills/obsidian-todo-action/SKILL.md` |
| Move   | `skills/obsidian-todotxt/references/create_outlook_email_draft.py` → `skills/obsidian-todo-action/references/` |
| Move   | `skills/obsidian-todotxt/references/create_outlook_calendar_draft.py` → `skills/obsidian-todo-action/references/` |

---

## Task 1: Update obsidian-todotxt SKILL.md

**Files:**
- Modify: `skills/obsidian-todotxt/SKILL.md`

- [ ] **Step 1: Update the frontmatter description**

In `skills/obsidian-todotxt/SKILL.md`, replace the `description:` value in the frontmatter:

Old:
```
description: Read, parse, write, sort, and complete tasks in Obsidian vaults using our custom Todo.txt format and its extended `complete:yyyy-mm-dd` tag and hierarchical grouping spec. Equip coding agents to cleanly add, modify, and check off tasks.
```

New:
```
description: Read, parse, write, sort, and complete tasks in Obsidian vaults using our custom Todo.txt format. Also surfaces top-k todos by urgency and serves as the entry point for actioning a todo via the obsidian-todo-action skill.
```

- [ ] **Step 2: Extend Workflow E to extract projectsPath**

In Workflow E, replace the current numbered steps:

Old:
```
1. Check if the file `./obsidian/plugins/obsidian-todotxt/data.json` exists relative to the vault root.
2. If it exists, parse it as JSON and extract the `todoPath` value (e.g., `"KB_2/00. Inbox/02. Tasks/todo.md"`).
3. Resolve this path relative to the vault root to get the absolute file path.
4. If the file does not exist, ask the user where the todo.txt file is located in their vault.
```

New:
```
1. Check if the file `.obsidian/plugins/obsidian-todotxt/data.json` exists relative to the vault root.
2. If it exists, parse it as JSON and extract:
   - `todoPath` (e.g., `"KB_2/00. Inbox/02. Tasks/todo.md"`) — resolve relative to the vault root.
   - `projectsPath` (e.g., `"KB_2/Projects"`) — resolve relative to the vault root. If this key is absent, ask the user where their projects folder is located in the vault.
3. If `data.json` does not exist, ask the user where the todo.txt file and projects folder are located in their vault.
```

Also replace the example data.json block:

Old:
```json
{
  "todoPath": "KB_2/00. Inbox/02. Tasks/todo.md",
  "additionalPaths": "",
  "archivePath": "KB_2/00. Inbox/02. Tasks/done.md"
}
```

New:
```json
{
  "todoPath": "KB_2/00. Inbox/02. Tasks/todo.md",
  "projectsPath": "KB_2/Projects",
  "additionalPaths": "",
  "archivePath": "KB_2/00. Inbox/02. Tasks/done.md"
}
```

- [ ] **Step 3: Append Workflow G to the end of the file**

Append the following after the Workflow F section:

```markdown
### G. Action a Todo (Entry Point for obsidian-todo-action)

Workflow G builds on Workflows E and F — it does not repeat their steps. Before running Workflow G, ensure:
- `todoPath` and `projectsPath` are known (Workflow E)
- The top-k ranked table has already been displayed to the user (Workflow F)

**Steps:**
1. Ask the user: *"Which todo do you want to work on?"* (referencing the numbered table displayed by Workflow F above)
2. User picks one by number
3. Note the full raw todo line, `todoPath`, and `projectsPath`, then invoke the `obsidian-todo-action` skill passing these three values as context for the session
```

- [ ] **Step 4: Verify the file reads correctly**

```bash
grep -n "projectsPath\|Workflow G" skills/obsidian-todotxt/SKILL.md
```

Expected output includes lines mentioning both `projectsPath` (in Workflow E) and `Workflow G`.

- [ ] **Step 5: Commit**

```bash
git add skills/obsidian-todotxt/SKILL.md
git commit -m "feat(obsidian-todotxt): extend Workflow E for projectsPath, add Workflow G entry point"
```

---

## Task 2: Create obsidian-todo-action SKILL.md

**Files:**
- Create: `skills/obsidian-todo-action/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p skills/obsidian-todo-action/references
```

- [ ] **Step 2: Create skills/obsidian-todo-action/SKILL.md**

Write the following content exactly:

```markdown
---
name: obsidian-todo-action
description: Action a single Obsidian todo: reads project context and related tasks, adaptively assesses what's needed (sub-tasks, email drafts, calendar invites), generates all artifacts into the project folder, and updates project.md — all in one session.
---

# Obsidian Todo Action Skill

Actions a single todo from the user's Obsidian vault in one focused session. Reads project context, decides adaptively what help is needed, generates artifacts (sub-tasks, email drafts, calendar invites, action notes), and updates the project folder.

**Dependency**: This skill is invoked from `obsidian-todotxt` Workflow G. It receives the selected todo line, `todoPath`, and `projectsPath` — it does not re-read `data.json`.

---

## 1. Setup

Parse the received todo line using the `obsidian-todotxt` parsing rules to extract:
- `description` — the task text (all tokens that are not metadata)
- `context` — the `@context` value (or `No Context` if absent)
- `project` — the `+project` value (or `No Project` if absent)
- `priority` — letter A–Z, or none
- `due_date` — `due:YYYY-MM-DD` value, or none

Resolve the project folder:
```
<projectsPath>/<context>/<project>/
```

If the folder does not exist, create it and write an empty `project.md` with this stub:
```markdown
# <project>

## Overview


## Collaborators


## Sessions
```

---

## 2. Context Gathering

Read three sources before doing any analysis:

1. **The selected todo line** — already parsed in Setup
2. **Sibling todos** — all uncompleted lines in `todo.txt` (skip `x ` prefix lines, skip `---`, `## @`, `### +` lines) that share the same `@context` AND `+project` as the selected todo
3. **`project.md`** — read the full file from the project folder

**Context richness check**: Count meaningful words in `project.md` — words not part of lines that are only markdown headings (`##`), horizontal rules (`---`), or blank lines. If the count is ≥100, context is **rich** → use Mode B. Otherwise, context is **sparse** → use Mode A.

---

## 3. Session Modes

### Mode B — Context-First Analysis (rich context)

Synthesize all three context sources and present a single pre-filled assessment:

> **Working on:** `<todo description>`
> **Project:** `@context / +project`
>
> Based on the todo, related tasks in this project, and project context, here's my assessment:
>
> **Suggested sub-tasks:**
> 1. [derived from context]
> 2. [derived from context]
>
> **People to loop in:** [names and roles from project.md or sibling todos, or "none identified"]
>
> **Suggested actions:**
> - [ ] Draft email to [name] re: [topic]  *(or: No email needed — this appears to be async/solo work)*
> - [ ] Set up a calendar invite with [name]  *(or: No invite needed)*
>
> **Blockers / dependencies:** [surfaced from context — if none found in context, ask: "Are there any blockers or dependencies I should know about?"]
>
> Does this look right? Anything to add or change before I proceed?

Wait for the user to confirm or adjust. Then proceed to Section 4 using the confirmed plan.

### Mode A — Linear Interview (sparse context)

Ask questions one at a time. Wait for a response before asking the next.

1. **"Who needs to be involved in this task?"** — list names or say "just me"
2. **"Should I break this into sub-tasks? Here are 2–3 suggestions: [suggest based on description]. Confirm, adjust, or say 'no sub-tasks'."**
3. *(Skip if solo/research — see heuristic below)* **"Should I draft an email to any of the people involved?"**
4. *(Skip if solo/research)* **"Does this need a calendar invite?"**
5. **"Are there any blockers or dependencies I should note?"**

**Solo/research heuristic (determines whether to skip questions 3 and 4):** Skip both if the selected todo description AND all sibling todo descriptions together contain none of the following:
- Capitalized person names (two or more consecutive words starting with a capital letter, excluding the first word of any line)
- Pronouns: "him", "her", "them", "with"
- Keywords (case-insensitive): "meeting", "align", "sync", "review", "discuss", "call", "email", "invite", "stakeholder", "team"

---

## 4. Artifact Generation

All artifacts are saved to `<projectsPath>/<context>/<project>/`. Generate only the artifacts confirmed by the user in Section 3.

### 4a. Sub-tasks → todo.txt

For each confirmed sub-task:

1. Build the task line in `obsidian-todotxt` inbox format:
   - Inherit `+project` and `@context` from the parent todo
   - Priority: one letter lower than parent (A→B, B→C, … Y→Z). If parent has no priority or priority Z, omit priority.
   - Example: `(B) Review stakeholder list +ProjectName @ContextName`
2. Insert at the top inbox of `todo.txt` per `obsidian-todotxt` Workflow A (within the 3 blank lines at the top of the file).

### 4b. Email Draft → .emltpl

If an email was confirmed:

1. Draft subject and body from context. Present to the user for review:
   > **Proposed email:**
   > **To:** [name / email]
   > **Subject:** [subject]
   > **Body:**
   > [body text]
   >
   > Look good, or would you like to adjust anything before I write the file?

2. After the user confirms or adjusts, run `create_emltpl_file()` from `references/create_outlook_email_draft.py`:

```python
from references.create_outlook_email_draft import create_emltpl_file

create_emltpl_file(
    from_addr="",          # leave blank — Outlook fills from default account
    to_addr="recipient@example.com",
    cc_addr="",            # omit if no CC
    subject="confirmed subject",
    body="confirmed body text",
    output_filename="/absolute/path/to/project/YYYY-MM-DD-<slug>-email.emltpl"
)
```

The `.emltpl` file opens in Outlook for Mac as a fully editable draft when double-clicked.

**Slug**: lowercase the todo description, replace spaces and non-alphanumeric characters with hyphens, truncate to 40 characters.

### 4c. Calendar Invite → .ics

If a calendar invite was confirmed:

1. Propose a time explicitly:
   > **Proposed meeting time:** [next business day] at 09:00–10:00
   > Does that work, or would you prefer a different date, time, or duration?

2. **Do not generate the file before receiving explicit user confirmation or an alternative.** Wait for the response.

3. After confirming, run `create_ics_draft()` from `references/create_outlook_calendar_draft.py`:

```python
import datetime
from references.create_outlook_calendar_draft import create_ics_draft

start_dt = datetime.datetime(YYYY, MM, DD, HH, MM)   # confirmed by user
end_dt = start_dt + datetime.timedelta(hours=1)       # or user-specified duration

create_ics_draft(
    summary="todo description",
    description="brief agenda derived from context",
    location="Microsoft Teams",    # ask user if they specify a different location
    start_dt=start_dt,
    end_dt=end_dt,
    output_filename="/absolute/path/to/project/YYYY-MM-DD-<slug>-invite.ics"
)
```

The `.ics` file opens as an editable calendar event in Outlook for Mac when double-clicked.

### 4d. Timestamped Action Note → .md

After all other artifacts are generated, write the action note.

Filename: `YYYY-MM-DD-HHMM-<slug>.md` (current date and time)

```markdown
# Action: <todo description>

**Date**: YYYY-MM-DD HH:MM
**Project**: @context / +project
**Priority**: <A or —>
**Due**: <YYYY-MM-DD or —>

---

## Assessment
<2–4 sentences on why this todo matters in the context of the project and related tasks>

## Sub-tasks Created
- [ ] Sub-task 1 (added to todo.txt)
- [ ] Sub-task 2 (added to todo.txt)

## People Involved
- Name — role (email drafted: YYYY-MM-DD-slug-email.emltpl)

## Blockers / Dependencies
- <listed, or "None">

## Decisions Made
- <listed, or "None">

## Next Steps
- <1–3 concrete next actions beyond the sub-tasks>
```

### 4e. Update project.md

After writing the action note, update `project.md`. Never overwrite the file — only upsert specific sections.

**Upsert `## Collaborators` section:**
- If it exists: add any newly identified people not already listed, format: `- Name — role`
- If it does not exist: insert it before `## Sessions` (or before the end of the file)

**Append to `## Sessions` section:**
- If it exists: append a new entry on its own line
- If it does not exist: append to the end of the file
- Format: `- [YYYY-MM-DD HH:MM — Action: <todo description>](<action-note-filename>.md)`

---

## 5. Session Summary

After all artifacts are written, print:

```
Session complete for: <todo description>

Created:
  ✓ <N> sub-tasks added to todo.txt
  ✓ Email draft: <filename>.emltpl        (or: — no email drafted)
  ✓ Calendar invite: <filename>.ics       (or: — no invite created)
  ✓ Action note: <filename>.md
  ✓ project.md updated

All files saved to: <projectsPath>/<context>/<project>/
```

---

## 6. Reference Scripts

### create_outlook_email_draft.py

Located at `references/create_outlook_email_draft.py`. Use `create_emltpl_file()` — creates a `.emltpl` file that Outlook for Mac opens as a fully editable draft.

Key parameters: `from_addr`, `to_addr`, `cc_addr`, `subject`, `body`, `output_filename` (absolute path).

### create_outlook_calendar_draft.py

Located at `references/create_outlook_calendar_draft.py`. Use `create_ics_draft()` — creates an `.ics` file without `ORGANIZER`/`METHOD` so Outlook opens it as a locally editable event.

Key parameters: `summary`, `description`, `location`, `start_dt` (Python `datetime.datetime`), `end_dt` (Python `datetime.datetime`), `output_filename` (absolute path).
```

- [ ] **Step 3: Verify the frontmatter**

```bash
head -6 skills/obsidian-todo-action/SKILL.md
```

Expected:
```
---
name: obsidian-todo-action
description: Action a single Obsidian todo: reads project context and related tasks, adaptively assesses what's needed (sub-tasks, email drafts, calendar invites), generates all artifacts into the project folder, and updates project.md — all in one session.
---

# Obsidian Todo Action Skill
```

- [ ] **Step 4: Commit**

```bash
git add skills/obsidian-todo-action/SKILL.md
git commit -m "feat(obsidian-todo-action): create skill SKILL.md with full session workflow"
```

---

## Task 3: Move reference scripts to obsidian-todo-action/references/

**Files:**
- Move: `skills/obsidian-todotxt/references/create_outlook_email_draft.py` → `skills/obsidian-todo-action/references/create_outlook_email_draft.py`
- Move: `skills/obsidian-todotxt/references/create_outlook_calendar_draft.py` → `skills/obsidian-todo-action/references/create_outlook_calendar_draft.py`

- [ ] **Step 1: Track the scripts at their current location (they are untracked)**

`git mv` only works on tracked files. Commit them at their current location first:

```bash
git add skills/obsidian-todotxt/references/create_outlook_email_draft.py \
        skills/obsidian-todotxt/references/create_outlook_calendar_draft.py
git commit -m "chore: track Outlook draft scripts before moving to obsidian-todo-action"
```

- [ ] **Step 2: Move both scripts with git mv**

```bash
git mv skills/obsidian-todotxt/references/create_outlook_email_draft.py \
       skills/obsidian-todo-action/references/create_outlook_email_draft.py

git mv skills/obsidian-todotxt/references/create_outlook_calendar_draft.py \
       skills/obsidian-todo-action/references/create_outlook_calendar_draft.py
```

- [ ] **Step 3: Verify the moves**

```bash
ls skills/obsidian-todotxt/references/
```
Expected (only one script remains):
```
get_top_todos.py
```

```bash
ls skills/obsidian-todo-action/references/
```
Expected:
```
create_outlook_calendar_draft.py
create_outlook_email_draft.py
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: move Outlook draft scripts to obsidian-todo-action/references/"
```

---

## Task 4: Final verification

- [ ] **Step 1: Confirm full file structure**

```bash
find skills/obsidian-todotxt skills/obsidian-todo-action -type f | sort
```

Expected:
```
skills/obsidian-todo-action/SKILL.md
skills/obsidian-todo-action/references/create_outlook_calendar_draft.py
skills/obsidian-todo-action/references/create_outlook_email_draft.py
skills/obsidian-todotxt/SKILL.md
skills/obsidian-todotxt/references/get_top_todos.py
```

- [ ] **Step 2: Confirm Workflow G is in obsidian-todotxt**

```bash
grep -n "Workflow G\|obsidian-todo-action" skills/obsidian-todotxt/SKILL.md
```

Expected: at least one line referencing Workflow G and one referencing `obsidian-todo-action`.

- [ ] **Step 3: Confirm obsidian-todo-action has all required sections**

```bash
grep -n "^## " skills/obsidian-todo-action/SKILL.md
```

Expected sections:
```
## 1. Setup
## 2. Context Gathering
## 3. Session Modes
## 4. Artifact Generation
## 5. Session Summary
## 6. Reference Scripts
```

- [ ] **Step 4: Confirm git log looks clean**

```bash
git log --oneline -5
```

Expected: 3 new commits (obsidian-todotxt update, obsidian-todo-action SKILL.md, script move) on top of the spec commit.
