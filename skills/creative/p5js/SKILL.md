---
name: p5js
description: "p5.js sketches: gen art, shaders, interactive, 3D."
when-to-use: "Use when the user wants a p5.js sketch — generative art, shaders, interactive visualizations, canvas animations, 3D WebGL scenes, audio-reactive visuals, or data viz, exported as HTML/PNG/GIF/MP4/SVG."
argument-hint: "<generative|data-viz|interactive|animation|3d|image-processing|audio-reactive> [output.html|png|gif|mp4|svg] [--width W --height H --frames N --fps F]"
version: 1.0.0
author: SHL0MS, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, generative-art, p5js, canvas, interactive, visualization, webgl, shaders, animation]
    related_skills: [ascii-video, manim-video, excalidraw]
---

# p5.js Production Pipeline

## When to use

Use when users request: p5.js sketches, creative coding, generative art, interactive visualizations, canvas animations, browser-based visual art, data viz, shader effects, or any p5.js project.

## What's inside

Production pipeline for interactive and generative visual art using p5.js. Creates browser-based sketches, generative art, data visualizations, interactive experiences, 3D scenes, audio-reactive visuals, and motion graphics — exported as HTML, PNG, GIF, MP4, or SVG. Covers: 2D/3D rendering, noise and particle systems, flow fields, shaders (GLSL), pixel manipulation, kinetic typography, WebGL scenes, audio analysis, mouse/keyboard interaction, and headless high-res export.

## Creative Standard

This is visual art rendered in the browser. The canvas is the medium; the
algorithm is the brush.

- **Before writing code**, articulate the creative concept: what does this piece
  communicate, and what separates it from a tutorial example? The user's prompt
  is a starting point — interpret it with creative ambition.
- **First-render excellence is non-negotiable.** If it looks like a p5.js
  tutorial exercise or "AI-generated creative coding," rethink before shipping.
- **Go beyond the reference vocabulary.** The catalogs are starting palettes;
  combine, layer, and invent. Include at least one visual detail the user
  didn't ask for but will appreciate.
- **Dense, layered, considered.** Never flat white backgrounds; always
  compositional hierarchy, intentional color, and micro-detail. All elements
  must serve a unified visual language — a sketch with ten unrelated effects is
  worse than three that belong together.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Generative art** | Seed / parameters | Procedural visual composition (still or animated) | `references/visual-effects.md` |
| **Data visualization** | Dataset / API | Interactive charts, graphs, custom data displays | `references/interaction.md` |
| **Interactive experience** | None (user drives) | Mouse/keyboard/touch-driven sketch | `references/interaction.md` |
| **Animation / motion graphics** | Timeline / storyboard | Timed sequences, kinetic typography, transitions | `references/animation.md` |
| **3D scene** | Concept description | WebGL geometry, lighting, camera, materials | `references/webgl-and-3d.md` |
| **Image processing** | Image file(s) | Pixel manipulation, filters, mosaic, pointillism | `references/visual-effects.md` § Pixel Manipulation |
| **Audio-reactive** | Audio file / mic | Sound-driven generative visuals | `references/interaction.md` § Audio Input |

## Stack

Single self-contained HTML file per project. No build step required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | p5.js 1.11.3 (CDN) | Canvas rendering, math, transforms, event handling |
| 3D | p5.js WebGL mode | 3D geometry, camera, lighting, GLSL shaders |
| Audio | p5.sound.js (CDN) | FFT analysis, amplitude, mic input, oscillators |
| Export | Built-in `saveCanvas()` / `saveGif()` / `saveFrames()` | PNG, GIF, frame sequence output |
| Capture | CCapture.js (optional) | Deterministic framerate video capture (WebM, GIF) |
| Headless | Puppeteer + Node.js (optional) | Automated high-res rendering, MP4 via ffmpeg |
| SVG | p5.js-svg 1.6.0 (optional) | Vector output for print — requires p5.js 1.x |
| Natural media | p5.brush (optional) | Watercolor, charcoal, pen — requires p5.js 2.x + WEBGL |
| Texture | p5.grain (optional) | Film grain, texture overlays |
| Fonts | Google Fonts / `loadFont()` | Custom typography via OTF/TTF/WOFF2 |

