---
name: dogfood
description: "Exploratory QA for web, terminal/TUI, desktop GUI, and mobile (Android) apps — finds bugs, captures evidence, and produces a structured report across all four target types."
when-to-use: "Use when doing exploratory QA of any application surface — web (navigate, interact, screenshot, console errors), terminal or TUI apps (command execution, exit codes, output capture), desktop GUI apps (click, type, accessibility tree, screenshot), or Android apps on an emulator (adb taps, swipes, logcat, screencap). Produces a structured bug report with per-issue evidence."
argument-hint: "<target> [--type web|terminal|desktop|mobile] [--scope <scope>] [--output-dir <dir>]"
---

# Dogfood — Exploratory QA

Runs one 5-phase pipeline — plan → explore → collect evidence → categorize → report — over any of four target types: `web`, `terminal`/`tui`, `desktop`, `mobile`. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

## Global Rules

The lane is determined from a physical signal, not by self-identification. Each agent's launcher stamps a fixed attribution env var into every command it runs; the model cannot set these.

```bash
if [[ -n "${HERMES_AGENT:-}" ]]; then echo HERMES
elif [[ -n "${GROK_AGENT:-}" ]]; then echo GROK
else echo UNSET; fi
```

- `HERMES` → **Hermes lane.** Read `references/hermes/`. Stop.
- `GROK` → **Grok lane.** Read `references/grok/`. Stop.
- `UNSET` → stop and report. Do not guess the lane.

Marker provenance:

- **Hermes** re-exports `AI_AGENT=hermes-agent` and `HERMES_AGENT=true` on every command.
- **Grok Build** runs with `GROK_AGENT=1`.

Read only the winning lane's references. Do not read the other lane's.

## Routing

### Hermes lane (Steps 0–3)

| Step | Reference                                                                     | Purpose                                                                                                  |
| ----: | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Infer target type; plan the brief (scope, output dir, acceptance criteria); create the Orca worktree (repo targets) or headless run (mobile); drop `/dogfood <target>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md) | Wait for Grok to finish the pipeline; read its report.md                                              |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify evidence integrity and that the app tree is unmodified; triage summary; deliver the report      |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (issues by severity, top issues, patterns, report location, worktree teardown) |

### Grok lane (5-phase pipeline, run by Grok Build)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0: plan | [`references/grok/step-0-plan.md`](references/grok/step-0-plan.md) | Output directory layout and target-specific test-plan items for all four types. |
| Step 1: explore — web | [`references/grok/step-1-web.md`](references/grok/step-1-web.md) | `browser_*` toolset, web-specific tips, web issue taxonomy. |
| Step 1: explore — terminal/TUI | [`references/grok/step-1-terminal.md`](references/grok/step-1-terminal.md) | `run_terminal_command`, `screen`/`tmux` capture, TUI sizing, signal handling, terminal issue taxonomy. |
| Step 1: explore — desktop | [`references/grok/step-1-desktop.md`](references/grok/step-1-desktop.md) | `computer_use` (cua-driver), AX-tree capture, drag-and-drop, desktop issue taxonomy. |
| Step 1: explore — mobile | [`references/grok/step-1-mobile.md`](references/grok/step-1-mobile.md) | `adb` shell (tap, swipe, type, screencap), `logcat`, rotation, permission dialogs, mobile issue taxonomy. |
| Shared QA rules | [`references/grok/shared.md`](references/grok/shared.md) | Output directory layout, evidence protocol, categorize rules, report requirements, issue taxonomy (severity + universal categories), shared tips for all targets. |
| Report template | [`templates/dogfood-report-template.md`](templates/dogfood-report-template.md) | Copy-source shape of the final report; fill and save to `{output_dir}/report.md`. |
