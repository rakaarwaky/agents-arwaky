---
name: media-acquisition
description: Download music lists to a local MP3 library via mdl.
when-to-use: "Use when the user wants to download songs to a local MP3 music library, build/replenish a music library from a named list, or acquire media assets from external sources."
argument-hint: "<song-list | songs...> [--out-dir DIR] [--format mp3|m4a|opus|flac|wav] [--bitrate 128K..320K|best]"
metadata:
  tags:
    - media
    - music
    - mp3
    - download
    - library
  related_skills:
    - gif-search
---

# Media Asset Acquisition

Acquire media assets from external sources into a local library. Split by source and format.

## Global Rules

- **Resolve-first.** Tools that pull audio/video from a URL (e.g. `mdl`) never search — resolve every item to a concrete track/playlist URL before downloading.
- **One tool run = one collection.** N items need N tool calls; never concatenate URLs into one call.
- **Verify resolution before batching.** Check the first query returns real results; a silently empty endpoint makes every item look NOT FOUND.
- **Locate binaries explicitly.** Global npm installs may not put the binary on PATH; resolve with `npm root -g` / `ls $(npm root -g)/../bin`.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Music download | [`references/music-download.md`](references/music-download.md) | Song-list collection, YouTube Music URL resolution, mdl batch loop, flat-output layout, pitfalls. |
| mdl command reference | [`references/mdl-reference.md`](references/mdl-reference.md) | Condensed mdl CLI flags, provider URL formats, completion checks. |