### Version Note

**p5.js 1.x** (1.11.3) is the default — stable, well-documented, broadest library compatibility. Use this unless a project requires 2.x features.

**p5.js 2.x** (2.2+) adds: `async setup()` replacing `preload()`, OKLCH/OKLAB color modes, `splineVertex()`, shader `.modify()` API, variable fonts, `textToContours()`, pointer events. Required for p5.brush. See `references/core-api.md` § p5.js 2.0.

## Pipeline

Every project follows the same 6-stage path:

```
CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY
```

1. **CONCEPT** — Articulate the creative vision: mood, color world, motion vocabulary, what makes this unique
2. **DESIGN** — Choose mode, canvas size, interaction model, color system, export format. Map concept to technical decisions
3. **CODE** — Write single HTML file with inline p5.js. Structure: globals → `preload()` → `setup()` → `draw()` → helpers → classes → event handlers
4. **PREVIEW** — Open in browser, verify visual quality. Test at target resolution. Check performance
5. **EXPORT** — Capture output: `saveCanvas()` for PNG, `saveGif()` for GIF, `saveFrames()` + ffmpeg for MP4, Puppeteer for headless batch
6. **VERIFY** — Does the output match the concept? Is it visually striking at the intended display size? Would you frame it?

## Creative Direction

Pick dimensions per project from [`references/aesthetic-dimensions.md`](references/aesthetic-dimensions.md)
(color system, noise, particles, shape language, motion, typography, shaders,
composition, interaction, blend modes, layering, texture). Follow the
per-project variation rules — never default configurations, always a custom
palette, background treatment, motion variety, and at least one invented
element. Invent at least one of: a custom palette, a novel noise field, a
unique particle behavior, a novel interaction, or a compositional technique.
Parameters should expose the algorithm's character, not be a generic menu.

## Workflow

### Step 1: Creative Vision

Before any code, articulate: mood/atmosphere, visual story over time, color world,
shape language, motion vocabulary, and what makes THIS sketch unique. Map the user's
prompt to concrete aesthetic choices — a "relaxing generative background" demands
different everything from a "glitch data visualization."

### Step 2: Technical Design

Pick the mode (7 in the table above), canvas size, renderer (`P2D` default or
`WEBGL` for 3D/shaders), frame rate, export target, and interaction model.
For interactive generative art, start from `templates/viewer.html`.

### Step 3: Code the Sketch

**Interactive generative art**: start from `templates/viewer.html` — it wires up
seed prev/next/random/jump, parameter sliders, and PNG download. Read the template
first, keep the fixed sections, replace the algorithm and parameter controls.

**Animations, video export, or simple sketches**: single bare HTML file with
inline p5.js. Skeleton: `CONFIG` → `PALETTE` → globals → `preload()` → `setup()` →
`draw()` → helpers → classes → event handlers. Use `randomSeed()` + `noiseSeed()`
for reproducibility, `colorMode(HSB, 360, 100, 100, 100)`, and `createGraphics()`
for layered composition. Full annotated HTML skeleton:
[`references/implementation-notes.md`](references/implementation-notes.md).

### Step 4: Preview & Iterate

Open the HTML directly in a browser (no server needed for basic sketches). For
local fonts/images use `scripts/serve.sh` or `python -m http.server`. Check
Chrome DevTools Performance tab for 60fps at the target export resolution, then
adjust parameters until the output matches the concept from Step 1.

### Step 5: Export

| Format | Method |
|--------|--------|
| **PNG** | `saveCanvas('output', 'png')` in `keyPressed()` — press 's' |
| **GIF** | `saveGif('output', 5)` — press 'g' |
| **Frame sequence** | `saveFrames('frame', 'png', 10, 30)` then `ffmpeg -i frame-%04d.png -c:v libx264 output.mp4` |
| **High-res PNG / MP4** | headless: `node scripts/export-frames.js sketch.html --width 3840 --height 2160 --frames 1` or `bash scripts/render.sh sketch.html output.mp4 --duration 30 --fps 30` (sketch must use `noLoop()` + `_p5Ready`) |
| **SVG** | `createCanvas(w, h, SVG)` with p5.js-svg, then `save('output.svg')` |

