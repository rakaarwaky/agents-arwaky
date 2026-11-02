---
name: pretext
description: "Build creative browser demos with DOM-free text layout."
when-to-use: "Use when the user wants a pretext creative demo — text flowing around a moving shape, ASCII-art effects using real words, text-as-geometry games, kinetic typography, multiline shrink-wrap UI, or per-glyph physics."
argument-hint: "<pattern> [output.html]"
metadata:
  tags:
    - creative-coding
    - typography
    - pretext
    - ascii-art
    - canvas
    - generative
    - text-layout
    - kinetic-typography
  related_skills:
    - p5js
    - claude-design
    - excalidraw
    - architecture-diagram
---

# Pretext Creative Demos

## Overview

[`@chenglou/pretext`](https://github.com/chenglou/pretext) is a 15KB zero-dependency TypeScript library by Cheng Lou (React core, ReasonML, Midjourney) for **DOM-free multiline text measurement and layout**. It does one thing: given `(text, font, width)`, return the line breaks, per-line widths, per-grapheme positions, and total height — all via canvas measurement, no reflow.

That sounds like plumbing. It is not. Because it is fast and geometric, it is a **creative primitive**: you can reflow paragraphs around a moving sprite at 60fps, build games whose level geometry is made of real words, drive ASCII logos through prose, shatter text into particles with exact per-grapheme starting positions, or pack shrink-wrapped multiline UI without any `getBoundingClientRect` thrash.

This skill exists so Hermes can make **cool demos** with it — the kind people post to X. See `pretext.cool` and `chenglou.me/pretext` for the community demo corpus.

## When to Use

Use when the user asks for:

- A "pretext demo" / "cool pretext thing" / "text-as-X"
- Text flowing around a moving shape (hero sections, editorial layouts, animated long-form pages)
- ASCII-art effects using **real words or prose**, not monospace rasters
- Games where the playfield / obstacles / bricks are made of text (Tetris-from-letters, Breakout-of-prose)
- Kinetic typography with per-glyph physics (shatter, scatter, flock, flow)
- Typographic generative art, especially with non-Latin scripts or mixed scripts
- Multiline "shrink-wrap" UI (smallest container width that still fits the text)
- Anything that would require knowing line breaks *before* rendering

Don't use for:

- Static SVG/HTML pages where CSS already solves layout — just use CSS
- Rich text editors, general inline formatting engines (pretext is intentionally narrow)
- Image → text (use `ascii-art` / `ascii-video` skills)
- Pure canvas generative art with no text role — use `p5js`

## Creative Standard

This is visual art rendered in a browser. Pretext returns numbers; **you** draw the thing.

- **Don't ship a "hello world" demo.** The `hello-orb-flow.html` template is the *starting* point. Every delivered demo must add intentional color, motion, composition, and one visual detail the user didn't ask for but will appreciate.
- **Dark backgrounds, warm cores, considered palette.** Classic amber-on-black (CRT / terminal) works, but so do cold-white-on-charcoal (editorial) and desaturated pastels (risograph). Pick one and commit.
- **Proportional fonts are the point.** Pretext's whole vibe is "not monospaced" — lean into it. Use Iowan Old Style, Inter, JetBrains Mono, Helvetica Neue, or a variable font. Never default sans.
- **Real source/text, not lorem ipsum.** The corpus should mean something. Short manifestos, poetry, real source code, a found text, the library's own README — never `lorem ipsum`.
- **First-paint excellence.** No loading states, no blank frames. The demo must look shippable the instant it opens.

## Stack

Single self-contained HTML file per demo. No build step.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | `@chenglou/pretext` via `esm.sh` CDN | Text measurement + line layout |
| Render | HTML5 Canvas 2D | Glyph rendering, per-frame composition |
| Segmentation | `Intl.Segmenter` (built-in) | Grapheme splitting for emoji / CJK / combining marks |
| Interaction | Raw DOM events | Mouse / touch / wheel — no framework |

```html
<script type="module">
import {
  prepare, layout,                   // use-case 1: simple height
  prepareWithSegments, layoutWithLines,  // use-case 2a: fixed-width lines
  layoutNextLineRange, materializeLineRange, // use-case 2b: streaming / variable width
  measureLineStats, walkLineRanges,  // stats without string allocation
} from "https://esm.sh/@chenglou/pretext@0.0.6";
</script>

```text

Pin the version. `@0.0.6` at time of writing — check [npm](https://www.npmjs.com/package/@chenglou/pretext) for the latest if demo behavior is off.

## The Two Use Cases

Almost everything reduces to one of these two shapes. Learn both.

### Use-case 1 — measure, then render with CSS/DOM

```js
const prepared = prepare(text, "16px Inter");
const { height, lineCount } = layout(prepared, 320, 20);

```text

You still let the browser draw the text. Pretext just tells you how tall the box will be at a given width, **without** a DOM read. Use for:

- Virtualized lists where rows contain wrapping text
- Masonry with precise card heights
- "Does this label fit?" dev-time checks
- Preventing layout shift when remote text loads

**Keep `font` and `letterSpacing` exactly in sync with your CSS.** The canvas `ctx.font` format (e.g. `"16px Inter"`, `"500 17px 'JetBrains Mono'"`) must match the rendered CSS, or measurements drift.

### Use-case 2 — measure *and* render yourself

```js
const prepared = prepareWithSegments(text, FONT);
const { lines } = layoutWithLines(prepared, 320, 26);
for (let i = 0; i < lines.length; i++) {
  ctx.fillText(lines[i].text, 0, i * 26);
}

```text

This is where the creative work lives. You own the drawing, so you can:

- Render to canvas, SVG, WebGL, or any coordinate system
- Substitute per-glyph transforms (rotation, jitter, scale, opacity)
- Use line metadata (width, grapheme positions) as geometry

For **variable-width-per-line** flow (text around a shape, text in a donut band, text in a non-rectangular column):

```js
let cursor = { segmentIndex: 0, graphemeIndex: 0 };
let y = 0;
while (true) {
  const lineWidth = widthAtY(y);  // your function: how wide is the corridor at this y?
  const range = layoutNextLineRange(prepared, cursor, lineWidth);
  if (!range) break;
  const line = materializeLineRange(prepared, range);
  ctx.fillText(line.text, leftEdgeAtY(y), y);
  cursor = range.end;
  y += lineHeight;
}

```text

This is the most important pattern in the whole library. It's what unlocks "text flowing around a dragged sprite" — the demo that went viral on X.

### Helpers worth knowing

- `measureLineStats(prepared, maxWidth)` → `{ lineCount, maxLineWidth }` — the widest line, i.e. multiline shrink-wrap width.
- `walkLineRanges(prepared, maxWidth, callback)` — iterate lines without allocating strings. Use for stats/physics over graphemes when you don't need the characters.
- `@chenglou/pretext/rich-inline` — the same system but for paragraphs mixing fonts / chips / mentions. Import from the subpath.

## Demo Recipe Patterns

Community demo patterns (reflow around obstacle, text-as-geometry games, shatter/particles,
ASCII obstacle typography, editorial multi-column, kinetic type, multiline shrink-wrap)
and which pretext API each one uses are in
[`references/patterns.md`](references/patterns.md). Pick one pattern, riff on it —
don't invent a new category unless asked.

Working starters: `templates/hello-orb-flow.html` (reflow around a moving orb) and
`templates/donut-orbit.html` (measured ASCII logo obstacles, draggable wire shapes).

## Performance Notes, Pitfalls, and Verification

Full performance notes, 8 common pitfalls, and the 10-item verification
checklist are in [`references/pitfalls.md`](references/pitfalls.md).
Key rules: call `prepare()`/`prepareWithSegments()` **once** per text+font
pair and cache the handle; set `ctx.font` once per frame; use `Intl.Segmenter`
for grapheme splits; verify the rendered CSS font matches the `prepare()` font
string; and test locally with `python -m http.server` before shipping.

## Reference: Community Demos

Clone these for inspiration / patterns (all MIT-ish, linked from [pretext.cool](https://www.pretext.cool/)):

- **Pretext Breaker** — breakout with word-bricks — `github.com/rinesh/pretext-breaker`
- **Tetris × Pretext** — `github.com/shinichimochizuki/tetris-pretext`
- **Dragon animation** — `github.com/qtakmalay/PreTextExperiments`
- **Somnai editorial engine** — `github.com/somnai-dreams/pretext-demos`
- **Bad Apple!! ASCII** — `github.com/frmlinn/bad-apple-pretext`
- **Drag-sprite reflow** — `github.com/dokobot/pretext-demo`
- **Alarmy editorial clock** — `github.com/SmisLee/alarmy-pretext-demo`

Official playground: [chenglou.me/pretext](https://chenglou.me/pretext/) — accordion, bubbles, dynamic-layout, editorial-engine, justification-comparison, masonry, markdown-chat, rich-note.
