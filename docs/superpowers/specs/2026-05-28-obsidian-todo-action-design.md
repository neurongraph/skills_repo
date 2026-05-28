# Design Spec: obsidian-todo-action Skill

**Date**: 2026-05-28  
**Status**: Approved  
**Depends on**: `obsidian-todotxt` skill

---

## Overview

A new skill (`obsidian-todo-action`) that helps the user action a single todo from their Obsidian vault — one session at a time. The entry point lives in `obsidian-todotxt` (Workflow G), which shows the top-k todos and asks the user to pick one. The action skill then takes over: reads project context, adaptively assesses what's needed, generates artifacts, and updates the project folder.

---

## Skill Structure

```
skills/obsidian-todotxt/
  SKILL.md                          ← add Workflow G (entry point)
  references/
    get_top_todos.py                ← unchanged, stays here

skills/obsidian-todo-action/
  SKILL.md                          ← new skill (execution layer)
  references/
    create_outlook_email_draft.py   ← moved here from obsidian-todotxt/references
    create_outlook_calendar_draft.py ← moved here from obsidian-todotxt/references
```

---

## Part 1: obsidian-todotxt — Changes Required

### Update Workflow E: Locating the Todo File Path

Workflow E currently extracts only `todoPath` from `data.json`. It must also extract `projectsPath`:

```json
{
  "todoPath": "KB_2/00. Inbox/02. Tasks/todo.md",
  "projectsPath": "KB_2/Projects",
  "additionalPaths": "",
  "archivePath": "KB_2/00. Inbox/02. Tasks/done.md"
}
```

If `projectsPath` is missing from `data.json`, ask the user where their projects folder is located in the vault.

### Add Workflow G: Action a Todo

Workflow G builds on Workflows E and F — it does not repeat their steps. It assumes:
- `todoPath` and `projectsPath` are already known (from Workflow E)
- The top-k ranked table has already been displayed (from Workflow F)

Steps:
1. Ask the user: *"Which todo do you want to work on?"* (referencing the table above)
2. User picks one by number
3. Hand off the selected todo line, `todoPath`, and `projectsPath` to the `obsidian-todo-action` skill

---

## Part 2: obsidian-todo-action — Execution Layer

### 2.1 Setup

Receives from `obsidian-todotxt` Workflow G: the selected todo line, `todoPath`, and `projectsPath` — does not re-read `data.json`.

- Parse the selected todo line: extract `@context`, `+project`, priority, due date, description
- Resolve project folder: `<projectsPath>/<context>/<project>/`
- If the folder doesn't exist: create it and stub an empty `project.md`

### 2.2 Context Gathering

Read three sources before doing any analysis:

1. **The selected todo line** — description, priority, due date, context, project
2. **All other uncompleted todos** in `todo.txt` sharing the same `@context` and `+project` — gives a picture of the broader workload and potential dependencies
3. **`project.md`** in the project folder (if it exists)

**Context richness threshold**: `project.md` exists AND contains ≥100 words of meaningful content (not just headings or blanks).

### 2.3 Session Modes

#### Mode B — Context-First Analysis (rich context)

Synthesize all three sources and present a pre-filled assessment in one message:

> *Based on the todo, related tasks in this project, and project context:*
> - *Suggested sub-tasks: [derived from context]*
> - *People to loop in: [from project.md or related todos]*
> - *Suggested action: draft alignment email to John*
> - *Blockers / dependencies: [surfaced from context, OR explicitly ask if not found]*
>
> *Does this look right? Anything to add or change?*

Blockers/dependencies are **always addressed** — surfaced from context if present, asked explicitly if not.

User confirms or adjusts, then the skill executes.

#### Mode A — Linear Interview (sparse context)

Ask questions one at a time in this order:

1. Who needs to be involved in this?
2. Can this be broken into sub-tasks? (suggest 2-3 based on description)
3. Should I draft an email to any of these people?
4. Does this need a calendar invite?
5. Are there any blockers or dependencies?

