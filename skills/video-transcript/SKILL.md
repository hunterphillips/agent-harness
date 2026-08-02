---
name: video-transcript
description: ALWAYS invoke when the user shares a YouTube or other video URL to summarize, analyze, quote, or extract its transcript — do not attempt WebFetch on video pages.
---

# video-transcript — Video Metadata and Captions

## Overview

Fetch video metadata and clean caption text with `yt-dlp`, without downloading the video. Manual subtitles are preferred over automatic captions.

## Usage

```bash
.claude/skills/video-transcript/fetch-transcript.py <url-or-video-id> [options]
```

| Option | Meaning |
|---|---|
| `--lang LANGS` | Pass a yt-dlp subtitle language expression verbatim. Default: `en.*,en`. |
| `--timestamps` | Prefix each transcript paragraph with its starting timestamp. |
| `--meta-only` | Print metadata and chapters without fetching captions. |
| `--cookies-from-browser BROWSER` | Let yt-dlp read cookies from a browser, such as `chrome` or `firefox`. |

## Examples

```bash
# Fetch metadata and an English transcript
.claude/skills/video-transcript/fetch-transcript.py "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# Include paragraph timestamps
.claude/skills/video-transcript/fetch-transcript.py "https://youtu.be/jNQXAC9IVRw" --timestamps

# Request Spanish caption variants
.claude/skills/video-transcript/fetch-transcript.py jNQXAC9IVRw --lang "es.*,es"

# Use signed-in browser cookies for an age-restricted video
.claude/skills/video-transcript/fetch-transcript.py "<url>" --cookies-from-browser chrome
```

## Output

The script prints title, channel, upload date, duration, canonical URL, and chapters when present, followed by readable transcript paragraphs. It collapses whitespace and removes bracketed caption noise such as `[Music]` and `[Applause]`.

## Analyzing

For long videos, pipe output to a scratch file and read relevant sections selectively instead of placing the entire transcript in context. Quote the script's timestamps when citing the video.

## First-Run Behavior

If `yt-dlp` is missing, the script installs it with `pip3 install --user yt-dlp`, retries with `--break-system-packages` only when required, and can run it as `python3 -m yt_dlp`. Prefer `brew install yt-dlp` for easier maintenance.

## Limitations

- Videos with no captions cannot be transcribed by this script. Manual fallback: run `yt-dlp -x --audio-format mp3 <url>`, then transcribe the MP3 with faster-whisper or whisper.cpp. This fallback is documented only and is not implemented here.
- Region-locked videos require a VPN in an allowed region.
- PO-token and anti-bot changes can cause odd failures. Update `yt-dlp` first when that happens.
