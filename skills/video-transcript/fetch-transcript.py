#!/usr/bin/env python3
"""Fetch video metadata and clean subtitles with yt-dlp."""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_LANGS = "en.*,en"
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
NOISE_RE = re.compile(r"\[[^\[\]]+\]")
SENTENCE_END_RE = re.compile(r"[.!?][\"'”’)]*$")


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def concise_process_error(result):
    text = result.stderr.strip() or result.stdout.strip()
    lines = [ANSI_RE.sub("", line).strip() for line in text.splitlines() if line.strip()]
    error_lines = [line for line in lines if "ERROR:" in line]
    message = error_lines[-1] if error_lines else (lines[-1] if lines else "unknown error")
    if "ERROR:" in message:
        message = message.split("ERROR:", 1)[1].strip()
    return re.sub(r"\s+", " ", message)


def run(command):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        fail(str(exc))


def yt_dlp_command():
    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]

    print(
        "note: yt-dlp is missing; installing it now (prefer `brew install yt-dlp` for easier maintenance).",
        file=sys.stderr,
    )
    pip = shutil.which("pip3")
    if not pip:
        fail("yt-dlp install failed: pip3 is not available")

    install = run([pip, "install", "--user", "yt-dlp"])
    install_text = f"{install.stdout}\n{install.stderr}".lower().replace("-", " ")
    if install.returncode != 0 and "externally managed" in install_text:
        install = run([pip, "install", "--user", "--break-system-packages", "yt-dlp"])
    if install.returncode != 0:
        fail(f"yt-dlp install failed: {concise_process_error(install)}")

    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]

    python3 = shutil.which("python3") or sys.executable
    module_command = [python3, "-m", "yt_dlp"]
    check = run(module_command + ["--version"])
    if check.returncode != 0:
        fail(f"yt-dlp install failed: {concise_process_error(check)}")
    return module_command


def normalize_url(value):
    if VIDEO_ID_RE.fullmatch(value):
        return f"https://www.youtube.com/watch?v={value}"
    return value


def common_options(args):
    options = ["--no-playlist", "--no-warnings"]
    if args.cookies_from_browser:
        options.extend(["--cookies-from-browser", args.cookies_from_browser])
    return options


