---
name: ytt
description: Fetch the transcript of a YouTube video and read it as context. Use whenever the user pastes a YouTube link (youtube.com/watch, youtu.be, shorts, live, embed) or asks to read, summarize, quote, or answer questions about a YouTube video.
---

# ytt

Run the bundled script with the URL or video ID. It prints Markdown: title, channel, URL, the caption track used,
then the transcript in paragraphs prefixed with `[m:ss]` timestamps.

```sh
~/.agents/skills/ytt/transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

- Pass several URLs at once to fetch them in one call. Outputs are separated by `---`.
- By default it uses the video's spoken language, preferring human-made captions over auto-generated ones. To
  force a language, pass codes in priority order: `--lang pt-BR,pt,en`.
- Read the output directly as context. Do not save it to a file unless the user asks.
- Auto-generated captions misspell names and jargon. Correct obvious errors when quoting, and cite timestamps when
  pointing to a moment in the video.

## Failures

- `TranscriptsDisabled` or `NoTranscriptFound`: the video has no captions. Tell the user; there is no transcript to
  read.
- `VideoUnavailable`: the video is private, removed, members-only, or age-restricted.
- `RequestBlocked` or `IpBlocked`: YouTube is blocking this machine's IP, common on cloud hosts. Tell the user to
  run it locally.
- `uv: command not found`: install uv (`brew install uv`).
