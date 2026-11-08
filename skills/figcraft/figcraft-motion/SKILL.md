---
name: figcraft-motion
description: Adds transition and animation polish to a FigCraft prototype after its flows already work, using verified transition types, easings, springs, and delayed triggers. Use as the final pass, never as a substitute for correct wiring.
---

# FigCraft Motion

Run this last. Motion polish on a broken flow hides the breakage. `figcraft-prototyper` must already have every required path wired and inspected before anything here is tuned.

Load the `figcraft` coordinator for completion rules.

## 1. What the Engine Provides

All of this lives on the interaction, not inside the action. Confirm the current contract with `list_commands` before use.

- `transition` types: `instant`, `dissolve`, `smartAnimate`, `moveIn`, `moveOut`, `push`, `slideIn`, `slideOut`, with `direction` of `left`, `right`, `top`, or `bottom`.
- `durationMs` on the interaction.
- `easing`: `linear`, `easeIn`, `easeOut`, `easeInOut`, `easeInBack`, `easeOutBack`, `easeInOutBack`, `gentle`, `quick`, `bouncy`, `slow`, or a custom `{customBezier {x1, y1, x2, y2}}` or `{customSpring {mass, stiffness, damping}}`.
- `delayMs` for mouse enter, leave, down, and up, so a hover can settle before it fires.
- An `afterDelay {ms}` trigger for timed sequences such as a splash, a toast that dismisses itself, or a staged reveal.
- `navigate` takes `preserveScroll`, which keeps a long page's scroll position across a transition.

## 2. Choose Motion From the Interaction, Not Habit

| Interaction | Transition | Duration | Easing |
|---|---|---|---|
| Tab or segment switch in place | `instant` or `dissolve` | 0–120 ms | `easeOut` |
| Forward into a detail screen | `slideIn` or `push`, direction `left` | 260–320 ms | `easeInOut` |
| Back to the previous screen | `back`, or the mirrored direction | 240–300 ms | `easeInOut` |
| Bottom sheet or modal opening | `moveIn`, direction `bottom` | 220–280 ms | `easeOut` |
| Sheet or modal closing | `moveOut`, direction `bottom` | 180–240 ms | `easeIn` |
| Element morphing between states | `smartAnimate` | 240–320 ms | `easeInOut` or `gentle` |
| Playful, child-facing confirmation | `smartAnimate` | 300–420 ms | `bouncy` or `easeOutBack` |
| Toast or alert self-dismissing | `dissolve` on `afterDelay` | 160–240 ms | `easeOut` |

Entering motion can afford to be slower than exiting motion. Exits should feel immediate. Nothing routine should exceed roughly 400 ms; past that an interface feels sluggish rather than polished.

Do not reach for `smartAnimate` by default. It earns its cost only when something genuinely continues across the two frames.

## 3. Smart Animate Pairing

`smartAnimate` pairs layers across the source and destination and animates the difference. For a pair to be found, keep the layer identical in both frames: same name, same place in the hierarchy, same type. Change only what should move, such as position, size, fill, opacity, or corner radius.

Common causes of a transition that snaps instead of animating: the layer was renamed, it sits at a different depth, it changed type, or it was rebuilt rather than duplicated. Build the second state by duplicating the first, then editing it.

Pairing behavior cannot be observed in a headless session. Treat it as a manual check and tell the user which transitions to watch.

## 4. Staged Sequences

For a celebration or onboarding beat, chain `afterDelay` interactions across intermediate frames rather than trying to stagger many elements in one transition. Keep the chain short, give the user an immediate way out, and never trap them in a timed sequence with no control.

Use `delayMs` on hover interactions so a pointer crossing a control does not trigger it.

## 5. Restraint

- Animate what communicates: hierarchy, origin, direction, state change, and progress.
- One primary motion per interaction. Competing animations read as noise.
- Keep the same journey consistent. If forward slides left, it slides left everywhere.
- Respect the design's temperament. A playful children's app can bounce; a banking confirmation should not.
- Users who need reduced motion exist. If the product has that requirement, ask whether to provide an instant or dissolve variant rather than inventing one.
- Do not add motion to elements the brief never mentioned.

## 6. Verification

1. Inspect the interactions and confirm `transition`, `durationMs`, `easing`, and any `delayMs` are stored as intended. These fields are reported by `inspect_document` and `get_node`.
2. Walk the graph and confirm forward and back motion mirror each other, and that every overlay's open and close pair are complementary.
3. Confirm no required interaction lost its action while being retimed.
4. Playback cannot be automated from this tool set. List the motion checks the user should run in preview, naming each transition, and do not call them verified.

Report the motion model you applied, the durations and easings chosen, the reasoning for anything unusual, and the pairing checks that still need a human eye.
