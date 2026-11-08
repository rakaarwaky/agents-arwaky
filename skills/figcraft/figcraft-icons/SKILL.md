---
name: figcraft-icons
description: Maps interface icons to a real icon set through the Iconify API and imports them into FigCraft as editable vectors. Use whenever a reference or specification calls for interface icons instead of hand-drawn glyphs.
---

# FigCraft Icons

Interface icons are a sourcing problem, not a drawing problem. Hand-built glyphs drift in weight, grid, and style; a published icon set stays consistent. Use Iconify to find the icon, then import it as native vectors.

Load the `figcraft` coordinator for intake and scope rules. Use `figcraft-svg` for illustrations and characters, which are not icons.

## 1. Never Guess an Icon Name

Icon names are not predictable across sets. A guessed name returns an empty response, and an empty file imports as nothing.

Search first:

```bash
curl -s "https://api.iconify.design/search?query=whale&limit=12"
```

The response reports the total and a list of `prefix:name` identifiers. Pick from that list only. Verified failure mode: `ph:whale-duotone` looks plausible and returns a 9-byte empty body, because that icon does not exist.

Validate before importing. An SVG smaller than roughly 100 bytes, or one that does not contain a `<path`, `<circle`, or `<rect`, is a miss. Search again with a different term rather than inventing a name.

## 2. Pick One Set and Stay in It

Read the reference and match its icon personality, then choose a single family for the whole document:

| Reference look | Candidate sets |
|---|---|
| Thin or medium outline, rounded caps | `lucide`, `tabler`, `ph` (regular) |
| Solid filled | `ph` (fill), `mdi`, `material-symbols` |
| Duotone or two-tone | `ph` (duotone), `material-symbols` (two-tone) |
| Playful, rounded, childlike | `fluent-emoji-flat`, `noto`, `streamline-emojis` |
| Platform-native | `material-symbols` for Android, `tabler` or `lucide` as a neutral iOS stand-in |

Mixing sets in one screen is a visible defect. If one needed icon is missing from the chosen set, decide deliberately: pick a near equivalent from the same set, or author it with `figcraft-svg` to match that set's weight and grid. Say which you did.

Emoji-style sets carry their own colors and are illustrations rather than icons; use them only when the reference clearly uses that look.

## 3. Fetch and Import

Request at the size the design needs, then import:

```bash
curl -sL "https://api.iconify.design/lucide/house.svg?height=24" -o /tmp/icons/home.svg
```

```json
{"command": "file.import", "params": {"path": "/tmp/icons/home.svg", "x": 0, "y": 0}}
```

Useful query parameters: `height` or `width` to size it, and `color` to set a flat color before import.

Verified import result for a `lucide` icon: a frame named after the file, containing a group of stroked vector layers, with `currentColor` resolved to solid black and layers named `Group` and `Vector`.

## 4. Normalize Every Imported Icon

1. Rename the frame to the document's scheme, for example `Icon/Home`, and rename generic child layers.
2. Recolor. Stroke icons carry `strokes`; filled icons carry `fills`. Set the one the icon actually uses.
3. Set stroke weight consistently across the set so icons look like siblings.
4. Size on a consistent box, commonly 20, 24, or 28, and keep that box constant per context.
5. Reparent into the control that owns the icon, and give the control the touch target. The icon is the glyph, not the hit area.
6. Make a component for any icon used more than once, so a later swap updates every instance.

## 5. Coverage Check

Before handing off:

- Every icon the reference shows has a real imported icon, not a placeholder shape.
- All icons come from one set, except deliberate exceptions you reported.
- Weight, size box, and color roles are consistent.
- Active and inactive states differ the way the reference shows, for example filled when selected and outline when not.
- No icon frame is empty from a failed fetch. Inspect the tree and confirm each has vector children.

## 6. Boundaries

- Respect each set's license. Iconify redistributes sets under their own licenses; report the sets used so the user can check attribution.
- Do not fabricate an icon for a concept the reference does not show.
- Do not substitute a different symbol than the reference uses because it was easier to find. Ask when the intended meaning is unclear.
- If the network is unavailable, say so and ask whether to author glyphs with `figcraft-svg` instead of silently drawing approximations.
