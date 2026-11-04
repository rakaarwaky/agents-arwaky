---
name: ascii-video
description: "ASCII video: convert video/audio to colored ASCII MP4/GIF."
when-to-use: "Use when the user wants ASCII video — video-to-ASCII conversion, audio-reactive music visualizers, generative ASCII animations, hybrid video+audio, text/lyrics overlays, or TTS narration videos (MP4, GIF, image sequence)."
argument-hint: "<video-to-ascii|audio-reactive|generative|hybrid|lyrics|tts> <input> [output.mp4]"
---

# ASCII Video Production Pipeline

You build a single self-contained Python renderer per project and pipe it through the 6-stage pipeline `INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE` to produce colored ASCII character video (MP4, GIF, image sequence). No GPU required.

## Global Rules

- **Creative standard.** This is visual art — ASCII characters are the medium, cinema is the standard. Articulate the creative concept before writing code; the output must be visually striking on the first render (full rubric in `references/creative-standard.md`).
- **Adaptive tonemap only.** ASCII on black is inherently dark — use adaptive `tonemap()`, never `canvas * N` multipliers (implementation notes in `references/implementation-notes.md`).
- **Per-section variation.** Never use one config for the whole video — vary background effect, character palette, color strategy, and shader intensity per scene/section.
- **Invent, don't just pick.** The effect, shader, and palette catalogs are a starting vocabulary; every project includes at least one custom palette, effect, or visual moment.
- **Single-file renderer.** One self-contained Python script per project: NumPy + Pillow + ffmpeg CLI, with SciPy for audio modes; hardware-detect a quality profile before building.
- **Verify with test frames.** Render single frames at key timestamps before any full render; check `canvas.mean() > 8` for all ASCII content.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Video-to-ASCII** | Video file | ASCII recreation of source footage | `references/inputs.md` § Video Sampling |
| **Audio-reactive** | Audio file | Generative visuals driven by audio features | `references/inputs.md` § Audio Analysis |
| **Generative** | None (or seed params) | Procedural ASCII animation | `references/effects.md` |
| **Hybrid** | Video + audio | ASCII video with audio-reactive overlays | Both input refs |
| **Lyrics/text** | Audio + text/SRT | Timed text with visual effects | `references/inputs.md` § Text/Lyrics |
| **TTS narration** | Text quotes + TTS API | Narrated testimonial/quote video with typed text | `references/inputs.md` § TTS Integration |

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Workflow | [`references/workflow.md`](references/workflow.md) | 4-step build sequence: creative vision, technical design, script component order, quality verification. |
| Creative standard | [`references/creative-standard.md`](references/creative-standard.md) | Creative rubric: first-render excellence, proactively creative, cohesive aesthetic, dense/layered, per-section variation, project-specific invention. |
| Pipeline architecture | [`references/architecture.md`](references/architecture.md) | 6-stage pipeline, grid system, resolution presets, font selection, character palettes, color system (HSV + OKLAB + discrete RGB + harmony), `_render_vf()`, GridLayer. |
| Composition | [`references/composition.md`](references/composition.md) | 20 pixel blend modes, `blend_canvas()`, multi-grid composition, adaptive `tonemap()`, `FeedbackBuffer`, `PixelBlendStack`, masking/stencil system. |
| Effects | [`references/effects.md`](references/effects.md) | Effect building blocks: value field generators, hue fields, noise/fBM/domain warp, voronoi, reaction-diffusion, cellular automata, SDFs, strange attractors, particle systems, coordinate transforms, temporal coherence. |
| Shaders | [`references/shaders.md`](references/shaders.md) | `ShaderChain`, `_apply_shader_step()` dispatch, 38-shader catalog, audio-reactive scaling, transitions, tint presets, output format encoding, terminal rendering. |
| Scenes | [`references/scenes.md`](references/scenes.md) | Scene protocol, `Renderer` class, `SCENES` table, `render_clip()`, beat-synced cutting, parallel rendering, scene design patterns, worked examples, design checklist. |
| Inputs | [`references/inputs.md`](references/inputs.md) | Audio analysis (FFT, bands, beats), video sampling, image conversion, text/lyrics, TTS integration (ElevenLabs, voice assignment, audio mixing). |
| Optimization | [`references/optimization.md`](references/optimization.md) | Hardware detection, quality profiles, vectorized patterns, parallel rendering, memory management, performance budgets. |
| Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) | NumPy broadcasting traps, blend mode pitfalls, multiprocessing/pickling, brightness diagnostics, ffmpeg issues, font problems, common mistakes. |
| Critical notes | [`references/implementation-notes.md`](references/implementation-notes.md) | `tonemap()` code, font cell height (macOS), ffmpeg pipe deadlock, font compatibility, per-clip architecture, performance budgets. |
| Creative divergence | [`references/creative-divergence.md`](references/creative-divergence.md) | Use only when the user requests experimental/creative/unique output: Forced Connections, Conceptual Blending, Oblique Strategies. |

## Completion

- Test frames at key timestamps pass the brightness check (`canvas.mean() > 8`) and the creative vision check against `references/creative-standard.md`.
- Output matches the selected mode's shape (MP4, GIF, or image sequence).
