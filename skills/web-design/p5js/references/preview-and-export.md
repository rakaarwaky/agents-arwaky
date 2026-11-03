# Preview & Export — P5js

## Step 4: Preview & Iterate

Open the HTML directly in a browser (no server needed for basic sketches). For
local fonts/images use `scripts/serve.sh` or `python -m http.server`. Check
Chrome DevTools Performance tab for 60fps at the target export resolution, then
adjust parameters until the output matches the concept from Step 1.

## Step 5: Export

| Format | Method |
|--------|--------|
| **PNG** | `saveCanvas('output', 'png')` in `keyPressed()` — press 's' |
| **GIF** | `saveGif('output', 5)` — press 'g' |
| **Frame sequence** | `saveFrames('frame', 'png', 10, 30)` then `ffmpeg -i frame-%04d.png -c:v libx264 output.mp4` |
| **High-res PNG / MP4** | headless: `node scripts/export-frames.js sketch.html --width 3840 --height 2160 --frames 1` or `bash scripts/render.sh sketch.html output.mp4 --duration 30 --fps 30` (sketch must use `noLoop()` + `_p5Ready`) |
| **SVG** | `createCanvas(w, h, SVG)` with p5.js-svg, then `save('output.svg')` |

Full export pipeline detail (deterministic capture, CCapture.js, ffmpeg, per-clip
architecture, fxhash platform export, video gotchas):
[`export-pipeline.md`](export-pipeline.md).

## Step 6: Quality Verification (Verify)

Does the output match the concept? Is it sharp at the target display size? Does
it hold 60fps (30fps minimum for animations)? Do the colors work on both light
and dark monitors? What happens at canvas edges, on resize, after 10 minutes?
