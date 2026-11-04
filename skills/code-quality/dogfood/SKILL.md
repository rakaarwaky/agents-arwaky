---
name: dogfood
description: "Exploratory QA for web, terminal/TUI, desktop GUI, and mobile (Android) apps — finds bugs, captures evidence, and produces a structured report across all four target types."
when-to-use: "Use when doing exploratory QA of any application surface — web (navigate, interact, screenshot, console errors), terminal or TUI apps (command execution, exit codes, output capture), desktop GUI apps (click, type, accessibility tree, screenshot), or Android apps on an emulator (adb taps, swipes, logcat, screencap). Produces a structured bug report with per-issue evidence."
argument-hint: "<target> [--type web|terminal|desktop|mobile] [--scope <scope>] [--output-dir <dir>]"
---

# Dogfood — Exploratory QA

Runs one 5-phase pipeline — plan → explore → collect evidence → categorize → report — over any of four target types: `web`, `terminal`/`tui`, `desktop`, `mobile`. The phases and their shared rules never change; only the toolset, evidence format, and category vocabulary change per target.

## Global rules

- **Target inference.** When `--type` is omitted, infer from the target value — a URL is `web`, a command or TUI binary is `terminal`, an app name is `desktop`, an APK or Android package name is `mobile`.
- **Inputs.** Target (URL / command / app name / APK + package name), optional type (four values above), scope (feature or flow names, or `full` for comprehensive testing), output directory (default `./dogfood-output`).
- **Explore rhythm.** Every target type follows the same act → observe → record loop; the per-target reference owns that type's toolset and exploration items.
- **Evidence before move.** Capture evidence (screenshot, transcript, log lines) before leaving a step — state is gone once you move on.
- **Categorize and report shared rules.** Severity levels, issue categories, evidence protocol, categorize rules, and report requirements live in [`references/shared.md`](references/shared.md); per-target issue categories live in the per-target reference.
- **Report.** Phase 5 produces `{output_dir}/report.md` from `templates/dogfood-report-template.md` with per-issue evidence and severity.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0: plan | [`references/step-0-plan.md`](references/step-0-plan.md) | Output directory layout and target-specific test-plan items for all four types. |
| Step 1: explore — web | [`references/step-1-web.md`](references/step-1-web.md) | `browser_*` toolset, web-specific tips, web issue taxonomy. |
| Step 1: explore — terminal/TUI | [`references/step-1-terminal.md`](references/step-1-terminal.md) | `run_terminal_command`, `screen`/`tmux` capture, TUI sizing, signal handling, terminal issue taxonomy. |
| Step 1: explore — desktop | [`references/step-1-desktop.md`](references/step-1-desktop.md) | `computer_use` (cua-driver), AX-tree capture, drag-and-drop, desktop issue taxonomy. |
| Step 1: explore — mobile | [`references/step-1-mobile.md`](references/step-1-mobile.md) | `adb` shell (tap, swipe, type, screencap), `logcat`, rotation, permission dialogs, mobile issue taxonomy. |
| Shared QA rules | [`references/shared.md`](references/shared.md) | Output directory layout, evidence protocol, categorize rules, report requirements, issue taxonomy (severity + universal categories), shared tips for all targets. |
| Report template | [`templates/dogfood-report-template.md`](templates/dogfood-report-template.md) | Copy-source shape of the final report; fill and save to `{output_dir}/report.md`. |
