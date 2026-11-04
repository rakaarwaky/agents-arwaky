---
name: dogfood
description: "Exploratory QA for web, terminal/TUI, desktop GUI, and mobile (Android) apps — finds bugs, captures evidence, and produces a structured report across all four target types."
when-to-use: "Use when doing exploratory QA of any application surface — web (navigate, interact, screenshot, console errors), terminal or TUI apps (command execution, exit codes, output capture), desktop GUI apps (click, type, accessibility tree, screenshot), or Android apps on an emulator (adb taps, swipes, logcat, screencap). Produces a structured bug report with per-issue evidence."
argument-hint: "<target> [--type web|terminal|desktop|mobile] [--scope <scope>] [--output-dir <dir>]"
---

# Dogfood — Exploratory QA

Runs one 5-phase pipeline — plan → explore → collect evidence → categorize → report — over any of four target types: `web`, `terminal`/`tui`, `desktop`, `mobile`. The phases and their shared rules never change; only the toolset, evidence format, and category vocabulary change per target.

**All exploration is delegated to Grok Build.** The 5-phase pipeline is the Grok lane — Grok runs it inside one Orca worktree (repo targets) or headless (mobile / no-repo targets). Hermes's lane is four steps: plan the brief, drop `/dogfood <target>` into Grok, wait, verify + triage. Hermes never explores the target itself.

## Global rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build)**: You never run the act → observe → record loop, capture evidence, or write the report yourself. One Orca worktree with `--agent grok` (repo targets) or a headless `grok -p` run (mobile / no-repo targets); Grok Build runs the entire pipeline. No `spawn_subagent` for QA — your only "subagent" is the Grok Build TUI.
- **One-shot task drop**: You send exactly one message to Grok: `/dogfood <target> --type <type> --scope <scope> --output-dir <dir>` plus the brief's constraints and acceptance criteria. No mid-run course corrections, no "any bugs yet?".
- **Single point of control**: You own the surviving git and delivery operations. Grok works inside `cwd: <worktree_path>` (or headless `--cwd`); it never modifies the app under test, never commits app source, never pushes or opens a PR (you verify and deliver in Step 2).
- **Target inference**: when `--type` is omitted, infer from the target value — a URL is `web`, a command or TUI binary is `terminal`, an app name is `desktop`, an APK or Android package name is `mobile`. State the inferred type in the brief so Grok picks the right step-1 variant.
- **Evidence re-verification.** Grok's report is self-reported. Step 2 spot-checks that cited evidence files exist and flags unverifiable issues — you do not re-explore the target.
- **Parallel-First for Hermes's own work**: when you need to read multiple report sections or verify multiple evidence files, batch them in one tool call. Serialize only true dependencies.
- **Exit condition for Hermes**: Grok's `{output_dir}/report.md` exists and is complete per the template; your Step 2 evidence spot-check passes (or flags what it can't verify). Then you triage and report.

## Routing

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree (or a headless `grok -p` session), having just received `/dogfood <target>`. Run the 5-phase pipeline in `references/grok/` (step 0 plan, step 1 explore per target type, shared rules, report template).

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