### Step 6: Quality Verification

Does the output match the concept? Is it sharp at the target display size? Does
it hold 60fps (30fps minimum for animations)? Do the colors work on both light
and dark monitors? What happens at canvas edges, on resize, after 10 minutes?

## Critical Implementation Notes

Full code examples for every rule below — FES disable, hot-path `Math.*`, seeded randomness,
fxhash platform support, HSB color mode, multi-octave noise + domain warp, `createGraphics()`
layers, vectorization, instance mode, WebGL gotchas, export key bindings, headless `noLoop()`
capture, and the agent workflow — are in
[`references/implementation-notes.md`](references/implementation-notes.md). Load it before writing
production code. The non-negotiable rules that apply to every sketch: disable FES and set
`pixelDensity(1)`, seed `randomSeed()`/`noiseSeed()`, use `colorMode(HSB, 360, 100, 100, 100)`,
layer with `createGraphics()`, and use `noLoop()` for headless capture.

## Performance Targets

Targets and budgets are in
[`references/implementation-notes.md`](references/implementation-notes.md) § Performance Targets.

## References

| File | Contents |
|------|----------|
| `references/core-api.md` | Canvas setup, coordinate system, draw loop, `push()`/`pop()`, offscreen buffers, composition patterns, `pixelDensity()`, responsive design |
| `references/shapes-and-geometry.md` | 2D primitives, `beginShape()`/`endShape()`, Bezier/Catmull-Rom curves, `vertex()` systems, custom shapes, `p5.Vector`, signed distance fields, SVG path conversion |
| `references/visual-effects.md` | Noise (Perlin, fractal, domain warp, curl), flow fields, particle systems (physics, flocking, trails), pixel manipulation, texture generation (stipple, hatch, halftone), feedback loops, reaction-diffusion |
| `references/animation.md` | Frame-based animation, easing functions, `lerp()`/`map()`, spring physics, state machines, timeline sequencing, `millis()`-based timing, transition patterns |
| `references/typography.md` | `text()`, `loadFont()`, `textToPoints()`, kinetic typography, text masks, font metrics, responsive text sizing |
| `references/color-systems.md` | `colorMode()`, HSB/HSL/RGB, `lerpColor()`, `paletteLerp()`, procedural palettes, color harmony, `blendMode()`, gradient rendering, curated palette library |
| `references/webgl-and-3d.md` | WEBGL renderer, 3D primitives, camera, lighting, materials, custom geometry, GLSL shaders (`createShader()`, `createFilterShader()`), framebuffers, post-processing |
| `references/interaction.md` | Mouse events, keyboard state, touch input, DOM elements, `createSlider()`/`createButton()`, audio input (p5.sound FFT/amplitude), scroll-driven animation, responsive events |
| `references/export-pipeline.md` | `saveCanvas()`, `saveGif()`, `saveFrames()`, deterministic headless capture, ffmpeg frame-to-video, CCapture.js, SVG export, per-clip architecture, platform export (fxhash), video gotchas |
| `references/troubleshooting.md` | Performance profiling, per-pixel budgets, common mistakes, browser compatibility, WebGL debugging, font loading issues, pixel density traps, memory leaks, CORS |
| `references/implementation-notes.md` | Full code examples: FES disable, hot-path Math, seeded randomness, fxhash, HSB, multi-octave noise, layers, vectorization, instance mode, WebGL gotchas, key bindings, headless noLoop(), annotated HTML skeleton, agent workflow, performance targets, creative-divergence strategies |
| `references/aesthetic-dimensions.md` | Aesthetic dimensions table (color, noise, particles, shapes, motion, typography, shaders, composition, interaction, blend modes, layers, texture) + per-project variation rules, invention prompts, parameter design philosophy |
| `templates/viewer.html` | Interactive viewer template: seed navigation (prev/next/random/jump), parameter sliders, download PNG, responsive canvas. Start from this for explorable generative art |
