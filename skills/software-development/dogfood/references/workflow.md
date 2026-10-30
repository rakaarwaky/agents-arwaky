# Workflow (5-Phase Pipeline)

Shared 5-phase QA pipeline that applies to every target type. Per-target toolsets
live in `web.md`, `terminal.md`, `desktop.md`, and `mobile.md`. Shared evidence
protocol, categorize rules, and report requirements live in `general.md`.

## Phase 1: Plan

Create the output directory structure:

```
{output_dir}/
├── screenshots/       # Visual evidence (web, desktop, mobile)
├── transcripts/       # Terminal output (terminal/TUI)
├── logs/              # Console / logcat / stderr captures
└── report.md          # Final report (Phase 5)
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

## Phase 2: Explore

Per target type, follow the matching reference file. Every target type follows the
same rhythm: **act → observe → record**.

| Target type | Reference file |
|---|---|
| `web` | [web.md](web.md) — `browser_*` toolset |
| `terminal` / `tui` | [terminal.md](terminal.md) — `run_terminal_command`, `screen`/`tmux` |
| `desktop` | [desktop.md](desktop.md) — `computer_use` (cua-driver) |
| `mobile` | [mobile.md](mobile.md) — `adb` shell commands |

## Phase 3: Collect Evidence

See [general.md](general.md) for the evidence protocol (screenshot/transcript
capture, field list, classification rules).

## Phase 4: Categorize

See [general.md](general.md) for the categorize rules.

## Phase 5: Report

See [general.md](general.md) for the report requirements. Use
[../templates/dogfood-report-template.md](../templates/dogfood-report-template.md).
Save to `{output_dir}/report.md`.
