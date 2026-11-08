---
name: figcraft
description: Coordinates end-to-end FigCraft work from one or more visual references or written requirements through native design construction, interactive prototyping, verification, review, and save. Use for any request to create, reconstruct, prototype, or audit a .figcraft interface.
---

# FigCraft Coordinator

Use FigCraft as a Figma-class design and prototyping tool. All sub-workflows below live in this one skill; load no separate skill for FigCraft work.

## FigCraft Sub-Workflows (labeled subsections)

### 1. Builder — screens, components, auto layout
Turn supplied references or approved written requirements into editable native `.figcraft` designs. Match the source exactly (hierarchy, layout, copy, typography, color, radius, effects, imagery, visible states). Build natively with frames, auto layout, components, instances, vectors, styles, and variables. Keep scope exact: build only the screens, states, overlays, and responsive sizes represented by the references or explicitly approved requirements. Ask on consequential ambiguity (page mapping, navigation outcomes, hidden states, product copy, data meaning). Delegate artwork to the SVG subsection, icons to the Icons subsection, and type to the Typography subsection. Before creating layers, inventory every reference in a manifest (Ref, Document page, Screen/frame, State/overlay, Viewport, Notes). Prefer auto layout for content sections, controls, card rows, lists, tags, navigation; use absolute positioning for overlays, floating controls, status chrome, decorative layers. Semantic names: `Screen/Home`, `Section/Recommendations`, `Card/Article`, `Button/Continue`, `Input/Email/Default`, `Overlay/ConfirmDelete`. Call `list_commands` before unfamiliar operations; use direct MCP tools directly and command envelopes only inside `run_command` or `batch`. Batch related operations into one undo step. Coordinates are relative to the immediate parent; auto-layout children are positioned by layout properties, not manual `x`/`y`. Import supplied SVG/image assets with `file.import` rather than redrawing. Verify each screen: inspect subtree with `get_node`/`inspect_document`, render temporary `screenshot`, compare against source, correct mismatches before prototyping. Save through `save_file` (create the target folder first), then re-inspect to confirm the active document path and coverage.

### 2. Icons — interface icon sourcing
Interface icons are a sourcing problem, not a drawing problem. Hand-built glyphs drift in weight, grid, and style; a published icon set stays consistent. Never guess an icon name — search Iconify first (`curl -s "https://api.iconify.design/search?query=...&limit=12"`) and pick only from the returned `prefix:name` list. Validate before importing: an SVG smaller than ~100 bytes or without `<path`, `<circle`, or `<rect` is a miss. Pick one set per document and stay in it — matching sets by reference look (outline: `lucide`, `tabler`, `ph` regular; solid: `ph` fill, `mdi`, `material-symbols`; duotone: `ph` duotone, `material-symbols` two-tone; platform-native: `material-symbols` for Android). Mixing sets in one screen is a visible defect. Fetch at the size the design needs (`height`/`width`/`color` query params), import via `file.import`, then normalize: rename frame to document scheme (e.g. `Icon/Home`), recolor, set consistent stroke weight, size on a consistent box (20/24/28), reparent into the owning control, make a component for repeated use. Every icon must have real vector children — no empty frames from failed fetches. Respect each set's license and report the sets used.

### 3. SVG — illustrations, characters, logos, organic artwork
Use this for artwork rather than UI chrome: mascots, characters, illustrations, logos, badges, curved forms that ellipses and rectangles cannot express. If the user supplied the asset as a file, `file.import` the original — never redraw it. Boxes, bars, pills, simple discs go to Builder; standard interface icons go to Icons; copy text goes in natively (SVG `font-family` is lost on import — do not place copy inside SVG). Write SVG to a temp file, then import. Set `width`, `height`, and matching `viewBox`. Name ids with the document's semantic scheme (`Whale/Body`, `Mascot/Head`). Order elements back to front (last on top). Use the document's palette. Prefer a few deliberate paths over dozens of fragments. Omit unconfirmed filters/masks/effects. For hand-drawn/marker looks, use stroked open paths with `stroke.widthProfile` (`uniform`, `wedge`, `taper`, `eye`, `rounded`, `pinch`) and `stroke.brush` (`taper`, `ink`, `ribbon`, `bristle`). After import: rename root frame from file name to semantic name, rename generic layers (`Group`, `Vector`), recolor black from `currentColor`, reparent into the owning screen/component, convert reused artwork to a component, delete empty groups. Judge small artwork at its real size — simplify for small sizes rather than shrinking detailed versions. Report every authored artwork as an interpretation unless the original file was supplied.

