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

Create the output directory structure:

```
{output_dir}/
├── screenshots/       # Visual evidence (web, desktop, mobile)
├── transcripts/       # Terminal output (terminal/TUI)
├── logs/              # Console / logcat / stderr captures
└── report.md          # Final report (Phase 5)
```

Build the test plan based on target type and scope:

- **web** — landing page, navigation links, key user flows (sign up, login, search, checkout), forms, empty states, 404s, edge cases.
- **terminal / TUI** — `--help` output, each subcommand, invalid arguments, pipe behavior, TUI rendering at multiple terminal sizes, signal handling (SIGINT, SIGTERM), non-interactive mode (stdin closed / `</dev/null`).
- **desktop** — app launch, each menu item, toolbars, dialogs, drag-and-drop, file open/save flows, accessibility tree coverage, error dialogs.
- **mobile** — cold start, each screen, navigation (back button, in-app nav), form input, touch targets, screen rotation, permission dialogs, background/foreground transitions.

### Phase 2: Explore

Per target type, follow the matching section below. Every target type follows the same rhythm: **act → observe → record**.

#### Web

Use the `browser_*` toolset. The full workflow is in
[references/web.md](references/web.md). Summary:

1. `browser_navigate(url)` → `browser_snapshot()` → `browser_console(clear=true)`
2. `browser_vision(question=..., annotate=true)` to get element labels `[N]` → ref `@eN`
3. Interact: `browser_click(ref="@eN")`, `browser_type(ref="@eN", text=...)`
4. After every significant action: `browser_console()` — silent JS errors are high-value findings
5. Screenshot each issue found: `browser_vision(question="...", annotate=false)`

#### Terminal / TUI

1. **Run the command** and capture stdout + stderr:
   ```
   run_terminal_command(command="<cmd> 2> err.log; echo \"exit:$?\"", block_until_ms=30000)
   ```
   Record the exit code, stdout, and stderr separately.

2. **Test the help surface:**
   ```
   <cmd> --help
   <cmd> --version
   ```
   Check that exit code is 0, help text is complete, and version string is present.

3. **Test each subcommand** with valid and invalid arguments. Capture exit codes and stderr for every failure.

4. **Test pipe behavior:**
   ```
   <cmd> | grep -q .   # non-empty output on success
   echo "" | <cmd>     # empty stdin
   <cmd> </dev/null    # closed stdin
   ```

5. **TUI-specific** — run inside `screen` or `tmux` to capture terminal state:
   ```
   screen -dmS qa <cmd>
   sleep 2 && screen -S qa hardcopy /tmp/qa-tui.txt
   screen -S qa -X quit
   ```
   Check: does the TUI render correctly at the default size? Does it crash if the terminal is resized? Does `SIGINT` (`kill -INT`) exit cleanly?

6. **Signal handling** — start the process in the background, send `SIGINT`, check that it exits (not hangs) and that exit code is 130.

#### Desktop

Use `computer_use` (cua-driver) — see the [computer-use skill](../../automation/computer-use/SKILL.md) for the full toolset. Summary:

1. **Capture the app state** — `computer_use(action="capture", mode="som", app="<App Name>")`
   Returns a screenshot with numbered overlays plus the AX-tree index.
2. **Interact by element index** — `computer_use(action="click", element=N, capture_after=true)`
3. **Type into fields** — `computer_use(action="type", text="...")`
4. **Test keybindings** — `computer_use(action="key", keys="<ctrl+n>")`
5. **After each state-changing action, re-capture** to verify the result.

Record the AX-tree index alongside every screenshot. A crash or missing element is evidenced by the AX index, not just the screenshot.

#### Mobile (Android)

Prerequisite: an AOSP/Android emulator is booted and connected via `adb`. The
[android-emulator-linux-gps skill](../../automation/android-emulator-linux-gps/SKILL.md)
covers AVD setup, ABI selection, and headless operation.

1. **Verify the app is installed and launches:**
   ```bash
   adb shell pm path <package>          # confirm APK is present
   adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1
   ```
2. **Capture the accessibility tree:**
   ```bash
   adb shell uiautomator dump /sdcard/window_dump.xml
   adb pull /sdcard/window_dump.xml {output_dir}/screenshots/<n>-dump.xml
   ```
   Parse `bounds="[x1,y1][x2,y2]"` + `text=` / `content-desc=` to locate elements.
3. **Tap an element** (center of its bounds):
   ```bash
   adb shell input tap <cx> <cy>
   ```
4. **Type text:**
   ```bash
   adb shell input text "hello"
   ```
5. **Swipe (scroll, dismiss, navigate):**
   ```bash
   adb shell input swipe <startX> <startY> <endX> <endY> <duration_ms>
   ```
6. **Screencap** — save to local evidence dir:
   ```bash
   adb exec-out screencap -p > {output_dir}/screenshots/<n>.png
   ```
7. **logcat** — capture the app's runtime logs between actions:
   ```bash
   adb logcat -d --pid=$(adb shell pidof <package>) 2>&1 | tail -50
   ```
   `ANDROID_LOG_ERROR` lines and uncaught exceptions in logcat are high-value findings.

8. **Test back navigation:**
   ```bash
   adb shell input keyevent KEYCODE_BACK
   ```
   Verify the app returns to the expected screen.

9. **Rotation:**
   ```bash
   adb shell cmd display set-user-rotation 1   # 90°
   adb shell cmd display set-user-rotation 0   # reset
   ```

### Phase 3: Collect Evidence

For every issue found, regardless of target type:

1. **Capture the visual/textual evidence:**
   - web / desktop / mobile → screenshot saved to `{output_dir}/screenshots/`
   - terminal / TUI → transcript saved to `{output_dir}/transcripts/`
2. **Record the details:**
   - **Location** — URL (web), command + args (terminal), app + window + element index (desktop), device + package + screen (mobile)
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Evidence path (screenshot or transcript)
   - Runtime log lines if relevant (console errors, logcat, stderr)
3. **Classify** using [references/issue-taxonomy.md](references/issue-taxonomy.md). Severity and category are target-aware — the taxonomy has target-specific categories in addition to the shared ones.

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge the same bug manifesting in different places.
3. Assign final severity and category.
4. Sort: Critical → High → Medium → Low.
5. Count by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using [templates/dogfood-report-template.md](templates/dogfood-report-template.md).

The report must include:
1. **Executive summary** — total issue count, breakdown by severity, target type, testing scope
2. **Per-issue sections** — location, severity/category badges, description, repro steps, expected vs actual, evidence reference (`MEDIA:<screenshot_path>` for images, inline code block for transcripts), runtime log lines
3. **Summary table** — all issues, sorted by severity
4. **Testing coverage** — what was tested, what was not, any blockers
5. **Notes** — observations and recommendations specific to the target type

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