def fetch_metadata(command, url, args):
    result = run(
        command
        + common_options(args)
        + ["--skip-download", "--dump-json", url]
    )
    if result.returncode != 0:
        fail(concise_process_error(result))

    for line in reversed(result.stdout.splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    fail("yt-dlp returned no readable metadata")


def format_time(seconds):
    try:
        total = max(0, int(float(seconds)))
    except (TypeError, ValueError):
        return "Unknown"
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_date(value):
    value = str(value or "")
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value or "Unknown"


def one_line(value):
    return re.sub(r"\s+", " ", str(value or "Unknown")).strip()


def print_metadata(metadata, fallback_url):
    print(f"Title: {one_line(metadata.get('title'))}")
    print(f"Channel: {one_line(metadata.get('channel') or metadata.get('uploader'))}")
    print(f"Upload date: {format_date(metadata.get('upload_date'))}")
    print(f"Duration: {format_time(metadata.get('duration'))}")
    print(f"URL: {one_line(metadata.get('webpage_url') or fallback_url)}")

    chapters = metadata.get("chapters") or []
    if chapters:
        print("Chapters:")
        for chapter in chapters:
            title = one_line(chapter.get("title"))
            print(f"  {format_time(chapter.get('start_time'))} — {title}")


def language_matches(languages, expression):
    tokens = [token.strip() for token in expression.split(",") if token.strip()]
    includes = [token for token in tokens if not token.startswith("-")]
    excludes = [token[1:] for token in tokens if token.startswith("-")]

    def matches(language, pattern):
        if pattern == "all":
            return True
        try:
            return re.fullmatch(pattern, language) is not None
        except re.error:
            return language == pattern

    selected = []
    for pattern in includes:
        for language in languages:
            if language == "live_chat" or language in selected:
                continue
            if matches(language, pattern) and not any(
                matches(language, excluded) for excluded in excludes
            ):
                selected.append(language)
    return selected


def available_languages(metadata):
    manual = list((metadata.get("subtitles") or {}).keys())
    automatic = list((metadata.get("automatic_captions") or {}).keys())
    return manual, automatic


def choose_caption(metadata, expression):
    manual, automatic = available_languages(metadata)
    manual_matches = language_matches(manual, expression)
    if manual_matches:
        return "manual", manual_matches[0]
    automatic_matches = language_matches(automatic, expression)
    if automatic_matches:
        return "automatic", automatic_matches[0]

    existing = sorted({lang for lang in manual + automatic if lang != "live_chat"})
    available = ", ".join(existing) if existing else "none"
    fail(
        f"no caption tracks match requested languages '{expression}'; "
        f"available caption languages: {available}"
    )


def fetch_caption_file(command, url, args, source, language, directory):
    output = str(Path(directory) / "caption.%(id)s.%(ext)s")
    write_option = "--write-subs" if source == "manual" else "--write-auto-subs"
    result = run(
        command
        + common_options(args)
        + [
            "--skip-download",
            write_option,
            "--sub-langs",
            args.lang,
            "--sub-format",
            "json3",
            "--output",
            output,
            url,
        ]
    )
    files = sorted(Path(directory).glob("*.json3"))
    exact = [path for path in files if path.name.endswith(f".{language}.json3")]
    if exact:
        return exact[0]
    if result.returncode != 0:
        fail(concise_process_error(result))
    if files:
        return files[0]
    fail(f"yt-dlp did not provide {language} captions in json3 format")


def clean_event_text(event):
    text = "".join(segment.get("utf8", "") for segment in event.get("segs") or [])
    text = html.unescape(text).replace("\u200b", "")
    text = NOISE_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_caption_events(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not read downloaded captions: {exc}")

    events = []
    for event in data.get("events") or []:
        text = clean_event_text(event)
        if not text:
            continue
        start = float(event.get("tStartMs", 0)) / 1000.0
        duration = float(event.get("dDurationMs", 0)) / 1000.0
        if events and events[-1][2] == text:
            events[-1] = (events[-1][0], max(events[-1][1], start + duration), text)
            continue
        events.append((start, start + duration, text))
    return events


def make_paragraphs(events):
    paragraphs = []
    parts = []
    paragraph_start = 0.0
    previous_end = None

    def flush():
        if parts:
            paragraphs.append((paragraph_start, " ".join(parts)))
            parts.clear()

    for start, end, text in events:
        if parts and previous_end is not None and start - previous_end > 3.0:
            flush()
        if not parts:
            paragraph_start = start
        parts.append(text)
        previous_end = max(previous_end or end, end)
        combined = " ".join(parts)
        if len(combined) >= 280 and SENTENCE_END_RE.search(combined):
            flush()
    flush()
    return paragraphs


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch video metadata and clean captions without downloading the video."
    )
    parser.add_argument("url_or_video_id")
    parser.add_argument("--lang", default=DEFAULT_LANGS, metavar="LANGS")
    parser.add_argument("--timestamps", action="store_true")
    parser.add_argument("--meta-only", action="store_true")
    parser.add_argument("--cookies-from-browser", metavar="BROWSER")
    return parser.parse_args()


def main():
    args = parse_args()
    url = normalize_url(args.url_or_video_id)
    command = yt_dlp_command()
    metadata = fetch_metadata(command, url, args)
    print_metadata(metadata, url)
    print()
    if args.meta_only:
        return

    source, language = choose_caption(metadata, args.lang)
    with tempfile.TemporaryDirectory(prefix="video-transcript-") as directory:
        caption_file = fetch_caption_file(
            command, url, args, source, language, directory
        )
        paragraphs = make_paragraphs(parse_caption_events(caption_file))

    if not paragraphs:
        fail(f"the {language} caption track contained no readable text")
    for start, paragraph in paragraphs:
        prefix = f"[{format_time(start)}] " if args.timestamps else ""
        print(f"{prefix}{paragraph}\n")


if __name__ == "__main__":
    main()
