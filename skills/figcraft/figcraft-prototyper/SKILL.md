---
name: figcraft-prototyper
description: Wires and verifies native FigCraft prototypes for sliders, navigation, buttons, overlays, alerts, component states, variables, and conditional flows. Keeps interactions synchronized with the final design and never claims unsupported editable input.
---

# FigCraft Prototyper

Add interactions only after required screens, overlays, and states exist. Use current FigCraft commands discovered with `list_commands`; do not rely on remembered schemas.

Load the `figcraft` coordinator for intake, scope, and completion rules. This skill covers wiring and verification.

## 1. Interaction Contract

Before wiring, inspect all relevant pages and write a compact interaction inventory:

| Source layer | Trigger | Action(s) | Destination/state | Transition | Close/back path | Expected result |
|---|---|---|---|---|---|---|

Every required interactive element must appear in the inventory. A visible control may remain non-interactive only when the user did not request behavior or the inventory marks it intentionally static.

Ask before wiring when the intended destination, state change, dismissal behavior, validation rule, or terminal result is unclear. If a required destination does not exist, ask whether to build it and request a reference or specification. Never generate an unrequested placeholder screen.

## 2. Runtime Capability Check

Before using prototype features, call `list_commands` with focused filters such as `proto`, `overflow`, `variable`, `component`, and the intended action name. Follow the returned schema exactly.

Current native actions may include:

- `navigate`, `back`, and `scrollTo`;
- `openOverlay`, `swapOverlay`, and `closeOverlay`;
- `openUrl`;
- `changeTo` for component variants;
- `setVariable`, `setVariableMode`, and `conditional`;
- multiple actions on one interaction.

Do not claim a capability unless it appears in the current command contract.

### What the engine checks for you

The engine rejects an unknown trigger, action, transition, or easing name, an `overflow` value outside `none|horizontal|vertical|both`, an overlay `position` outside `center|topLeft|topCenter|topRight|bottomLeft|bottomCenter|bottomRight|manual`, and a `dest` id that does not exist. Read the error text; it names the accepted values.

The engine does not check that a `changeTo` destination is a variant, that an overlay has a close path, that a scroll track is larger than its viewport, or that a required screen is reachable. Those remain your responsibility.

## 3. Sliders and Scrollable Content

A slider is a scroll viewport plus an oversized content track:

- Outer frame: fixed viewport dimensions, intended `overflow` direction, and deliberate clipping.
- Inner frame: horizontal or vertical auto layout, consistent gap/padding, and content larger than the viewport.
- Cards/items: sized consistently unless the reference clearly varies them.

Use `onDrag` only when the intended interaction needs an explicit action. Native overflow does not require a fake click-navigation interaction.

### Verifying a slider

`overflow` is write-only for inspection: `inspect_document`, `get_node`, `inspect.properties`, and `inspect.code` do not report it even after it is set and saved. Verify it three ways instead:

1. The `set_properties` call succeeded. Since the engine rejects any other value, success means the direction was applied.
2. Inspect both frames and compare sizes. The track's reported width or height must exceed the viewport's; a track that fits inside its viewport cannot scroll regardless of the flag.
3. If proof in the file is required, read `overflow` on that node in the saved `.figcraft` document, which is a zip containing `document.json`.

Do not write "overflow confirmed via inspect_document." That field will not be there.

## 4. Navigation and Buttons

Attach interactions to the final visible button/container rather than a child label or icon. The interactive bounds should cover the complete control and meet the chosen touch-target standard.

Example using `run_command` and the current `proto.interaction.add` shape:

```json
{
  "command": "proto.interaction.add",
  "params": {
    "id": "button-layer-id",
    "trigger": {"type": "onClick"},
    "action": {"type": "navigate", "dest": "destination-frame-id"},
    "transition": {"type": "smartAnimate"},
    "durationMs": 300,
    "easing": "easeInOut"
  }
}
```

`transition`, `durationMs`, and `easing` are interaction-level fields unless the current `list_commands` contract says otherwise.

Use an explicit flow starting point through the current flow command. Ensure required destinations are reachable and back behavior is available where expected. Do not use Smart Animate by habit; choose instant, dissolve, smart animate, move, push, or slide based on the design and navigation model.

## 5. Overlays, Popups, and Alerts

Use overlays for dialogs, menus, popups, toasts, alerts, and bottom sheets when that matches the design.

