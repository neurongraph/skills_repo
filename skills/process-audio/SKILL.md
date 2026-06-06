---
name: process-audio
description: Transcribes audio files (voice memos, recordings, meetings) into text using a local ASR model (qwen3_asr_rs). Processes all audio in the configured input directory and saves transcripts as text files. Use this skill whenever the user wants to transcribe audio, convert speech to text, process voice memos, or get spoken content into written form — even if they don't use the word "transcribe".
compatibility: Requires qwen3_asr_rs and ffmpeg. Paths (ASR_CLI, MODEL_PATH, AUDIO_TEMP_DIR) are provided by the invoking agent — do not load .env.
---

# Instructions

Paths are provided by the invoking agent: `$ASR_CLI`, `$MODEL_PATH`, `$AUDIO_TEMP_DIR`. Do not source `.env` — the orchestrator has already resolved these.

## Transcribe Audio Files

Set up the working directories, creating them if they don't exist:

```bash
mkdir -p "$AUDIO_TEMP_DIR/outputs" "$AUDIO_TEMP_DIR/transcripts"
```

- Input: `$AUDIO_TEMP_DIR/inputs` — must already exist and contain audio files
- Converted WAVs: `$AUDIO_TEMP_DIR/outputs`
- Transcripts: `$AUDIO_TEMP_DIR/transcripts`

Look for files in `$AUDIO_TEMP_DIR/inputs` with these extensions: `.m4a`, `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.opus`. Skip any other file types.

If no matching audio files are found, report to the orchestrator and stop.

For each audio file found:

**1. Convert to WAV** (skip this step if the file is already `.wav`):
```bash
ffmpeg -i "$AUDIO_TEMP_DIR/inputs/<filename>" -ar 16000 -ac 1 "$AUDIO_TEMP_DIR/outputs/<basename>.wav"
```

**2. Transcribe** using the ASR CLI:
```bash
"$ASR_CLI/asr" "$MODEL_PATH" "$AUDIO_TEMP_DIR/outputs/<basename>.wav" \
  > "$AUDIO_TEMP_DIR/transcripts/<basename>.raw" \
  2>"$AUDIO_TEMP_DIR/transcripts/<basename>.err"
```

Stderr (model loading INFO logs) is redirected to `.err`. After each transcription, check whether the `.err` file is non-empty and warn if it contains anything.

**3. Extract clean transcript** — the raw stdout has this fixed format:
```
Language: English
Text: <spoken words>
```
Strip the metadata and write just the spoken text:
```bash
sed -n 's/^Text: //p' "$AUDIO_TEMP_DIR/transcripts/<basename>.raw" \
  > "$AUDIO_TEMP_DIR/transcripts/<basename>.txt"
rm "$AUDIO_TEMP_DIR/transcripts/<basename>.raw"
```

When all files are processed, report how many were transcribed and where the transcripts are saved: `$AUDIO_TEMP_DIR/transcripts/`.
