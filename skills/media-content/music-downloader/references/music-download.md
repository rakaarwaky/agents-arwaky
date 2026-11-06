# Music Download Workflow

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

For a FLAT output dir (no subfolders, mp3-only): mdl's `-o` always nests each file in a subfolder it names itself, so download each track into a tempdir, then move the .mp3 into the flat dir.

## Pitfalls

- A silently empty YouTube results endpoint (rate-limited or blocked) makes every song look NOT FOUND — verify resolution on the first song before batching the rest.
- `mdl` may not be on PATH after `npm install -g`; resolve the binary with `npm root -g` → `../bin`.
- mdl's `-o` always creates one subfolder per track; for a flat layout, download to a tempdir then `mv` the .mp3 into the target dir.
- 100 songs takes ~30–60 min; run in background and poll the log, never block on stdout.
