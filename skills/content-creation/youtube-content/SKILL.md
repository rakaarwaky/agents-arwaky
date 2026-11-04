---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs."
when-to-use: "Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat YouTube content into chapters, threads, blog posts, or quotes."
argument-hint: "<youtube-url> [--text-only|--timestamps|--language LANG]"
---

# YouTube Content

You fetch YouTube transcripts via a bundled Python helper and reformat them
into chapters, summaries, threads, blog posts, or quotes.

## Global Rules

- **Prepare the helper's Python first.** The `youtube` extra declares the
  helper's dependency. From a PM-prepared Hermes source checkout:

  ```bash
  source ./activate
  python -c "import pm; pm.sync_venv(['youtube'], explicit=True)"
  source ./activate
  python -c "import youtube_transcript_api; print(youtube_transcript_api.__file__)"
  ```

  On Windows use `. .\activate.ps1` instead of `source ./activate`. Run
  every helper command with the interpreter whose import check succeeded.
  Never install into Hermes with raw pip or project-discovering `uv run`.
  See the
  [Hermes package-management docs](https://hermes-agent.nousresearch.com/docs/reference/package-management#developer-workflow).
- **URL forms accepted.** `scripts/fetch_transcript.py` accepts any
  standard YouTube URL format, short links (`youtu.be`), shorts, embeds,
  live links, or a raw 11-character video ID.
- **Output formats.** Six supported transformations — chapters, summary,
  chapter summaries, thread, blog post, quotes — owned by
  [`references/output-formats.md`](references/output-formats.md). Default to
  a summary when the user did not specify.
- **Chunking.** If the transcript exceeds ~50K characters, split into
  overlapping chunks (~40K with 2K overlap) and summarize each chunk
  before merging.
- **Workflow (5 steps).** (1) Fetch the transcript with
  `--text-only --timestamps`. (2) Validate: confirm non-empty and the
  expected language; if empty, retry without `--language`; if still empty,
  the video likely has transcripts disabled. (3) Chunk if needed.
  (4) Transform into the requested output format (default: summary).
  (5) Verify the transformed output — coherence, correct timestamps,
  completeness.
- **Error handling.** Transcript disabled → tell the user and suggest
  checking the video page for subtitles. Private/unavailable video → relay
  the error and ask the user to verify the URL. No matching language →
  retry without `--language` and note the actual language. Missing
  dependency → repeat the PM preparation and reactivation, then verify the
  helper uses that Python; do not repair the selected generation with pip.
- **Completion.** The transformed output re-reads coherent, with correct
  timestamps and completeness — no gaps, no fabricated sections.

## Routing

| Step         | Reference                                                                                       | Purpose                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| Helper usage | `python <SKILL_DIR>/scripts/fetch_transcript.py <url> [--text-only] [--timestamps] [--language tr,en]` | One-line helper with JSON metadata, plain text, timestamps, and language fallback chain.   |
| Output formats | [`references/output-formats.md`](references/output-formats.md)                                 | The six transformations with shape and worked example (chapters).                             |
