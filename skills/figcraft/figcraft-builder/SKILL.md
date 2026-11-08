---
name: figcraft-builder
description: Builds native FigCraft UI designs and screens from one or more reference images or written specifications. Applies reference mapping, reusable components, auto layout, visual fidelity, and strict scope control without inventing screens or content.
---

# FigCraft Builder

Turn supplied references or approved written requirements into editable native `.figcraft` designs. Pair with `figcraft-prototyper` for interactions and `figcraft-review` for the final quality gate.

Load the `figcraft` coordinator for intake, scope, and completion rules.

## Core Rules

1. **Match the source.** Reconstruct hierarchy, layout, copy, typography, color, radius, effects, imagery, and visible states with care. Do not replace a distinctive reference with a generic template.
2. **Build natively.** Use frames, auto layout, components, instances, vectors, styles, and variables where they improve editability and consistency. Delegate artwork to `figcraft-svg`, icons to `figcraft-icons`, and type to `figcraft-typography`.
3. **Keep scope exact.** Build only the screens, states, overlays, and responsive sizes represented by the supplied references or explicitly approved requirements.
4. **Ask on consequential ambiguity.** Do not guess page mapping, navigation outcomes, hidden states, product copy, data meaning, or unsupported behavior.
5. **Verify, then save.** Inspect the layer tree and render temporary screenshots for visual checking. Do not export preview PNG files as deliverables unless requested.

## 1. Intake and Reference Manifest

Before creating layers, inventory every supplied reference:

| Ref | Document page | Screen/frame | State/overlay | Viewport | Notes |
|---|---|---|---|---|---|

For multiple references:

- Map every image to a screen, state, overlay, or responsive variant.
- Identify shared shell elements and reusable components.
- Compare references for deliberate differences versus accidental inconsistency.
- Preserve the user-provided order unless another flow is explicit.
- Ask if two references conflict or their relationship is unclear.

Do not stop after implementing only the first image when several references are in scope.

### No-image requests

Read the complete prompt and extract all explicit constraints before asking questions. If enough information exists, proceed. If not, ask only for decision-blocking details: target platform/viewport, required screens, exact or representative content, visual direction/design system, and required states/interactions.

Do not create filler pages, invented product features, fabricated data, or brand choices that change the task. Mark small reversible visual assumptions in the final report.

## 2. Visual Decomposition

For each reference or approved screen, record:

- viewport and safe-area behavior;
- fixed, sticky, scrollable, and overlay regions;
- content hierarchy and reading order;
- color and typography roles;
- spacing, grid, radius, stroke, and effect patterns;
- repeated elements suitable for components;
- likely interactive elements and all visible states;
- assets that must be imported, recreated, or requested.

Use the real device preset for the target. `frame.presets` lists what the engine offers and `frame.create {preset}` creates the frame at that exact size; the coordinator skill carries the catalog and the rules for choosing one. Use the reference's own dimensions when the user supplies them instead. Never force a remembered size, radius, or font when the source says otherwise.

## 3. Structure and Layout

Prefer auto layout for content sections, controls, card rows, lists, tags, navigation, and repeated components. Use absolute positioning for intentional overlays, floating controls, status chrome, and decorative layers.

For a detected slider or carousel, build both:

1. an outer viewport frame with the required width, clipping choice, and overflow direction;
2. an inner horizontal or vertical auto-layout track whose content exceeds the viewport.

Do not describe a row as a slider unless its structure can support overflow and the prototype requirement is handed to `figcraft-prototyper`.

Use semantic names such as:

- `Screen/Home`
- `Section/Recommendations`
- `Card/Article`
- `Button/Continue`
- `Input/Email/Default`
- `Overlay/ConfirmDelete`

Create components and variants for repeated controls or states. Avoid abstractions used only once unless they provide clear editing or prototype value.

## 4. MCP Usage

Call `list_commands` before unfamiliar operations. Use direct MCP tools directly; use command envelopes only inside `run_command` or `batch`.

Direct creation example:

```json
{
  "type": "frame",
  "name": "Screen/Home",
  "width": 390,
  "height": 844,
  "props": {
    "fill": "#FAF8F5",
    "clip": true,
    "layout": "vertical"
  }
}
```

Batch example:

```json
{
  "label": "Create recommendation card",
  "commands": [
    {
      "command": "node.create",
      "as": "card",
      "params": {
        "type": "frame",
        "name": "Card/Recommendation",
        "props": {"layout": "vertical", "gap": 8, "padding": 16}
      }
    },
    {
      "command": "node.create",
      "params": {
        "type": "text",
        "name": "Text/Title",
        "text": "Title",
        "parent": {"$ref": "card"}
      }
    }
  ]
}
```

Batch related operations into one undo step when practical. Do not use a huge opaque batch that is difficult to diagnose or verify.

Coordinates are relative to the immediate parent frame. Auto-layout children are positioned by layout properties rather than manual `x` and `y`.

### Icons and supplied assets

Build UI structure here and delegate the assets:

- Interface icons go to `figcraft-icons`, which sources them from a real icon set instead of hand-drawing glyphs.
- Illustrations, mascots, logos, and organic artwork go to `figcraft-svg`, which authors curves as SVG and imports them as editable vectors.
- Typeface choice and installing a family go to `figcraft-typography`.

When the user supplied an SVG or image, import the original with `file.import` rather than redrawing it. An SVG becomes an editable frame of shapes and an image becomes an image layer.

A simple one-off glyph can still be a native vector:

```json
{
  "type": "vector",
  "name": "Icon/Chevron",
  "parent": 12,
  "path": "M9 5l7 7-7 7",
  "props": {"fill": "#1C1C1E"}
}
```

Do not stack primitives to imitate detailed artwork, and do not invent an asset that was never provided. Ask for it.

## 5. Verification and Handoff

After each meaningful screen or reference group:

1. Inspect the relevant subtree with `get_node` or `inspect_document`.
2. Render a temporary `screenshot` and compare composition, spacing, clipping, typography, and visible state against the source.
3. Correct mismatches before prototyping.
4. Record interactive candidates and the intended outcome. If the outcome is not shown or specified, ask rather than invent it.

After the final visual edit, re-inspect IDs and bounds before prototype wiring. Visual restructuring can invalidate destinations or hotspot alignment.

Save through `save_file`, then inspect again to confirm the active document path, page/screen coverage, and final structure. `save_file` fails when the target folder does not exist, so create the folder first. Report what was built, which references were covered, assumptions, missing assets or limitations, and the target file path.