Questions 3 and 4 are skipped if the todo is clearly solo/research work — specifically, if the description and related todos contain none of: capitalized person names, pronouns ("him", "her", "them", "with"), or keywords ("meeting", "align", "sync", "review", "discuss", "call", "email", "invite", "stakeholder", "team").

---

### 2.4 Artifact Generation

All artifacts are saved to `<projectsPath>/<context>/<project>/`.

#### Sub-tasks → `todo.txt`

Each confirmed sub-task is inserted as a new uncompleted task at the top inbox of `todo.txt` (per obsidian-todotxt Workflow A), inheriting the parent's `+project` and `@context`. Priority is one level lower than the parent (e.g., parent A → sub-tasks B), or unprioritized if parent has no priority.

#### Email Draft → `.emltpl`

- Uses `create_outlook_email_draft.py` → `create_emltpl_file()` method
- The skill drafts subject + body from context and presents it to the user for review before writing
- Filename: `YYYY-MM-DD-<slug>-email.emltpl`
- Opens directly in Outlook for Mac as an editable draft

#### Calendar Invite → `.ics`

- Uses `create_outlook_calendar_draft.py` → `create_ics_draft()` method
- The skill proposes a suggested time (e.g., next business day 09:00–10:00) then explicitly asks:
  > *"I'm suggesting [date] at [time] for 1 hour — does that work, or would you prefer a different date, time, or duration?"*
- Only after user confirms or provides an alternative does it generate the `.ics` file
- Filename: `YYYY-MM-DD-<slug>-invite.ics`

#### Timestamped Action Note → `.md`

Filename: `YYYY-MM-DD-HHMM-<slug>.md`

```markdown
# Action: <todo description>

**Date**: YYYY-MM-DD HH:MM
**Project**: @context / +project
**Priority**: A
**Due**: YYYY-MM-DD

---

## Assessment
<brief synthesis of why this todo matters in project context>

## Sub-tasks Created
- [ ] sub-task 1  (added to todo.txt)
- [ ] sub-task 2  (added to todo.txt)

## People Involved
- Name — role (email drafted: YYYY-MM-DD-slug-email.emltpl)

## Blockers / Dependencies
- ...

## Decisions Made
- ...

## Next Steps
- ...
```

#### `project.md` Update

After the session, update `project.md`:
- **Upsert `## Collaborators` section**: add any newly identified people (name + role)
- **Append to `## Sessions` section**: dated link to the timestamped action note

```markdown
## Sessions
- [2026-05-28 09:45 — Action: <todo description>](2026-05-28-0945-<slug>.md)
```

If these sections don't exist yet, create them.

---

### 2.5 Session Summary

After all artifacts are written, report a concise summary:

```
Session complete for: <todo description>

Created:
  ✓ 3 sub-tasks added to todo.txt
  ✓ Email draft: 2026-05-28-slug-email.emltpl
  ✓ Calendar invite: 2026-05-28-slug-invite.ics
  ✓ Action note: 2026-05-28-0945-slug.md
  ✓ project.md updated
```

---

## Skill Trigger Descriptions

**obsidian-todotxt** (existing, updated):
> Read, parse, write, sort, and complete tasks in Obsidian vaults using our custom Todo.txt format. Also surfaces top-k todos by urgency and serves as the entry point for actioning a todo via the obsidian-todo-action skill.

**obsidian-todo-action** (new):
> Action a single Obsidian todo: reads project context and related tasks, adaptively assesses what's needed (sub-tasks, email drafts, calendar invites), generates all artifacts into the project folder, and updates project.md — all in one session.

---

## Key Constraints

- One session = one todo. No looping. User invokes again to action another.
- The skill never sends email or calendar invites — it only creates drafts/files for the user to review and send.
- `project.md` is updated but never overwritten — only sections are upserted or appended.
- Sub-tasks are inserted at the inbox top (3 blank lines) per the obsidian-todotxt spec, not filed into headings.
