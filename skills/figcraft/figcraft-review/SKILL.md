---
name: figcraft-review
description: Reviews native FigCraft files for structure, auto layout, visual consistency, accessibility, reference coverage, and prototype correctness. Produces a concise scorecard plus a pass/fail interaction gate grounded in inspected layers and preview evidence.
---

# FigCraft Review

Audit the actual `.figcraft` document, not screenshots alone. Inspect every in-scope page, screen, state, overlay, and prototype path. Use `list_commands` before remediation so fixes follow the current FigCraft schema.

Load the `figcraft` coordinator for the shared terms and completion rules.

## 1. Design Quality Score (100 Points)

### Structure and Auto Layout: 40

- **Auto-layout adoption: 15.** Repeated sections, controls, cards, tags, and lists use stable layout rather than fragile absolute placement.
- **Semantic naming: 15.** Layers use names such as `Screen/Home`, `Card/Article`, and `Button/Continue`, not defaults such as `Frame 45`.
- **Hierarchy and clipping: 10.** Nesting, parent-child relationships, sizing, constraints, clipping, and scrolling are deliberate.

### Tokens and Visual Consistency: 30

- **Color roles: 10.** Surfaces, text, accents, borders, and states are consistent with the reference or approved system.
- **Spacing and sizing: 10.** Equivalent elements use consistent spacing and size scales. Do not force a grid that conflicts with the reference.
- **Typography, radius, and effects: 10.** Equivalent hierarchy levels and component states remain consistent.

### Accessibility and Usability: 30

- **Target size: 15.** Use the target platform standard. For Apple interfaces, use at least 44×44 pt. If reviewing WCAG 2.2 AA, evaluate 2.5.8's 24×24 CSS px minimum and its exceptions; 44×44 CSS px belongs to the enhanced AAA criterion 2.5.5.
- **Contrast and readability: 10.** Target at least 4.5:1 for normal text and 3:1 for large text unless an approved standard differs.
- **Text resizing and overflow: 5.** Wrapping, auto-resize, maximum lines, clipping, and truncation behave intentionally.

Score only evidence visible in inspection or rendered output. Explain every deduction with a layer name/id and a concrete fix.

## 2. Reference Coverage Gate

When references were supplied, verify:

- every reference maps to an implemented screen, state, overlay, or responsive size;
- hierarchy, copy, key assets, and composition match;
- differences from the source are approved, necessary, or explicitly reported;
- multiple references have not been collapsed into one screen or expanded into unrequested pages.

Result: `PASS`, `FAIL`, or `NOT APPLICABLE`.

## 3. Asset, Type, and Size Gate

Check:

- screens use a real device preset from `frame.presets`, or a size the user specified;
- responsive variants, when requested, each come from their own preset and keep layer names aligned;
- illustrations and characters are real vector artwork, not primitives stacked to imitate curves, and authored artwork is reported as an interpretation rather than a reproduction;
- interface icons come from one icon set, with consistent weight, size box, and color role, and no icon frame is empty from a failed fetch;
- icons that carry state, such as selected versus inactive, differ the way the reference shows;
- supplied assets were imported rather than redrawn;
- imported SVG layers were renamed from `Group` and `Vector`, and `currentColor` black was recolored;
- `text.missingFonts` is empty, or every remaining entry is reported with a reason;
- no face was silently substituted, meaning font `warnings` were resolved or reported;
- text roles follow one scale instead of ad hoc sizes per layer.

Result: `PASS`, `FAIL`, or `NOT APPLICABLE`.

## 4. Prototype Correctness Gate

Keep this as a pass/fail gate outside the 100-point visual score. A polished design with broken behavior must not receive an unconditional approval.

Check:

- the intended flow has a valid start frame;
- every required button/CTA has the intended action;
- all navigation destinations exist and required screens are reachable;
- slider viewport, track size, overflow direction, clipping, and drag behavior are correct, checked by comparing track and viewport sizes because `overflow` is not reported by inspection;
- overlays open in the intended position and have required close/dismiss paths;
- back actions return to the expected state;
- alerts have correct trigger, actions, dismissal, and terminal state;
- component variants, variables, and conditionals reach the expected states, and every `changeTo` destination is a real variant of the same component set rather than a plain frame;
- hotspots align with the final visible controls, meet target size, and do not overlap unrelated controls;
- no stale IDs, orphan destinations, duplicate interactions, or unreachable required states remain;
- editable input is not claimed when the implementation only simulates input states;
- motion is consistent per journey, exits are not slower than entrances, nothing routine runs past roughly 400 ms, and `smartAnimate` pairs are named and nested identically across frames;
- interaction verdicts cite inspected interaction data; a successful `proto.preview` call is not accepted as runtime evidence, and remaining click-through checks are listed for the user.

Result: `PASS`, `FAIL`, or `NOT APPLICABLE`.

## 5. Workflow

1. Inspect the document with `inspect_document`; use `allPages: true` when several pages are in scope.
2. Use `get_node` for truncated or interaction-heavy subtrees.
3. Render temporary screenshots for all relevant screens and overlays.
4. Compare the result with the reference manifest or approved requirements.
5. Inspect interaction arrays, components, variables, destinations, and flow start points. `overflow` is not reported by inspection, so judge scrolling by comparing track and viewport sizes or by reading the saved document.
6. Check assets and type: confirm screen sizes against `frame.presets`, run `text.missingFonts`, and inspect icon and illustration frames for real vector children rather than empty or placeholder layers.
7. Trace the reported interaction graph by hand. Playback is not observable from this tool set: in a headless session `proto.preview` and `proto.present` succeed without a window, and `pointer` drives the canvas, not the player. List the click-through checks the user must run instead of calling them verified.
8. Save only after approved remediation. Inspect once more after saving.

Do not apply fixes without user approval when they change visual direction, information architecture, navigation, content, or product behavior. Safe mechanical fixes may be offered separately.

## 6. Report Format

```markdown
# FigCraft Review

**File:** `ui.figcraft`
**Design score:** 88 / 100
**Reference coverage:** PASS
**Assets, type & size:** FAIL
**Prototype correctness:** FAIL

| Dimension | Score | Main issue |
|---|---:|---|
| Structure & Auto Layout | 35 / 40 | Two card rows use fragile absolute positions |
| Tokens & Consistency | 27 / 30 | One secondary text color is inconsistent |
| Accessibility & Usability | 26 / 30 | Close target is 32×32 pt |

## Blocking findings
1. `Button/Confirm` → destination id is missing. Reconnect it to `Screen/Success`.
2. `Overlay/Delete` has no explicit close action while outside dismissal is disabled.
3. `Icon/Filter` is an empty frame; the Iconify fetch returned nothing. Re-source it from the same set.

## Other findings
- `Frame 45` should be renamed `Section/Recommendations`.

## Verification limits
- Free-form typing was not verified because this prototype simulates input states.
```

Use `PASS` only when the inspected and tested evidence satisfies every in-scope requirement. If preview interaction cannot be automated, state the manual checks instead of calling the gate fully verified.
