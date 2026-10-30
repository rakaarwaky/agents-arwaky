# Desktop Target — Toolset and Workflow

QA workflow for native desktop GUI apps using `computer_use` (cua-driver).
See the [computer-use skill](../../automation/computer-use/SKILL.md) for the full
toolset and the verify → escalate ladder.

## Prerequisites

- The target app is installed and launches.
- `computer_use` is available (cua-driver backend).

## Explore rhythm

1. **Capture the app state** — `computer_use(action="capture", mode="som",
   app="<App Name>")`
   Returns a screenshot with numbered overlays plus the AX-tree index. Record both.

2. **Interact by element index** — `computer_use(action="click", element=N,
   capture_after=true)`
   Prefer element indices over pixel coordinates.

3. **Type into fields** — `computer_use(action="type", text="...")`

4. **Test keybindings** — `computer_use(action="key", keys="<ctrl+n>")`

5. **Scroll and drag** — `computer_use(action="scroll", direction="down")`,
   `computer_use(action="drag", from_element=A, to_element=B)`

6. **After each state-changing action, re-capture** to verify the result.

7. **Evidence** — save screenshots to `{output_dir}/screenshots/`. Record the
   AX-tree index alongside every screenshot — a crash or missing element is
   evidenced by the AX index, not just the screenshot.

## Tips

- Always capture the AX-tree alongside the screenshot — a crash is evidenced by
  a missing or truncated AX index.
- Test drag-and-drop flows, not just click flows.
- Test what happens when the app is left idle (background timers, auto-save).
- Check menu items, toolbars, dialogs, and file open/save flows.
- Test error dialogs: what happens when the app is given a bad input file?
- Don't interact with the user's personal browser tabs (email, banking,
  Messages) unless that's the actual task.
# Issue Taxonomy — Desktop

Desktop-GUI-specific category detail. Shared severity levels and universal

## Visual (desktop)
- desktop app window restores at wrong size or position on relaunch
- layout misaligned or overlapping at non-default DPI / display scaling
- z-index issues: elements hidden behind others (modal dialogs, popovers)

## Console (desktop)
- uncaught exceptions in the app's runtime log
- failed network requests (4xx, 5xx) during app operation

## Accessibility (desktop)
- elements not reachable via keyboard navigation
- missing focus indicators
- screen reader incompatible content

## UX (desktop)
- app not responding to the OS (spinner cursor) during long operations
- missing confirmation dialogs for destructive actions
- no feedback after user actions (button click with no visible result)
- drag-and-drop flows broken or partially working
- file open/save flows fail or lose data

## Functional (desktop)
- menu items, toolbars, or dialogs that do nothing when activated
- keyboard shortcuts that don't fire or fire the wrong action
- app crashes on specific inputs or file types

