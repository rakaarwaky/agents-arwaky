# Music Library Downloader — Resolve + Download Workflow

## Step 1: Collect the song list

Get every entry as `(title, artist)` pairs. If the user provides a Markdown list, convert it to a JSON file:

```json
[ {"title": "Lathi", "artist": "Weird Genius"}, … ]
```

Drop `ft.`/feature lines from the query — they only add noise to the search.

## Step 2: Resolve to YouTube Music URLs

Scrape `youtube.com/results` with the query `"<title> <artist> official audio"`, take the first `videoRenderer` hit, and write `https://music.youtube.com/watch?v=<id>` per song. No API key needed — parse the `ytInitialData` blob in the HTML page. Check `NOT FOUND` entries and re-query manually (or drop `official audio` to broaden). Resolve each song into a JSON file:

```json
[ {"title": "Lathi", "artist": "Weird Genius", "url": "https://music.youtube.com/watch?v=<id>"}, … ]
```

## Step 3: Batch download with mdl

Install if missing: `npm install -g @mdlx/cli` — the binary is `mdl` in the dir next to the npm global `node` (`npm root -g` → `../bin`). It may not be on the default PATH; locate with `ls $(npm root -g)/../bin`.

Loop over the resolved URLs and run one mdl call per song into the output dir, logging stdout to a file and running in the background: mdl prints a box-drawing UI on each run, and 100 songs is ~30–60 min. Check the log periodically and print a `[i/N] <name>` progress line plus a final ok/failed per-song tally (count mdl's 'Downloaded'/'Failed' counters on its final line).

mdl creates one subfolder per song (title uppercased). After the run, optionally rename into a flat numbered layout, e.g. `001-Lathi - Weird Genius.mp3`.

For a FLAT output dir (no subfolders, mp3-only): mdl's `-o` always nests each file in a subfolder it names itself, so download each track into a tempdir, then move the .mp3 into the flat dir renamed `NNN - Title - Artist.mp3` and delete the tempdir. No flag downloads directly flat.

## Pitfalls

1. **mdl's binary may not be on PATH after `npm install -g`** — the install dir is the npm global prefix, which may not be on the user's PATH. Resolve the absolute path with `npm root -g` and call it explicitly (`--mdl <path>` if the default isn't found).
2. **Spotify API / embed endpoints are network-blocked on this host** — `open.spotify.com` responses come back as 403 from a Varnish cache, and catalog token endpoints fail. Don't spend time trying Spotify resolution; jump straight to YouTube scraping. (Also: a catalog endpoint with a hard-coded client id may silently return nothing; an `except: return []` around the fetch swallows that so every song looks 'NOT FOUND'. Verify the first query returns real JSON before running a batch.)
3. **mdl's per-run UI box makes logs noisy** — filter with `grep -E 'Downloaded|Failed|Error'` when checking a single run.
4. **Per-song failure check** looks at the 'Downloaded' and 'Failed' counters on mdl's final line; if a song's video is region-locked or deleted, mdl prints 'This video is unavailable' and the folder may not exist — treat a missing folder as a failure and re-resolve the URL in Step 2.
5. **One mdl run = one collection**: for N songs you need N calls (the loop does it). Don't try to concatenate URLs into one call — mdl takes a single URL argument.

## Completion

- Every song in the input list has a resolved `music.youtube.com` URL (or is marked NOT FOUND with a re-query attempt).
- The download loop finishes with an ok/failed tally; failed songs are re-resolved, not silently dropped.
