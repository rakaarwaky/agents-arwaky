# mdl command reference (condensed)

```bash
mdl '<URL>' -o <dir> -c 1 -f mp3 -b 256K
```

- `-c 1` — limit to one track (mandatory for single-track URLs).
- `-f` — mp3 | m4a | opus | flac | wav; `-b` — best | 0-10 | 128K…320K.
- Provider URLs accepted: Spotify/Apple/Amazon/Tidal etc. only for playlist/album/track pages; **audio is always sourced from YouTube**, so a Spotify URL requires that track to exist on YouTube.
- YouTube Music URLs: `music.youtube.com/watch?v=<id>` (track) or `music.youtube.com/playlist?list=<id>` / `music.youtube.com/browse/<playlistId>`. **Search URLs (`/search?q=…`) are rejected** — mdl does not perform search; you must resolve to concrete track/playlist IDs yourself (see `references/music-download.md` step 2).

## Completion

- The mdl command uses exactly one URL per call (`-c 1` for single-track URLs).
- Search URLs (`/search?q=…`) are never passed to mdl.
