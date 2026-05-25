---
name: process-audio
description: Transcribes audio files (voice memos, recordings, meetings) into text using a local ASR model (qwen3_asr_rs). Processes all audio in the configured input directory and saves transcripts as text files. Use this skill whenever the user wants to transcribe audio, convert speech to text, process voice memos, or get spoken content into written form — even if they don't use the word "transcribe".
---

# Instructions

## Step 1: Check Prerequisites

This skill uses [qwen3_asr_rs](https://github.com/second-state/qwen3_asr_rs) for transcription and `ffmpeg` for audio format conversion.

Check whether these three environment variables are set in the current shell. If not, read the `.env` file in the project root (`cat .env`) and look for them there:

- `ASR_CLI` — path to the directory containing the `asr` executable (e.g. `~/.local/bin`)
- `MODEL_PATH` — full path to the Qwen3 ASR model file used for transcription
- `AUDIO_TEMP_DIR` — base directory for audio processing; inputs, converted WAVs, and transcripts all live under here

If any variable is missing, stop here and tell the user what's missing. Provide these pointers:
- **Installing qwen3_asr_rs**: `curl -sSf https://raw.githubusercontent.com/second-state/qwen3_asr_rs/main/install.sh | bash`
- **Getting a model**: follow the [qwen3_asr_rs documentation](https://github.com/second-state/qwen3_asr_rs) to download the Qwen3 ASR model file, then set `MODEL_PATH` to its full path
- **Setting env vars**: export them in the shell or add them to a `.env` file in the project root

Do not continue to Step 2 until all three variables are confirmed.

## Step 2: Transcribe Audio Files

Set up the working directories, creating them if they don't exist:

```bash
mkdir -p "$AUDIO_TEMP_DIR/outputs" "$AUDIO_TEMP_DIR/transcripts"
```

- Input: `$AUDIO_TEMP_DIR/inputs` — must already exist and contain audio files
- Converted WAVs: `$AUDIO_TEMP_DIR/outputs`
- Transcripts: `$AUDIO_TEMP_DIR/transcripts`

Look for files in `$AUDIO_TEMP_DIR/inputs` with these extensions: `.m4a`, `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.opus`. Skip any other file types.

If no matching audio files are found, tell the user and stop.

For each audio file found:

**1. Convert to WAV** (skip this step if the file is already `.wav`):
```bash
ffmpeg -i "$AUDIO_TEMP_DIR/inputs/<filename>" -ar 16000 -ac 1 "$AUDIO_TEMP_DIR/outputs/<basename>.wav"
```

**2. Transcribe** using the ASR CLI:
```bash
"$ASR_CLI/asr" "$MODEL_PATH" "$AUDIO_TEMP_DIR/outputs/<basename>.wav" \
  > "$AUDIO_TEMP_DIR/transcripts/<basename>.txt" \
  2>"$AUDIO_TEMP_DIR/transcripts/<basename>.err"
```

Stderr is redirected to a separate `.err` file so errors don't pollute the transcript. After each transcription, check whether the `.err` file is non-empty and warn the user if it contains anything.

When all files are processed, tell the user how many were transcribed and where the transcripts are saved: `$AUDIO_TEMP_DIR/transcripts/`.

## Step 3: Clean Up Intermediate Files

The converted WAV files in `$AUDIO_TEMP_DIR/outputs` are intermediate artifacts — the original audio and the transcripts are what matter. Ask the user whether to delete the WAV files now.

The original files in `$AUDIO_TEMP_DIR/inputs` and the transcripts in `$AUDIO_TEMP_DIR/transcripts` are left in place.
