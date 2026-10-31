---
name: music-library-downloader
description: Download named song lists or hit collections to MP3 via mdl / YouTube URLs.
when-to-use: "Use when the user wants to download a list of named songs (title + artist) or a curated hit collection (e.g. \"100 lagu hits 2020-2026\", \"50 Indonesian + 50 global\") to MP3 — resolve each track to a YouTube Music URL, then batch-download with mdl. User phrasings: \"bantu carai 100 lagu hits\", \"unduh daftar lagu\", \"download these songs\"."
argument-hint: "<songs.json|<title> <artist> …> [--out DIR]"
metadata:
  tags:
    - mdl
    - music-download
    - youtube-music
    - mp3
  category: creative
---

# Music Library Downloader (mdl)

Convert a list of named songs (title + artist) into a local music library of
MP3 files. Downloads are done by `mdl` (@mdlx/cli), which pulls audio from
YouTube; the only URL format that works headlessly is a YouTube Music track
URL, so the whole task is: resolve each song to a `music.youtube.com/watch?v=…` URL,
then drive mdl in a loop.

## What's in this skill

- `scripts/yt-resolve.py` — resolves a song list (JSON) to YouTube Music URLs by scraping
  YouTube search (ytInitialData); no API key needed.
- `scripts/mdl-download.py` — downloads all resolved URLs via mdl into an output dir;
  logs to a file and is safe to run in the background.
- `references/mdl.md` — mdl command flags and the URL patterns it accepts/rejects.
- `references/resolving-urls.md` — YouTube scraping details and why the Spotify
  approach dead-ends.

## Workflow

### 1. Collect the song list

Get every entry as `(title, artist)` pairs. If the user provides a Markdown list,
convert it to a JSON file:

```json
[ {"title": "Lathi", "artist": "Weird Genius"}, … ]
```

Drop `ft.`/feature lines from the query — they only add noise to the search.

### 2. Resolve to YouTube Music URLs

```bash
python3 scripts/yt-resolve.py songs.json -o ~/Music/<list-name>/yt-links.json
```

Scrapes `youtube.com/results` with the query `"<title> <artist> official audio"`,
takes the first `videoRenderer` hit, and writes `https://music.youtube.com/watch?v=<id>`
per song. Check `NOT FOUND` entries and re-query manually (or drop `official audio`
to broaden).

### 3. Batch download with mdl

Install if missing: `npm install -g @mdlx/cli` — the binary is `mdl` in the
dir next to the npm global `node` (`npm root -g` → `../bin`). It may not be
on the default PATH; locate with `ls $(npm root -g)/../bin`.

```bash
python3 scripts/mdl-download.py ~/Music/<list-name>/yt-links.json -o ~/Music/<list-name>/mp3
```

Run as a background process and log stdout: mdl prints a box-drawing UI on
each run, and 100 songs is ~30–60 min. Check the log periodically;
`mdl-download.py` prints `[i/N] <name>` and a final ok/failed tally.

mdl creates one subfolder per song (title uppercased). After the run,
optionally rename into a flat numbered layout, e.g. `001-Lathi - Weird Genius.mp3`.

For a FLAT output dir (no subfolders, mp3-only): mdl's `-o` always nests each
file in a subfolder it names itself, so download each track into a tempdir,
then move the .mp3 into the flat dir renamed `NNN - Title - Artist.mp3`
and delete the tempdir. No flag downloads directly flat.

## mdl command reference (condensed)

```bash
mdl '<URL>' -o <dir> -c 1 -f mp3 -b 256K
```

- `-c 1` — limit to one track (mandatory for single-track URLs).
- `-f` — mp3 | m4a | opus | flac | wav; `-b` — best | 0-10 | 128K…320K.
- Provider URLs accepted: Spotify/Apple/Amazon/Tidal etc. only for
  playlist/album/track pages; **audio is always sourced from YouTube**,
  so a Spotify URL requires that track to exist on YouTube.
- YouTube Music URLs: `music.youtube.com/watch?v=<id>` (track) or
  `music.youtube.com/playlist?list=<id>` / `music.youtube.com/browse/<playlistId>`.
  **Search URLs (`/search?q=…`) are rejected** — mdl does not perform search;
  you must resolve to concrete track/playlist IDs yourself (Step 2).

## Pitfalls

1. **mdl's binary may not be on PATH after `npm install -g`** — the install
   dir is the npm global prefix, which may not be on the user's PATH.
   Resolve the absolute path with `npm root -g` and call it explicitly
   (`mdl-download.py` does this; pass `--mdl <path>` if the default isn't
   found).
2. **Spotify API / embed endpoints are network-blocked on this host** —
   `open.spotify.com` responses come back as 403 from a Varnish cache, and
   catalog token endpoints fail. Don't spend time trying Spotify
   resolution; jump straight to YouTube scraping.
   (Also: a catalog endpoint with a hard-coded client id may silently return
   nothing; an `except: return []` around the fetch swallows that so every
   song looks 'NOT FOUND'. Verify the first query returns real JSON before
   running a batch.)
3. **mdl's per-run UI box makes logs noisy** — filter with
   `grep -E 'Downloaded|Failed|Error'` when checking a single run; the
   downloader script already does this.
4. **mdl-download.py's per-song failure check** looks at the 'Downloaded' and
   'Failed' counters on mdl's final line; if a song's video is region-locked
   or deleted, mdl prints 'This video is unavailable' and the folder may not
   exist — treat a missing folder as a failure and re-resolve the URL in Step 2.
5. **One mdl run = one collection**: for N songs you need N calls (the loop
   does it). Don't try to concatenate URLs into one call — mdl takes a single
   URL argument.