### 4. Typography — typeface choice and installation
Type carries most of a reference's character. Describe what you observe (skeleton, weight range, contrast, terminals, roundness, width; geometric/grotesque/humanist/rounded/hand-drawn). Do not claim to identify a typeface with certainty from an image — offer two or three candidates with reasons, and say which you will use unless told otherwise. Check `text.fonts` before downloading; `text.missingFonts` returns families not installed. `font.downloads` returns `allowed` — if false, tell the user the exact switch to turn on or agree on an installed family; do not keep retrying. If true, `font.download {family}` then poll until `state` is `installed`, then re-run `text.missingFonts`. Only Google Fonts and Noto are reachable; commercial/custom fonts need `text.loadFont {path|data}` (session-only). Build a small type scale (display/title, section heading, card/list title, body, caption/metadata/pill) with size, face, line height, letter spacing per role; reuse across screens. Verify no silent fallback: `text.missingFonts` empty or every entry reported with a reason; `warnings` resolved or reported.

### 5. Prototyper — wiring interactions
Add interactions only after required screens, overlays, and states exist. Before wiring, write an interaction inventory (Source layer, Trigger, Action(s), Destination/state, Transition, Close/back path, Expected result). Every required interactive element must appear; a visible control may remain non-interactive only when intentionally static. Call `list_commands` before using prototype features. Native actions may include: `navigate`, `back`, `scrollTo`, `openOverlay`, `swapOverlay`, `closeOverlay`, `openUrl`, `changeTo` (component variants), `setVariable`, `setVariableMode`, `conditional`. Attach interactions to the final visible button/container, not child label/icon. Every overlay must have a close path (visible Close/Cancel/backdrop controls with `closeOverlay`, or outside-click dismissal when appropriate). Use component variants + `changeTo` for direct visual states; variables + `conditional` for flows depending on previous actions. `changeTo` accepts any layer id without complaint — confirm the source is an instance and the destination is a real variant of the same component set. No native free-form text entry exists in the current command contract — simulate input only with states/variables/key triggers/conditionals, labeled as simulated. Hotspot: prefer the visible control frame; if separate, name it `Hotspot/<purpose>`, match bounds to the full target, do not cover unrelated controls. Verify: inspect `interactions` per layer and `flows` per page; walk the graph for reachability, missing close paths, stale IDs, unreachable states. Save, then inspect again.

### 6. Motion — transition and animation polish
Run this last — motion polish on a broken flow hides the breakage. Prototyper must have every path wired and inspected first. Transition types: `instant`, `dissolve`, `smartAnimate`, `moveIn`, `moveOut`, `push`, `slideIn`, `slideOut` (direction: left/right/top/bottom). Fields: `durationMs`, `easing` (linear/easeIn/easeOut/easeInOut/easeInBack/easeOutBack/easeInOutBack/gentle/quick/bouncy/slow, or custom bezier/spring), `delayMs`, `afterDelay {ms}` trigger. Choose motion from the interaction, not habit: tab switch → instant/dissolve 0–120ms easeOut; forward detail → slideIn/push left 260–320ms easeInOut; back → mirrored 240–300ms; bottom sheet open → moveIn bottom 220–280ms easeOut; close → moveOut bottom 180–240ms easeIn; smartAnimate morph → 240–320ms easeInOut/gentle; toast dismiss → dissolve on afterDelay 160–240ms. Entering motion can be slower than exiting; nothing routine exceeds ~400ms. `smartAnimate` pairs layers by identical name, hierarchy position, and type across frames — duplicate the first state, then edit, rather than rebuilding. Chain `afterDelay` interactions for timed sequences; give the user an immediate way out. Verify interactions via `inspect_document`/`get_node`; playback cannot be automated (headless `proto.preview`/`proto.present` return success without a window — never treat as runtime evidence).

### 7. Review — quality gate and scorecard
Audit the actual `.figcraft` document, not screenshots alone. Design Quality Score (100 pts): Structure & Auto Layout 40 (auto-layout adoption 15, semantic naming 15, hierarchy/clipping 10); Tokens & Visual Consistency 30 (color roles 10, spacing/sizing 10, typography/radius/effects 10); Accessibility & Usability 30 (target size 15 — Apple ≥44×44 pt, WCAG 2.2 AA 24×24 CSS px; contrast 4.5:1 normal / 3:1 large; text resizing/overflow 5). Explain every deduction with a layer name/id and a concrete fix. Reference Coverage Gate (PASS/FAIL/N/A): every reference maps to an implemented screen/state/overlay/responsive size; composition matches; differences approved or reported. Asset/Type/Size Gate: screens use real `frame.presets`; icons from one set with consistent weight/size/color; `text.missingFonts` empty or explained; no silent font fallback. Prototype Correctness Gate (pass/fail outside the 100-point score): valid start frame, every CTA has intended action, destinations exist and screens reachable, slider track larger than viewport (overflow not reported by inspection — check by size comparison or reading the saved document), overlays open in intended position with close paths, back actions return to expected state, `changeTo` destinations are real variants, hotspots meet target size and don't overlap, no stale IDs/orphan destinations, motion consistent per journey with exits not slower than entrances. Report format: file, design score, reference coverage, assets/type/size, prototype correctness, blocking findings, other findings, verification limits.

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
