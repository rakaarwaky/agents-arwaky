---
name: dogfood
description: Exploratory QA for web apps, terminal/TUI apps, desktop GUI apps, and mobile (Android) apps. Finds bugs, captures evidence, and produces a structured report across all four target types.
when-to-use: "Use when doing exploratory QA of any application surface — web (navigate, interact, screenshot, console errors), terminal or TUI apps (command execution, exit codes, output capture), desktop GUI apps (click, type, accessibility tree, screenshot), or Android apps on an emulator (adb taps, swipes, logcat, screencap). Produces a structured bug report with per-issue evidence."
argument-hint: "<target> [--type web|terminal|desktop|mobile] [--scope <scope>] [--output-dir <dir>]"
version: 2.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, terminal, tui, desktop, gui, mobile, android, adb, dogfood]
    related_skills:
      - computer-use
      - android-emulator-linux-gps
---

# Dogfood: General Application QA Testing

Systematic exploratory QA across four target types: **web**, **terminal/TUI**, **desktop GUI**, and **mobile (Android)**. The workflow is the same 5-phase pipeline for every target; only the toolset, evidence format, and category vocabulary change per target.

## Target Types and Toolsets

| Target type | Entry point | Primary toolset | Evidence format |
|---|---|---|---|
| `web` | URL | `browser_*` tools | Screenshot (`MEDIA:` path), console log, DOM snapshot |
| `terminal` / `tui` | Command or TUI app | `run_terminal_command`, `screen`/`tmux` for capture | Transcript, exit code, stderr |
| `desktop` | App name or window | `computer_use` (cua-driver) | Screenshot, AX-tree index, action verdict |
| `mobile` | APK + package name | `adb shell` (tap, swipe, type, screencap), `logcat` | Screenshot (`.png` via `adb exec-out`), logcat lines |

**Default:** if `--type` is omitted, infer from the target value — a URL is `web`, a command or TUI binary is `terminal`, an app name is `desktop`, an APK or Android package name is `mobile`.

## Inputs

1. **Target** — URL (web), command (terminal/TUI), app name (desktop), APK path + package name (mobile).
2. **Type** — one of `web`, `terminal`, `desktop`, `mobile`. Inferred from the target if omitted.
3. **Scope** — which features or flows to focus on, or `full` for comprehensive testing.
4. **Output directory** (optional) — default `./dogfood-output`.

## Workflow

### Phase 1: Plan

See [references/workflow.md](references/workflow.md) for the output directory
layout and target-specific test-plan items.

### Phase 2: Explore

Per target type, follow the matching reference file. Every target type follows the
same rhythm: **act → observe → record**.

| Target type | Reference file |
|---|---|
| `web` | [references/web.md](references/web.md) — `browser_*` toolset |
| `terminal` / `tui` | [references/terminal.md](references/terminal.md) — `run_terminal_command`, `screen`/`tmux` |
| `desktop` | [references/desktop.md](references/desktop.md) — `computer_use` (cua-driver) |
| `mobile` | [references/mobile.md](references/mobile.md) — `adb` shell commands |

Shared pipeline lives in [references/workflow.md](references/workflow.md).
Shared evidence protocol, categorize, and report rules live in
[references/general.md](references/general.md). Issue categories are documented
in each per-target reference file (web/terminal/desktop/mobile).

### Phase 3: Collect Evidence

See [references/workflow.md](references/workflow.md) (phase overview) and
[references/general.md](references/general.md) (evidence protocol).

### Phase 4: Categorize

See [references/general.md](references/general.md) for the categorize rules.

### Phase 5: Report

See [references/general.md](references/general.md) for the report requirements.
Use [templates/dogfood-report-template.md](templates/dogfood-report-template.md).
Save to `{output_dir}/report.md`.

## Tips

**All targets**
- Always capture evidence *before* moving on to the next step — state is gone once you leave.
- Test with both valid and invalid inputs — validation bugs are the most common findings.
- Test edge cases: empty inputs, very long inputs, special characters, rapid repeated actions.

**Web**
- Check `browser_console()` after every navigation and significant interaction.
- Use `annotate=true` with `browser_vision` when element refs from the snapshot are unclear.
- Scroll long pages — content below the fold may have rendering issues.

**Terminal / TUI**
- Test the TUI at at least two terminal sizes (narrow: 80 cols, wide: 200+ cols) to catch layout breakage.
- `SIGINT` must exit the process, not leave it hung — kill -INT and check the process is gone within 1 second.
- Non-interactive mode (`</dev/null` stdin) must not hang indefinitely.

**Desktop**
- Always capture the AX-tree alongside the screenshot — a crash is evidenced by a missing or truncated AX index.
- Test drag-and-drop flows, not just click flows.
- Check what happens when the app is left idle for a while (background timers, auto-save).

**Mobile**
- Test cold start separately from warm start (kill the app, re-launch).
- Verify permission dialogs are handled — granting vs denying each permission path.
- Rotate the screen on key flows — layout breakage in landscape is a common finding.
- `logcat` uncaught exceptions are Critical severity by default.
