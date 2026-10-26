# Pretext — Performance Notes, Common Pitfalls, and Verification Checklist

## Performance Notes

- `prepare()` / `prepareWithSegments()` is the expensive call. Do it **once** per text+font pair. Cache the handle.
- On resize, only rerun `layout()` / `layoutWithLines()` — never re-prepare.
- For per-frame animations where text doesn't change but geometry does, `layoutNextLineRange` in a tight loop is cheap enough to do every frame at 60fps for normal-length paragraphs.
- When rendering ASCII masks per frame, keep a cell buffer (`Uint8Array`/typed arrays), derive measured per-row obstacle spans from the cells or projected geometry, merge spans, then feed those spans into `layoutNextLineRange` before drawing text.
- Keep visual animation and layout animation coupled. If a sphere morphs into a cube, tween both the rendered cell buffer and the obstacle spans with the same value; otherwise the demo looks painted-on instead of physically reflowed.
- For fades, prefer layer opacity over changing glyph intensity or obstacle scale. Put transient ASCII sprites on their own canvas and fade the canvas with CSS/GSAP opacity so geometry does not appear to shrink.
- Canvas `ctx.font` setting is surprisingly slow; set it **once** per frame if font doesn't vary, not per `fillText` call.

## Common Pitfalls

1. **Drifting CSS/canvas font strings.** `ctx.font = "16px Inter"` measured, but CSS says `font-family: Inter, sans-serif; font-size: 16px`. Fine *if* Inter loads. If Inter 404s, CSS falls back to sans-serif and measurements drift by 5-20%. Always `preload` the font or use a web-safe family.

2. **Re-preparing inside the animation loop.** Only `layout*` is cheap. Re-calling `prepare` every frame will tank perf. Keep the prepared handle in module scope.

3. **Forgetting `Intl.Segmenter` for grapheme splits.** Emoji, combining marks, CJK — `"é".split("")` gives you two chars. Use `new Intl.Segmenter(undefined, { granularity: "grapheme" })` when sampling individual visible glyphs.

4. **`break: 'never'` chips without `extraWidth`.** In `rich-inline`, if you use `break: 'never'` for an atomic chip/mention, you must also supply `extraWidth` for the pill padding — otherwise chip chrome overflows the container.

5. **Using `@chenglou/pretext` from `unpkg` with TypeScript-only entry.** Use `esm.sh` — it compiles the TS exports to browser-ready ESM automatically. `unpkg` will 404 or serve raw TS.

6. **Monospace fallbacks silently erasing the whole point.** Users seeing monospace-looking output often have a CSS `font-family` that fell through to `monospace`. Verify the actual rendered font via DevTools.

7. **Skipping rows vs adjusting width** when flowing around a shape. If the corridor on this row is too narrow to fit a line, *skip the row* (`y += lineHeight; continue;`) rather than passing a tiny maxWidth to `layoutNextLineRange` — pretext will return one-grapheme lines that look broken.

8. **Shipping a cold demo.** The default first-paint looks tutorial-grade. Add: vignette, subtle scanline, idle auto-motion, one carefully chosen interactive response (drag, hover, scroll, click). Without these, "cool pretext demo" lands as "intern repro of the README."

## Verification Checklist

- [ ] Demo is a single self-contained `.html` file — opens by double-click or `python -m http.server`
- [ ] `@chenglou/pretext` imported via `esm.sh` with pinned version
- [ ] Corpus is real prose, not lorem ipsum, and matches the demo's concept
- [ ] Font string passed to `prepare` matches the CSS font exactly
- [ ] `prepare()` / `prepareWithSegments()` called once, not per frame
- [ ] Dark background + considered palette — not the default white canvas
- [ ] At least one interactive response (drag / hover / scroll / click) or idle auto-motion
- [ ] Tested locally with `python -m http.server` and confirmed no console errors
- [ ] 60fps on a mid-tier laptop (or graceful degradation documented)
- [ ] One "extra mile" detail the user didn't ask for
