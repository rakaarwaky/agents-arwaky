---
name: p5js
description: "p5.js sketches: gen art, shaders, interactive, 3D."
when-to-use: "Use when the user wants a p5.js sketch — generative art, shaders, interactive visualizations, canvas animations, 3D WebGL scenes, audio-reactive visuals, or data viz, exported as HTML/PNG/GIF/MP4/SVG."
argument-hint: "<generative|data-viz|interactive|animation|3d|image-processing|audio-reactive> [output.html|png|gif|mp4|svg] [--width W --height H --frames N --fps F]"
version: 1.1.0
author: SHL0MS, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, generative-art, p5js, canvas, interactive, visualization, webgl, shaders, animation]
    related_skills: [ascii-video, architecture-diagram]
---

# P5js

Production pipeline for interactive and generative visual art using p5.js.
Creates browser-based sketches, generative art, data visualizations, interactive
experiences, 3D scenes, audio-reactive visuals, and motion graphics — exported as
HTML, PNG, GIF, MP4, or SVG. Every project is a single self-contained HTML file
(no build step), and every project follows one ordered pipeline:

```
CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY
```

## Global rules

- **Creative standard.** This is visual art rendered in the browser; the canvas is
  the medium, the algorithm is the brush. Before writing code, articulate the
  creative concept: what the piece communicates, and what separates it from a
  tutorial example. First-render excellence is non-negotiable — if it looks like a
  p5.js tutorial exercise or "AI-generated creative coding," rethink before
  shipping.
- **Invention.** Go beyond the reference vocabulary: catalogs are starting
  palettes; combine, layer, and invent. Every delivered sketch includes at least
  one of a custom palette, a novel noise field, a unique particle behavior, a
  novel interaction, or a compositional technique, plus at least one visual detail
  the user didn't ask for but will appreciate.
- **Coherence.** Dense, layered, considered. Never flat white backgrounds; always
  compositional hierarchy, intentional color, and micro-detail. All elements serve
  a unified visual language — a sketch with ten unrelated effects is worse than
  three that belong together. Parameters should expose the algorithm's
  character, not be a generic menu.
- **Non-negotiable implementation rules** (every sketch): disable FES and set
  `pixelDensity(1)`; seed `randomSeed()`/`noiseSeed()`; use
  `colorMode(HSB, 360, 100, 100, 100)`; layer with `createGraphics()`; use
  `noLoop()` for headless capture. Full code examples for these and every other
  rule live in [`references/implementation-notes.md`](references/implementation-notes.md).
- **Stack.** Default is p5.js 1.11.3 (CDN); WebGL mode for 3D/shaders;
  p5.sound.js for audio; optional CCapture.js, Puppeteer + ffmpeg, p5.js-svg,
  p5.brush, p5.grain. Details: [`references/stack.md`](references/stack.md).
- **Verification.** The output must match the concept and be sharp at the target
  display size; hold 60fps at export resolution (30fps minimum for animations);
  survive canvas edges, resize, and 10 minutes of runtime. Check in Chrome
  DevTools before declaring done.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Mode selection | [`references/modes.md`](references/modes.md) | Match the request to one of 7 modes (generative, data-viz, interactive, animation, 3D, image processing, audio-reactive) and its deep-dive reference. |
| Concept / design / creative direction | [`references/aesthetic-dimensions.md`](references/aesthetic-dimensions.md) | Color system, noise, particles, shape language, motion, typography, shaders, composition, interaction, blend modes, layering, texture — plus per-project variation rules and invention prompts. |
| Coding the sketch | [`references/implementation-notes.md`](references/implementation-notes.md) | HTML skeleton (CONCEPT → CONFIG → PALETTE → globals → `preload()` → `setup()` → `draw()` → helpers → classes → event handlers), full code examples for every non-negotiable rule, performance targets and budgets. |
| Preview & iterate | [`references/preview-and-export.md`](references/preview-and-export.md) | Browser + local server preview workflow, 60fps DevTools check, iteration loop against the concept. |
| Export | [`references/export-pipeline.md`](references/export-pipeline.md) | PNG / GIF / frame-sequence / headless MP4 / SVG / high-res export methods, key bindings, ffmpeg capture, `_p5Ready` + `noLoop()` capture. |
| Verification | [`references/preview-and-export.md`](references/preview-and-export.md) § Verify | Quality gate: concept match, sharpness, performance, edge cases. |
| Topic deep-dives | `references/core-api.md`, `shapes-and-geometry.md`, `visual-effects.md`, `animation.md`, `typography.md`, `color-systems.md`, `webgl-and-3d.md`, `interaction.md`, `troubleshooting.md` | Load the matching file for a pipeline step; `modes.md` maps mode → topic. |
| Templates & scripts | `templates/viewer.html`, `scripts/serve.sh`, `scripts/export-frames.js`, `scripts/render.sh`, `scripts/setup.sh` | Interactive viewer template (seed nav, sliders, PNG download) for generative art; headless export and preview tooling. |
