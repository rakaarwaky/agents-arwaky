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
    - architecture-diagram
---

# Pretext Creative Demos

[`@chenglou/pretext`](https://github.com/chenglou/pretext) is a 15KB
zero-dependency TypeScript library by Cheng Lou (React core, ReasonML,
Midjourney) for **DOM-free multiline text measurement and layout**: given
`(text, font, width)`, it returns line breaks, per-line widths, per-grapheme
positions, and total height via canvas measurement, no reflow. It is a creative
primitive: reflow paragraphs around a moving sprite at 60fps, build games whose
level geometry is real words, shatter text into particles, or pack
shrink-wrapped multiline UI with zero `getBoundingClientRect` thrash.

This skill makes **cool demos** with it — the kind people post to X. The
community demo corpus is at `pretext.cool` and `chenglou.me/pretext`.

## Global rules

- **Creative standard.** Pretext returns numbers; you draw the thing. Don't
  ship a "hello world" demo — the `hello-orb-flow.html` template is the
  *starting* point; every delivered demo adds intentional color, motion,
  composition, and one visual detail the user didn't ask for. Dark backgrounds
  with considered palettes (amber-on-black, editorial white-on-charcoal,
  risograph pastels). Proportional fonts are the point — lean into "not
  monospaced". Use real source text, never lorem ipsum. First-paint
  excellence: no loading states, no blank frames.
- **Scope.** Use pretext only when the demo needs to know line breaks *before*
  rendering. Don't use for static CSS/HTML layouts, rich text editors, image →
  text (use `ascii-art` / `ascii-video` skills), or canvas generative art with
  no text role (use `p5js`).
- **Stack.** Single self-contained HTML file per demo, no build step:
  `@chenglou/pretext` via esm.sh CDN, Canvas 2D for rendering, `Intl.Segmenter`
  for grapheme splits, raw DOM events for interaction. Details:
  [`references/stack-and-use-cases.md`](references/stack-and-use-cases.md).
- **API invariants.** Call `prepare()`/`prepareWithSegments()` once per
  text+font pair and cache the handle; set `ctx.font` once per frame; keep the
  `prepare()` font string exactly in sync with the rendered CSS; use
  `Intl.Segmenter` for grapheme splits. Pitfalls + verification:
  [`references/pitfalls.md`](references/pitfalls.md).

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| API & use cases | [`references/stack-and-use-cases.md`](references/stack-and-use-cases.md) | The two use cases (measure-only vs measure+render), streaming variable-width flow, helpers, pinned CDN import. |
| Pick a pattern | [`references/patterns.md`](references/patterns.md) | Community demo patterns and which pretext API each uses. Pick one, riff on it — don't invent a new category unless asked. |
| Pitfalls & verification | [`references/pitfalls.md`](references/pitfalls.md) | Performance notes, 8 common pitfalls, 10-item verification checklist. |
| Starters | `templates/hello-orb-flow.html`, `templates/donut-orbit.html` | Working starters: reflow around a moving orb; measured ASCII logo obstacles with draggable wire shapes. |
| Inspiration | [`references/community-demos.md`](references/community-demos.md) | Clone-worthy community demos and the official playground gallery. |
