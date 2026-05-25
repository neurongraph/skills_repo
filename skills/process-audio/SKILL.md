---
name: process-audio
description: Takes an audio file and processes it using a Voice LLM to create a transcript. Use this skill when user mentions audio processing or voice memos or transcription
---

# Instructions
## Step 1 : Check the pre-requesites
We will use [qwen3_asr_rs](https://github.com/second-state/qwen3_asr_rs) to process the audio file and create a transcript.
This requires that qwen3_asr_rs and ffmpeg are installed.

Check if all the environment variables needed for this skill are set:
- `ASR_CLI`: The path to the ASR CLI executable.
- `MODEL_PATH`: The path to the model file used for transcription.
- `AUDIO_TEMP_DIR`: The directory where the audio input is present, the temporary .wav file and audio transcript.txtwill be saved.

If these environment variables are not set, check for them in the .env file in the project root. If they are not found, the skill will not be able to run. Ask the user to set them manually or update the .env file. Especially point out that this skill requires `ASR_CLI` to be set to the path where qwen3_asr_rs is installed. If the user has not installed qwen3_asr_rs, ask them to do so and set the `ASR_CLI` environment variable accordingly. Advise them to use the following command to install qwen3_asr_rs:

```bash
curl -sSf https://raw.githubusercontent.com/second-state/qwen3_asr_rs/main/install.sh | bash
```

Stop the execution of this skill here, and ask the user to retry after all insallation pre-requisites and the environment variables are set.

## Step 2 : Transcribe all the audio to text
Ensure that the AUDIO_TEMP_DIR/inputs directory exists and contains audio files to be transcribed.
Ensure that the AUDIO_OUTPUT_DIR directory exists and is writable. This should be AUDIO_TEMP_DIR/outputs. Create this dir if it does not exist.
Ensure that the AUDIO_TRANSCRIPTS_DIR directory exists and is writable. This should be AUDIO_TEMP_DIR/transcripts. Create this dir if it does not exist.

For every audio file in the AUDIO_TEMP_DIR/inputs, do the following:
- If the audio file is not in .wav format, convert it to .wav using ffmpeg
  - `ffmpeg -i <input_file>.m4a -ar 16000 -ac 1 AUDIO_OUTPUT_DIR/<output_file>.wav`
  - Note that in the above the input file can be other audio formats such as .mp3, .wav, .flac, etc.
- Transcribe the audio file using the ASR CLI.
  - `ASR_CLI/asr MODEL_PATH AUDIO_OUTPUT_DIR/<output_file>.wav > AUDIO_TRANSCRIPTS_DIR/<output_file>.txt 2>&1`
  - Note: The ASR CLI outputs to stdout (not a file parameter), so use `>` to redirect output to the transcript file.

## Step 3 : Append transcript to Daily Notes
Read `.obsidian/daily-notes.json` to understand:
1. Naming convention of daily notes (default `YYYY-MM-DD.md`)
2. Template for daily notes
3. Location of daily notes files

Read each of the transcript files and append it to the appropriate daily notes.
If the daily note does not exist, create it using the template and the transcript.
If the daily note already exists, append the transcript to the end of the note.

## Step 4 : Clean-up
Ask the user and on his confirmation remove the temporary audio files from AUDIO_INPUT_DIR, AUDIO_OUTPUT_DIR and the transcript files from AUDIO_TRANSCRIPTS_DIR.
