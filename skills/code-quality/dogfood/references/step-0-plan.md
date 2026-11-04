# Step 0 — Plan

Create the output directory structure:

```text
{output_dir}/
├── screenshots/       # Visual evidence (web, desktop, mobile)
├── transcripts/       # Terminal output (terminal/TUI)
├── logs/              # Console / logcat / stderr captures
└── report.md          # Final report (step 4)
```

Build the test plan based on target type:

- **web** — landing page, navigation links, key user flows (sign up, login,
  search, checkout), forms, empty states, 404s, edge cases.
- **terminal / TUI** — `--help` output, each subcommand, invalid arguments,
  pipe behavior, TUI rendering at multiple terminal sizes, signal handling
  (SIGINT, SIGTERM), non-interactive mode (stdin closed / `</dev/null`).
- **desktop** — app launch, each menu item, toolbars, dialogs, drag-and-drop,
  file open/save flows, accessibility tree coverage, error dialogs.
- **mobile** — cold start, each screen, navigation (back button, in-app nav),
  form input, touch targets, screen rotation, permission dialogs,
  background/foreground transitions.

Shared QA rules, evidence protocol, categorize rules, report requirements, and
the issue taxonomy live in [`shared.md`](shared.md).

## Completion

- The output directory layout exists under `{output_dir}` and the per-target
  test-plan items are listed for the selected target type.
