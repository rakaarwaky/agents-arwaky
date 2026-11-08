---
name: figcraft
description: Coordinates end-to-end FigCraft work from one or more visual references or written requirements through native design construction, interactive prototyping, verification, review, and save. Use for any request to create, reconstruct, prototype, or audit a .figcraft interface.
---

# FigCraft Coordinator

Use FigCraft as a Figma-class design and prototyping tool. Route work through:

1. `figcraft-builder` for references, screens, components, and visual states.
2. `figcraft-svg` when the reference contains illustrations, characters, mascots, logos, or organic artwork.
3. `figcraft-icons` when the design needs interface icons.
4. `figcraft-typography` when the typeface matters or a family must be installed.
5. `figcraft-prototyper` when the request includes navigation, scrolling, buttons, overlays, alerts, forms, or state changes.
6. `figcraft-motion` as the final polish pass, only after the flows are wired and verified.
7. `figcraft-review` before reporting completion.

Build structure before artwork, artwork before motion. Do not tune transitions on a flow that is not yet correct.

Do not claim completion after saving alone. Verify the design tree, visual result, and every required interaction.

## Source of Truth

FigCraft commands and schemas can change. Before using an unfamiliar feature, call `list_commands` with a narrow filter such as `page`, `proto`, `overflow`, `component`, `variable`, or the intended action name. Use the returned command id and parameter schema exactly.

Distinguish these forms:

- Direct MCP tools such as `create_node`, `set_properties`, `inspect_document`, `get_node`, `screenshot`, and `save_file` receive their own parameters directly.
- `run_command` receives `{ "command": "<id>", "params": {...} }`.
- `batch` receives a `commands` array of command envelopes and may use `as` plus `$ref` between steps.

Never invent a command, property, trigger, action, or runtime capability.

## Terms

- **Document page:** An organizational canvas page.
- **Screen:** A top-level frame shown as one application state or route.
- **Overlay:** A modal, dialog, popup, menu, toast, or bottom sheet presented over a screen.
- **Component state:** A variant or variable-driven visual state such as default, focused, loading, success, error, selected, or disabled.
- **Hotspot:** The layer that owns a prototype interaction. Prefer the visible interactive container itself.

A document page may contain several screen frames. Do not treat every screen as a separate document page unless the user asks for that organization.

## Device Frames and Sizes

Never invent a screen size. The engine ships real device presets: `frame.presets` lists them, and `frame.create {preset}` creates a frame at that exact size. Call `frame.presets` and use a listed name, because the catalog changes between releases.

Verified presets at the time of writing, by category:

| Category | Preset | Size |
|---|---|---|
| Phone | iPhone 17 / 17 Pro | 402 × 874 |
| Phone | iPhone 17 Pro Max | 440 × 956 |
| Phone | iPhone Air | 420 × 912 |
| Phone | iPhone 16 | 393 × 852 |
| Phone | iPhone 16 Plus | 430 × 932 |
| Phone | iPhone SE | 320 × 568 |
| Phone | Android Compact | 412 × 917 |
| Phone | Android Medium | 700 × 840 |
| Tablet | iPad mini 8.3 | 744 × 1133 |
| Tablet | iPad Pro 11" | 834 × 1194 |
| Tablet | iPad Pro 12.9" | 1024 × 1366 |
| Tablet | Surface Pro 8 | 1440 × 960 |
| Tablet | Android Expanded | 1280 × 800 |
| Desktop | MacBook Air | 1280 × 832 |
| Desktop | MacBook Pro 14" | 1512 × 982 |
| Desktop | MacBook Pro 16" | 1728 × 1117 |
| Desktop | Desktop | 1440 × 1024 |
| Desktop | TV | 1280 × 720 |
| Watch | Apple Watch 41 / 45 / 42 mm | 176 × 215 / 198 × 242 / 187 × 223 |
| Presentation | Slide 16:9 | 1920 × 1080 |
| Presentation | Slide 4:3 | 1024 × 768 |
| Paper | A4 / A5 / A6 | 595 × 842 / 420 × 595 / 297 × 420 |

Choosing a target:

- Match the device the reference actually depicts. A tall phone mockup is not a tablet.
- When the user names a platform but no device, pick the current mainstream preset for it and say which you used: a modern iPhone for iOS, Android Compact for Android, Desktop 1440 × 1024 for web.
- Desktop web work is a viewport, not a device. Lay out content on a centered container inside the frame and state the container width and gutters.
- For responsive work, build each requested breakpoint as its own frame from its own preset, and keep layer names identical across them so component and motion pairing still work.
- Sizes are points, not physical pixels. Design at 1x and let export scale.
- Ask before adding breakpoints nobody requested.

## Intake and Scope Gate

### When references are supplied

Create a reference manifest before building:

| Reference | Page | Screen/state/overlay | Intended interactions | Notes |
|---|---|---|---|---|

Map every supplied image. Determine whether images represent different pages, screens, responsive sizes, overlays, or states of the same screen. Ask one focused question when that mapping or an interaction outcome is unclear and materially changes the result.

### When no reference image is supplied

Extract all available facts from the prompt first. Proceed without unnecessary questions when the prompt is sufficient. If a decision-critical fact is missing, ask for only what blocks the work:

- target platform and viewport;
- required screen, state, and overlay list;
- exact or representative content;
- visual direction or existing design system;
- expected action for each interactive element;
- required form, validation, success, error, loading, and empty states.

Do not invent product scope, pages, copy, data, branding, assets, or interaction outcomes. State harmless reversible assumptions. Ask before making assumptions that change navigation, content meaning, or required states.

## Capability Boundaries

Supported commands currently include screen navigation, back, scroll-to, overlays, overlay swapping/closing, URLs, component state changes, variables, conditionals, multiple actions, flow start points, and horizontal/vertical overflow. Confirm them through `list_commands` at runtime.

Do not promise free-form text entry in prototype playback unless a current FigCraft command explicitly supports it. `type_text` edits a design text layer; it does not prove that a prototype viewer can type into an input. If native input is unavailable, offer either a clearly labeled simulated input flow using states/variables/key triggers or a static form design. Ask which is acceptable.

## Definition of Done

Before reporting completion:

- Every approved reference maps to an implemented screen, state, or overlay.
- Screens use a real device preset, or a size the user specified.
- Visual hierarchy, copy, assets, layout, and viewport match the reference or approved specification.
- Illustrations and icons are real artwork, not placeholder shapes, and their origin is reported.
- No text renders in a silent font fallback.
- Required sliders scroll; required buttons have the intended action.
- Navigation destinations exist and required flows are reachable.
- Every overlay has the required open and close paths.
- Alerts and form states have the agreed trigger, result, dismissal, and terminal state.
- Hotspots align with the final visible layers and meet the target size.
- The prototype has an explicit flow start frame.
- `inspect_document` or `get_node` confirms structure and interactions after final edits.
- `screenshot` confirms the rendered design. A temporary screenshot used for verification is not an exported deliverable.
- Interaction claims rest on inspected interaction data, not on a successful `proto.preview` call. In a headless session preview and present return success without a window, so click-through stays a named manual check for the user.
- The final `.figcraft` file is saved and inspected again. `save_file` does not create missing folders.

Report implemented behavior, known limitations, manual checks, and the saved file path. Do not add unrequested screens or enhancements after the requirements are satisfied.
