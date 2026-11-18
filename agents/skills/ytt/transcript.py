#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["youtube-transcript-api>=1.2"]
# ///
"""Print the transcript of one or more YouTube videos as timestamped plain text."""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi

VIDEO_ID = re.compile(r"^[\w-]{11}$")
PATH_PREFIXES = ("shorts", "live", "embed", "v", "e")
PARAGRAPH_SECONDS = 30


def parse_id(value):
    value = value.strip()
    if VIDEO_ID.match(value):
        return value
    url = urllib.parse.urlparse(value if "://" in value else f"https://{value}")
    host = url.hostname or ""
    parts = [part for part in url.path.split("/") if part]
    candidate = ""
    if host.endswith("youtu.be") and parts:
        candidate = parts[0]
    elif "youtube" in host:
        query = urllib.parse.parse_qs(url.query)
        if "v" in query:
            candidate = query["v"][0]
        elif len(parts) > 1 and parts[0] in PATH_PREFIXES:
            candidate = parts[1]
    if not VIDEO_ID.match(candidate):
        raise ValueError(f"not a YouTube video URL: {value}")
    return candidate


def metadata(video_id):
    watch = f"https://www.youtube.com/watch?v={video_id}"
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(watch, safe="")
    try:
        with urllib.request.urlopen(url, timeout=5) as res:
            data = json.load(res)
        return data.get("title"), data.get("author_name")
    except Exception as err:
        print(f"warning: no title for {video_id}: {err}", file=sys.stderr)
        return None, None


def pick(transcripts, languages):
    if languages:
        return transcripts.find_transcript(languages)
    manual = [t for t in transcripts if not t.is_generated]
    generated = [t for t in transcripts if t.is_generated]
    if not generated:
        return manual[0]
    # YouTube only auto-generates captions in the spoken language, so it marks the original.
    spoken = generated[0].language_code.split("-")[0]
    for transcript in manual:
        if transcript.language_code.split("-")[0] == spoken:
            return transcript
    return generated[0]


def stamp(seconds):
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{secs:02}" if hours else f"{minutes}:{secs:02}"


def paragraphs(snippets):
    start, lines = 0.0, []
    for snippet in snippets:
        line = " ".join(snippet.text.split())
        if not line:
            continue
        elapsed = snippet.start - start
        sentence_done = lines and lines[-1][-1] in ".?!"
        if lines and elapsed >= PARAGRAPH_SECONDS and (sentence_done or elapsed >= 2 * PARAGRAPH_SECONDS):
            yield f"[{stamp(start)}] " + " ".join(lines)
            lines = []
        if not lines:
            start = snippet.start
        lines.append(line)
    if lines:
        yield f"[{stamp(start)}] " + " ".join(lines)


def render(api, video_id, languages):
    transcript = pick(api.list(video_id), languages)
    title, author = metadata(video_id)
    header = [f"# {title or video_id}"]
    if author:
        header.append(f"Channel: {author}")
    header.append(f"URL: https://www.youtube.com/watch?v={video_id}")
    header.append(f"Transcript: {transcript.language} [{transcript.language_code}]")
    return "\n".join(header) + "\n\n" + "\n\n".join(paragraphs(transcript.fetch()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", nargs="+", help="YouTube URLs or 11-character video IDs")
    parser.add_argument(
        "-l", "--lang", help="comma-separated language codes in priority order, e.g. pt-BR,pt,en"
    )
    args = parser.parse_args()
    languages = [code.strip() for code in args.lang.split(",")] if args.lang else None

    api = YouTubeTranscriptApi()
    outputs, failed = [], False
    for value in args.videos:
        try:
            outputs.append(render(api, parse_id(value), languages))
        except CouldNotRetrieveTranscript as err:
            print(f"error: {value}: {type(err).__name__}", file=sys.stderr)
            failed = True
        except Exception as err:
            print(f"error: {value}: {err}", file=sys.stderr)
            failed = True
    print("\n\n---\n\n".join(outputs))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
