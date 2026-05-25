---
name: obsidian-daily-process
description: Transcribes voice memos and audio recordings, then files the transcripts into the correct Obsidian daily note. Orchestrates the full pipeline: audio transcription via the process-audio skill, date inference, and daily note creation or update. Use this skill whenever the user wants audio or voice memo content to appear in their Obsidian journal, daily log, or daily notes — even if they only mention "voice memo", "recording", or "daily note" without explicitly mentioning transcription.
---

# Instructions

This skill orchestrates two things: transcribing audio files (delegated to the `process-audio` skill), then filing those transcripts into the right Obsidian daily note.

## Step 1: Invoke the process-audio Skill

Run the `process-audio` skill to transcribe all audio files in `$AUDIO_TEMP_DIR/inputs`.

It will check prerequisites, convert and transcribe all audio, and save transcripts to `$AUDIO_TEMP_DIR/transcripts/`. Wait for it to complete before continuing. If it stops due to missing prerequisites or no files found, stop here too.

## Step 2: Locate the Obsidian Vault

Determine where the Obsidian vault is. Check in this order:

1. An `OBSIDIAN_VAULT` environment variable, if set
2. The `.env` file in the current project root (`cat .env | grep OBSIDIAN_VAULT`)
3. Ask the user to provide the vault path

The vault root is the directory that contains the `.obsidian/` folder. Confirm this is correct before proceeding.

## Step 3: Read Daily Notes Configuration

Read `<vault>/.obsidian/daily-notes.json` to find:
1. The naming convention for daily notes (default: `YYYY-MM-DD.md`)
2. The folder where daily notes are stored, relative to the vault root (default: vault root)
3. The template file path, if specified

If `daily-notes.json` does not exist, use the defaults and continue.

If a template file is specified, read it now — you'll need it when creating a new daily note.

## Step 4: File Each Transcript into the Correct Daily Note

For each `.txt` file in `$AUDIO_TEMP_DIR/transcripts/`:

**Determine the target date** :
This should be present as initial part of the transcript.

**Find or create the daily note:**
- Build the note path from the vault folder, naming convention, and target date
- If the note already exists, append the transcript at the end
- If it doesn't exist, create it: apply the template (substituting the correct date wherever the template uses a date placeholder), then append the transcript

**Format the transcript block:**

```markdown

## Voice Memo

<transcript content>
```

Use a `## Voice Memo` heading so the content is clearly sectioned within the note. If multiple transcripts land in the same daily note, each gets its own `## Voice Memo` section with the heading repeated.

Tell the user which daily note each transcript was filed into.

## Step 5: Full Cleanup

List all temporary files that were created during processing, grouped by directory:
- Original audio files in `$AUDIO_TEMP_DIR/inputs/`
- Converted WAV files in `$AUDIO_TEMP_DIR/outputs/`
- Transcript text files in `$AUDIO_TEMP_DIR/transcripts/`

Ask the user whether to delete them. Delete only on explicit confirmation, and only after the daily notes have been successfully written.