```json
{
  "command": "proto.interaction.add",
  "params": {
    "id": "open-button-id",
    "trigger": {"type": "onClick"},
    "action": {
      "type": "openOverlay",
      "dest": "overlay-frame-id",
      "position": "bottomCenter",
      "close_on_outside": true,
      "background": "#00000055"
    },
    "transition": {"type": "moveIn", "direction": "bottom"},
    "durationMs": 250,
    "easing": "easeOut"
  }
}
```

Every overlay must have the close behavior required by the design:

- wire visible Close, Cancel, or backdrop controls with `closeOverlay` or the agreed action;
- use outside-click dismissal only when appropriate;
- prevent outside dismissal for destructive confirmation or required decisions when specified;
- verify success, error, confirmation, timeout, and follow-up states when they are in scope.

An alert is not complete because it is drawn. Its trigger, message state, primary/secondary actions, dismissal, and final outcome must match the approved flow.

## 6. Component States, Variables, and Conditions

Use component variants plus `changeTo` for direct visual states. Use variables and `conditional` for flows whose result depends on previous actions or entered/simulated values.

Support only states required by the source or approved specification, such as:

- default, hover, pressed, focused, selected, and disabled;
- empty, filled, invalid, loading, success, and error;
- open and closed;
- destructive confirmation and completion.

Keep state changes attached to the component or control they visually affect. Verify that variant names and destinations still exist after design edits. Do not draw duplicate frames and call them interactive unless the required transitions are wired.

`changeTo` accepts any existing layer id without complaint, including a plain top-level frame that is not a variant at all. Such a wire saves cleanly and does nothing in playback. Before and after wiring `changeTo`, confirm through inspection that the source is an instance and the destination is a variant of the same component set.

## 7. Form and Typing Boundary

A text layer that an agent edits with `type_text` is not an editable prototype input. As of the current FigCraft command contract, no command matching native free-form runtime input is exposed.

When a user asks for a form that can be typed into:

1. Recheck `list_commands` for a current input capability.
2. If none exists, state the limitation before implementation.
3. Ask whether a simulated flow is acceptable.
4. If approved, simulate only the agreed cases using component states, text properties, variables, key triggers, and conditionals. Label the result as simulated input.
5. If real arbitrary text entry is required, do not claim the `.figcraft` prototype provides it.

Designing input states, clicking/focusing fields, validating representative values, and submitting a form can be simulated. Arbitrary text entry cannot be assumed.

## 8. Hotspot and Design Synchronization

Prefer the visible control frame as the hotspot. If a separate hotspot is necessary:

- name it `Hotspot/<purpose>`;
- place it with the corresponding control in the same screen/component hierarchy;
- match its bounds to the full target;
- do not cover unrelated controls;
- inspect it again after any layout or component change.

Before saving, detect missing destinations, stale layer IDs, duplicate or overlapping hotspots, controls wired through child text/icon layers, overlays without close paths, and unreachable required states.

## 9. Verification

Verification has three automated parts plus an explicit manual handover.

1. **Structure.** Use `inspect_document` with the relevant pages and `get_node` for deep subtrees. It reports `interactions` per layer and `flows` per page, so trigger, action type, `dest`, transition, duration, and easing are all checkable. Confirm source ids, destination ids, bounds, components, variants, and variables. Remember that `overflow` is not reported; verify a slider by the size comparison in section 3.
2. **Graph.** Walk the reported interactions and confirm every required path is reachable and has the intended back, close, success, error, or terminal route. Look for missing close paths, `changeTo` wires pointing at non-variants, controls wired through a child text or icon layer, and required states that nothing reaches.
3. **Persistence.** Save the document, then inspect again. `save_file` does not create missing folders, so make sure the target directory exists.

**Runtime playback is not automatable from this tool set.** In a headless session `proto.preview` and `proto.present` return success without producing a window, and `pointer` drives the canvas rather than the prototype player. A successful `proto.preview` call is therefore not evidence that anything works. Never convert it into a claim of runtime verification.

Report verified structure, the paths you traced, and the click-through checks the user must perform, naming each one, for example: open the overlay from the card, dismiss it by tapping outside, and drag the card row horizontally.

Report implemented interactions, simulated behavior, unsupported behavior, manual checks, and the saved `.figcraft` path.
