---
name: obsidian-daily-process
description: Orchestrates the full Obsidian vault processing pipeline: transcribes voice memos and audio recordings, classifies them into todos, ideas, or daily notes, and files each into the right place in the vault. Also triggers downstream Obsidian pipelines (wiki update, ArtMind knowledge graph). Use this skill whenever the user wants to process voice memos, audio recordings, or run any Obsidian vault update — even if they only mention "voice memo", "recording", "daily note", "capture ideas", or "update my vault" without explicitly mentioning transcription or Obsidian.
---

# Instructions

This skill orchestrates the full Obsidian vault processing pipeline: audio transcription, transcript classification and filing, and triggering of downstream vault update processes.

## Step 1: Invoke the process-audio Skill

Run the `process-audio` skill to transcribe all audio files in `$AUDIO_TEMP_DIR/inputs`.

It will check prerequisites, convert and transcribe all audio, and save transcripts to `$AUDIO_TEMP_DIR/transcripts/`. Wait for it to complete before continuing. If it stops due to missing prerequisites or no files found, stop here too.

## Step 2: Locate the Obsidian Vault

Determine where the Obsidian vault is. Check in this order:

1. The current working directory — if it contains an `.obsidian/` folder, treat it as the vault root
2. An `OBSIDIAN_VAULT` environment variable, if set
3. The `.env` file in the current working directory (`cat .env | grep OBSIDIAN_VAULT`)
4. Ask the user to provide the vault path

The vault root is the directory that contains the `.obsidian/` folder. Confirm this is correct before proceeding.

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

1. **Daily Note** — The transcript opens with a date reference (e.g. "Monday", "May 20th", "yesterday", "2025-05-19"). The date in the opening words determines which daily note it belongs to.
2. **Idea** — The transcript contains the word "idea" (case-insensitive) in the first 5 words.
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
- *(Placeholder — idea filing location not yet configured.)*
- Ask the user where ideas should be filed in their vault (e.g. a specific note, a folder, a daily note section). Once confirmed, append the transcript there with an `## Idea` heading.
- Note the location for next time so the user doesn't have to specify it again.

**Todo:**
- *(Placeholder — todo/task file location not yet configured.)*
- Ask the user where todos should be filed in their vault (e.g. a `Tasks.md` file, a specific folder, a daily note section). Once confirmed, append the transcript there with a `## Captured Task` heading.
- Note the location for next time so the user doesn't have to specify it again.

Tell the user the type assigned to each transcript and where it was filed (or where it will be filed once they confirm the location).

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
