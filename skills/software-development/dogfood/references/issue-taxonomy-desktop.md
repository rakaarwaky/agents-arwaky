# Issue Taxonomy — Desktop

Desktop-GUI-specific category detail. Shared severity levels and universal
categories live in `issue-taxonomy-general.md`.

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
