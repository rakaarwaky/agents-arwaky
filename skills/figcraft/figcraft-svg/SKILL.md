---
name: figcraft-svg
description: Builds illustrations, characters, logos, and decorative artwork for FigCraft by authoring SVG and importing it as editable native vectors. Use when a reference image contains artwork that primitive shapes cannot reproduce faithfully.
---

# FigCraft SVG Illustration

Use this skill when a reference contains artwork rather than UI chrome: mascots, characters, illustrations, hand-drawn doodles, logos, badges, decorative scenery, or any curved form that ellipses and rectangles cannot express.

Load the `figcraft` coordinator for intake and scope rules. Pair with `figcraft-icons` for interface icons, which are a different problem.

## 1. Choose the Right Source

| Artwork in the reference | Approach |
|---|---|
| User supplied the asset as a file | `file.import` the original. Never redraw it by hand. |
| Boxes, bars, pills, simple discs, progress tracks | Native primitives in `figcraft-builder`. |
| Standard interface icon | `figcraft-icons` via Iconify. |
| Curved illustration, character, mascot, logo mark, organic shape | Author SVG here, then import. |
| Photography, raster texture, complex painted art | Cannot be authored. Ask the user for the asset. |

Do not approximate a detailed character with stacked ellipses when SVG curves are available. Do not claim an authored illustration reproduces the reference artwork; it is an interpretation unless the original file was supplied.

## 2. Verified Import Behavior

`file.import` accepts `{path}` or `{data (base64), name}` and turns an SVG into an editable frame of shapes. Confirmed against the engine:

- An `id` attribute on an element becomes that layer's name. Put an `id` on every shape and group.
- Groups become groups; nesting is preserved.
- `<circle>` becomes a real ellipse layer, not a path.
- Linear and radial gradients survive as gradient fills.
- Strokes survive, so stroke weight stays editable after import.
- `currentColor` resolves to solid black. Recolor after import.
- `<text>` becomes an editable text layer, but **the SVG `font-family` is lost**.
- The root frame is named after the file or the `name` you pass.
- Import returns the root frame id, and may return `warnings` listing what was dropped. Read them.

Because font family does not survive, **do not place copy inside the SVG**. Author text natively with `figcraft-builder` or `figcraft-typography`.

## 3. Authoring Rules

Write the SVG to a temporary file, then import it. Keep it clean:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" viewBox="0 0 200 120">
  <g id="Whale">
    <path id="Whale/Fluke" d="M42 62C28 52 14 32 18 10c18 10 30 32 36 48z" fill="#1D6FA3"/>
    <path id="Whale/Body" d="M40 70C40 40 70 22 108 22c40 0 62 20 62 44 0 18-22 30-58 30-40 0-72-10-72-26z" fill="#1D6FA3"/>
    <path id="Whale/Mouth" d="M120 72c14 6 28 4 38-4 6 14-10 22-26 20-10-2-14-10-12-16z" fill="#F2D06B"/>
    <circle id="Whale/Eye" cx="140" cy="48" r="5" fill="#15283A"/>
  </g>
</svg>
```

- Set `width`, `height`, and a matching `viewBox` so the artwork imports at the intended size.
- Name ids with the same semantic scheme the rest of the document uses, for example `Whale/Body` or `Mascot/Head`.
- Order elements back to front; the last element sits on top.
- Use the document's palette. Do not introduce colors absent from the reference or approved system.
- Prefer a few deliberate paths over dozens of fragments. A reviewer must be able to edit the result.
- Omit filters, masks, and effects you have not confirmed survive import; check `warnings` when you do use them.

## 4. Hand-Drawn and Marker Looks

When the reference artwork is a crayon, marker, pencil, or ink doodle, flat filled paths will look too clean. The engine can express the stroke character directly:

- `stroke.widthProfile` with `uniform`, `wedge`, `taper`, `eye`, `rounded`, or `pinch` varies weight along the path.
- `stroke.brush` with `taper`, `ink`, `ribbon`, or `bristle` stretches a brush along the path; `dots`, `stars`, `confetti`, and `leaves` scatter along it.
- Both accept `ids`, and both work on strokes that came in from an imported SVG.

Target the imported layers by their SVG id with `select.byName {query}`, then apply the profile or brush. Confirmed working sequence: `file.import` → `select.byName` → `stroke.brush` → `stroke.widthProfile`.

Author those elements as **stroked open paths** rather than filled outlines, otherwise there is no stroke for the brush to follow.

## 5. Normalize After Import

Imported art is not finished art. Always:

1. Rename the root frame from the file name to a semantic name.
2. Rename any layer the SVG left generic, such as `Group` or `Vector`.
3. Recolor anything that came in as black from `currentColor`.
4. Reparent the frame into the screen or component that owns it, and set its position and size.
5. Turn artwork reused across screens into a component so copies stay in sync.
6. Delete empty groups and stray layers the converter produced.

## 6. Fidelity Loop

1. Author the SVG and import it.
2. Render with `screenshot`, or `figcraft-cli render` when driving the CLI.
3. Compare against the reference: silhouette, proportion, weight, color, and where the artwork sits in the layout.
4. Fix the paths and re-import. Replace the previous layer rather than stacking a second copy.
5. Stop when the artwork reads as the same subject at the size it will actually be viewed.

Judge small artwork at its real size. A mark that reads correctly at 200 px can collapse into a blob at 28 px; simplify it for the small size instead of shrinking the detailed version.

## 7. Boundaries

- Do not invent a brand logo, mascot, or trademarked artwork. Ask for the asset.
- Do not trace or reproduce third-party artwork the user has no rights to.
- Do not pad a design with decorative illustrations the reference or brief does not call for.
- Report every piece of artwork you authored as an interpretation, and name what you could not match.
