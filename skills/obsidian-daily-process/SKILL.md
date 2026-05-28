---
name: obsidian-daily-process
description: Orchestrates the full Obsidian vault processing pipeline: transcribes voice memos and audio recordings, classifies them into todos, ideas, or daily notes, and files each into the right place in the vault. Also triggers downstream Obsidian pipelines (wiki update, ArtMind knowledge graph). Use this skill whenever the user wants to process voice memos, audio recordings, or run any Obsidian vault update — even if they only mention "voice memo", "recording", "daily note", "capture ideas", or "update my vault" without explicitly mentioning transcription or Obsidian.
---

# Instructions

This skill orchestrates the full Obsidian vault processing pipeline: audio transcription, transcript classification and filing, and triggering of downstream vault update processes.

## Environment Setup

This workflow requires environment variables from `.env`: `ASR_CLI`, `MODEL_PATH`, `AUDIO_TEMP_DIR`, `IDEAS_INBOX`, `TODO_PATH`, and `OBSIDIAN_VAULT`.

If variables are undefined, prefix bash commands with:
```bash
set -a; source .env; set +a &&
```

**Important:** The current working directory should be the Obsidian vault root (the directory containing `.obsidian/`).

## Step 1: Invoke the process-audio Skill

Run the `process-audio` skill to transcribe all audio files in `$AUDIO_TEMP_DIR/inputs`.

It will check prerequisites, convert and transcribe all audio, and save transcripts to `$AUDIO_TEMP_DIR/transcripts/`. Wait for it to complete before continuing. If it stops due to missing prerequisites or no files found, stop here too.

## Step 2: Verify Obsidian Vault Root

This workflow assumes the current working directory is the Obsidian vault root (the directory containing `.obsidian/`). Verify:

```bash
[ -d ".obsidian" ] && echo "✓ Vault root confirmed"
```

If `.obsidian/` is not in the current directory, the user should:
1. Check if `OBSIDIAN_VAULT` environment variable is set (it will be loaded in the Environment Setup step)
2. If set, change to that directory: `cd "$OBSIDIAN_VAULT"`
3. If not set, ask the user to provide the vault path or cd into it before running this workflow

All subsequent file paths are relative to the vault root (e.g., `KB_2/00. Inbox/02. Tasks/todo.md`).

## Step 3: Read Daily Notes Configuration

Read `<vault>/.obsidian/daily-notes.json` to find:
1. The naming convention for daily notes (default: `YYYY-MM-DD.md`)
2. The folder where daily notes are stored, relative to the vault root (default: vault root)
3. The template file path, if specified

If `daily-notes.json` does not exist, use the defaults and continue.

If a template file is specified, read it now — you'll need it when creating a new daily note.

## Step 4: Classify and File Each Transcript

For each `.txt` file in `$AUDIO_TEMP_DIR/transcripts/`, first classify it, then file it accordingly.

### Classification

Read the transcript and determine its type using these rules, applied in order:

1. **Daily Note** — The transcript opens with a date reference. Check the first ~20 characters for day names (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, yesterday, today, tomorrow) or date patterns (May, Jan, Feb, etc., or YYYY-MM-DD format). The date in the opening words determines which daily note it belongs to.
   
   ```bash
   if echo "$transcript" | grep -qi "^[^a-z]*\(monday\|tuesday\|wednesday\|thursday\|friday\|saturday\|sunday\|yesterday\|today\|tomorrow\|january\|february\|march\|april\|may\|june\|july\|august\|september\|october\|november\|december\)"; then
     # Daily Note
   ```

2. **Idea** — The transcript contains the word "idea" (case-insensitive) in the first 5 words. Simple check without complex patterns:
   
   ```bash
   if echo "$transcript" | head -c 100 | grep -qi "idea"; then
     # Idea
   ```

3. **Todo** — Everything else. Task-oriented language ("I need to", "remind me", "follow up", "don't forget", "action item") with no date reference at the start and no mention of "idea" signals a todo or task capture.

A transcript matches the first rule that fits — so a note that opens with a date is always a Daily Note even if it also mentions "idea" or tasks.

### Filing by Type

**Daily Note:**
- Derive the target date from the opening words. If relative ("yesterday", "Monday"), resolve it to an absolute date.
- Build the note path from the vault folder, naming convention, and target date.
- If the note already exists, append at the end. If it doesn't exist, create it from the template (substituting the correct date wherever the template uses a date placeholder), then append.
- Format the appended block as:

```markdown

## Voice Memo

<transcript content>
```

If multiple transcripts land on the same date, each gets its own `## Voice Memo` section.

**Idea:**
- Check the `.env` file for the `IDEAS_INBOX` variable. This points to a folder or directory where idea files should be stored (e.g., `KB_2/01. Ideas/`).
- If `IDEAS_INBOX` is set, create a new `.md` file in that directory with a filename based on the first few words of the idea (e.g., `New product feature.md`).
- Add the `#ideas` tag at the end of the file and include the full transcript content.
- If `IDEAS_INBOX` is not set, ask the user where ideas should be filed in their vault and confirm before filing.

**Todo:**
- Use `obsidian-todotxt` **Workflow E** to locate the todo file (session cache first, then `data.json`).
- Use `obsidian-todotxt` **Workflow A** to append the transcript as a new task at the top of the inbox.

Tell the user the type assigned to each transcript and where it was filed.

## Step 5: Wiki Update Pipeline

*(Placeholder — not yet implemented.)*

This step will trigger an Obsidian wiki update process — scanning newly filed content for entities, concepts, or references that should be reflected in the vault's wiki or reference notes. Leave this step as a no-op for now and note it to the user as "coming soon."

## Step 6: ArtMind Knowledge Graph Update

*(Placeholder — not yet implemented.)*

This step will trigger an artmind knowledge graph update — propagating newly captured ideas, tasks, and notes into the knowledge graph for cross-linking and insight generation. Leave this step as a no-op for now and note it to the user as "coming soon."

## Step 7: Full Cleanup

List all temporary files that were created during processing, grouped by directory:
- Original audio files in `$AUDIO_TEMP_DIR/inputs/`
- Converted WAV files in `$AUDIO_TEMP_DIR/outputs/`
- Transcript text files in `$AUDIO_TEMP_DIR/transcripts/`

Ask the user whether to delete them. Delete only on explicit confirmation, and only after all vault notes have been successfully written.

## Step 8: Todo Review and Action

Use `obsidian-todotxt` **Workflow F** to fetch and display the top 10 uncompleted todos ranked by composite urgency score. This surfaces the highest-priority work — including any tasks just added from this session's transcripts.

Then use `obsidian-todotxt` **Workflow G** to ask the user if they want to action one of the todos. If yes, invoke `obsidian-todo-action` for the selected task.
