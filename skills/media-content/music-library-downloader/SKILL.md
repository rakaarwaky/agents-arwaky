---
name: music-library-downloader
description: "Downloads named song lists to a local MP3 library via mdl, resolving each song to a YouTube Music URL."
when-to-use: "Use when the user wants to download songs (by title + artist) to a local MP3 music library, or build/replenish a music library from a named list."
argument-hint: "<song-list | songs...> [--out-dir DIR] [--format mp3|m4a|opus|flac|wav] [--bitrate 128K..320K|best]"
---

# Music Library Downloader

You convert a list of named songs (title + artist) into a local MP3 library: resolve each song to a YouTube Music URL, then drive `mdl` in a loop. `mdl` (@mdlx/cli) pulls audio from YouTube; the only URL format that works headlessly is a YouTube Music track URL. No bundled scripts — implement resolve + download inline or write your own helpers.

## Global Rules

- **Resolve-first.** `mdl` takes a concrete track/playlist URL and never searches — resolve every song to a `music.youtube.com/watch?v=…` URL before downloading (Step 2 of `references/workflow.md`).
- **One mdl run = one collection.** N songs need N mdl calls; never concatenate URLs into one call.
- **Verify resolution before batching.** Check the first query returns real results; a silently empty endpoint makes every song look NOT FOUND (pitfall list in `references/workflow.md`).
- **Locate the mdl binary explicitly.** `npm install -g @mdlx/cli` may not put `mdl` on PATH; resolve it with `npm root -g` (command reference in `references/mdl-reference.md`).

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Resolve + download loop | [`references/workflow.md`](references/workflow.md) | Song-list collection, YouTube Music URL resolution, mdl batch loop, flat-output layout, pitfalls. |
| mdl command reference | [`references/mdl-reference.md`](references/mdl-reference.md) | Condensed mdl flags, accepted URL forms, and which URL types it rejects. |
