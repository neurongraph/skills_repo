---
name: obsidian-todo-action
description: Action a single Obsidian todo: reads project context and related tasks, adaptively assesses what's needed (sub-tasks, email drafts, calendar invites), generates all artifacts into the project folder, and updates project.md — all in one session.
---

# Obsidian Todo Action Skill

Actions a single todo from the user's Obsidian vault in one focused session. Reads project context, decides adaptively what help is needed, generates artifacts (sub-tasks, email drafts, calendar invites, action notes), and updates the project folder.

**Dependency**: This skill is invoked from `obsidian-todotxt` Workflow G. It receives the selected todo line and resolves `todoPath`/`projectsPath` from the session file written by Workflow E.

---

## 1. Setup

**Resolve the skill directory** (once per session, before running any helper script):
Use the Glob tool with pattern `**/obsidian-todo-action/SKILL.md` to locate this skill. Take the dirname of the result as `OBSIDIAN_TODO_ACTION_DIR`. All scripts are at `$OBSIDIAN_TODO_ACTION_DIR/scripts/`.

**Resolve paths from the session file:**
```bash
if [ -f /tmp/obsidian_todo_session.env ]; then
  source /tmp/obsidian_todo_session.env
  # OBSIDIAN_TODO_PATH and OBSIDIAN_PROJECTS_PATH are now set
else
  # Fall back: read .obsidian/plugins/obsidian-todotxt/data.json
  # and resolve todoPath + projectsPath as described in obsidian-todotxt Workflow E
fi
```

Use `OBSIDIAN_TODO_PATH` as `todoPath` and `OBSIDIAN_PROJECTS_PATH` as `projectsPath` throughout this skill.

**Parse the received todo line** using the `obsidian-todotxt` parsing rules to extract:
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
> **People to loop in:** [names and roles from project.md or sibling todos, or "none identified" — include email addresses if present in project.md or sibling todos; otherwise ask the user for emails before generating any invite or email artifact]
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

1. **"Who needs to be involved in this task?"** — list names (and email addresses if known), or say "just me". Parse the response into a list of `{name, email}` pairs (email may be blank if not provided). Carry this list through all subsequent artifact generation steps.
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

2. After the user confirms or adjusts, run `create_outlook_email_draft.py` from `$OBSIDIAN_TODO_ACTION_DIR/scripts/`:

```bash
python3 "$OBSIDIAN_TODO_ACTION_DIR/scripts/create_outlook_email_draft.py" \
  --to "recipient@example.com" \
  --subject "confirmed subject" \
  --body "confirmed body text" \
  --output "/absolute/path/to/project/YYYY-MM-DD-<slug>-email.emltpl"
# Add --from "addr" and/or --cc "addr" only when needed
```

The `.emltpl` file opens in Outlook for Mac as a fully editable draft when double-clicked.

**Slug**: lowercase the todo description, replace spaces and non-alphanumeric characters with hyphens, truncate to 40 characters.

### 4c. Calendar Invite → .ics

If a calendar invite was confirmed:

1. Propose a time explicitly:
   > **Proposed meeting time:** [next business day] at 09:00–10:00
   > Does that work, or would you prefer a different date, time, or duration?

2. **Do not generate the file before receiving explicit user confirmation or an alternative.** Wait for the response.

3. After confirming, run `create_outlook_calendar_draft.py` from `$OBSIDIAN_TODO_ACTION_DIR/scripts/`:

```bash
python3 "$OBSIDIAN_TODO_ACTION_DIR/scripts/create_outlook_calendar_draft.py" \
  --summary "todo description" \
  --description "brief agenda derived from context" \
  --location "Microsoft Teams" \
  --start "YYYY-MM-DDTHH:MM" \
  --end "YYYY-MM-DDTHH:MM" \
  --attendee "Name:email@example.com" \
  --output "/absolute/path/to/project/YYYY-MM-DD-<slug>-invite.ics"
# Repeat --attendee for each person with a known email; omit entirely if no emails collected
# --location defaults to "Microsoft Teams" if not specified
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

Located at `$OBSIDIAN_TODO_ACTION_DIR/scripts/create_outlook_email_draft.py`. Creates a `.emltpl` file that Outlook for Mac opens as a fully editable draft.

CLI flags: `--to` (required), `--subject` (required), `--body` (required), `--output` (required, absolute path), `--from` (optional), `--cc` (optional).

### create_outlook_calendar_draft.py

Located at `$OBSIDIAN_TODO_ACTION_DIR/scripts/create_outlook_calendar_draft.py`. Creates an `.ics` file without `ORGANIZER`/`METHOD` so Outlook opens it as a locally editable event.

CLI flags: `--summary` (required), `--start` (required, `YYYY-MM-DDTHH:MM`), `--end` (required, `YYYY-MM-DDTHH:MM`), `--output` (required, absolute path), `--description` (optional), `--location` (optional, default: `Microsoft Teams`), `--attendee NAME:EMAIL` (optional, repeatable).
