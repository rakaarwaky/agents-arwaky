---
name: orca-computer-use
description: Drive a visible local app window through `orca computer` — accessibility tree, clicks, typing, menus, dialogs, and screenshots in native apps and external browser windows (Chrome, Edge, Safari) or webviews.
when-to-use: Use when a visible window needs GUI control that a CLI, filesystem, HTTP, or existing toolchain cannot reach. Do not use for Orca's embedded browser — use `orca-cli` for that instead.
argument-hint: "get-app-state|click|type-text|set-value|press-key|hotkey|scroll|drag <app> [--element-index <n>]"
license: Apache-2.0
---

# Orca Computer Use

Drive a visible local app window through `orca computer`.

## Resolve the CLI for this session

Choose the executable once and reuse it for every later command:

- If the `ORCA_CLI_COMMAND` environment variable is set, use its value. Orca exports this for managed WSL sessions.
- Otherwise, in a dev checkout whose session exposes `ORCA_DEV_REPO_ROOT`, use `orca-dev`.
- Otherwise, on Linux outside an Orca-managed terminal, use `orca-ide`. Never run bare `orca` there — outside Orca terminals it normally resolves to the GNOME Orca screen reader (`/usr/bin/orca`).
- Otherwise, use `orca`.

Substitute `ORCA` with the resolved executable.

## Load the version-matched guide before acting

```text
ORCA skills get computer-use
```

Prefer `--json`. Use the selected executable's `--help` for commands or flags the guide does not cover. If a command reports that Orca is not running, start it with `ORCA open --json` and retry. If it fails with `runtime_access_denied`, re-run with escalated permissions; do not restart Orca. If `skills get` is unknown, use `--help` for read-only discovery and do not guess unsupported commands.

## Preconditions

- Prefer `--json`; image output only on screenshot request.
- Do not push, submit forms, send messages, buy items, delete data, change account settings, or expose secrets unless the user explicitly asked.
- If an app contains sensitive content, read only what the user requested.
- Prefer a programmatic path (shell, filesystem, git, HTTP, existing CLIs) whenever it can complete the task.

## Core Loop

```text
ORCA computer list-apps --json
ORCA computer get-app-state --app <app> --json
ORCA computer click --app <app> --element-index <n> --json
```

Read the fresh state returned by each action before choosing the next element index. Element indexes are the numeric labels in the accessibility tree; they go stale after delays, navigation, focus changes, scrolling, window changes, or app re-rendering. Never infer valid indexes from `elementCount` — read `result.snapshot.treeText` instead.

## App Selectors

Prefer bundle IDs from `list-apps`. Names are acceptable when unambiguous. Use `pid:<number>` only when bundle ID or name matching is ambiguous.

```text
ORCA computer get-app-state --app com.microsoft.edgemac --json
ORCA computer get-app-state --app Spotify --json
ORCA computer get-app-state --app pid:12345 --json
```

For apps with multiple windows, run `list-windows` first. Prefer `--window-id <id>` when the listed id is not `none`; otherwise use `--window-index <n>`. Pass the same window selector to `get-app-state` and later actions until the target window changes.

## Commands

```text
ORCA computer permissions --json
ORCA computer capabilities --json
ORCA computer list-apps --json
ORCA computer list-windows --app <app> --json
ORCA computer get-app-state --app <app> --json
ORCA computer get-app-state --app <app> --restore-window --json
ORCA computer click --app <app> --element-index <n> --json
ORCA computer click --app <app> --x 100 --y 100 --json
ORCA computer click --app <app> --x 100 --y 100 --modifiers CmdOrCtrl+Shift --json
ORCA computer click --app <app> --element-index <n> --mouse-button right --json
ORCA computer perform-secondary-action --app <app> --element-index <n> --action <name> --json
ORCA computer set-value --app <app> --element-index <n> --value "text" --json
ORCA computer type-text --app <app> --text "text" --json
ORCA computer press-key --app <app> --key Return --json
ORCA computer hotkey --app <app> --key CmdOrCtrl+A --json
ORCA computer paste-text --app <app> --text "text" --json
ORCA computer scroll --app <app> --element-index <n> --direction down --json
ORCA computer drag --app <app> --from-element-index <n> --to-element-index <n> --json
```

Use `--no-screenshot` only when pixels are not needed. Use `--text-stdin` or `--value-stdin` for sensitive text so payloads do not land in shell history.

## Action Rules

- `verified` means the changed value was read back.
- `unverified` means the call succeeded but no post-state assertion was made, or synthetic input was fired into the void.
- Never report an unverified action as success. If it could have sent, submitted, bought, or deleted something, say the effect is unproven.
- Prefer semantic actions: `set-value` for editable fields, `click` for controls, `perform-secondary-action` only for listed action names.
- After any UI-changing action, use the returned state or rerun `get-app-state` before choosing the next element index.
- Use `type-text` only after confirming the app has a focused text receiver; synthetic keyboard delivery is reported as unverified.
- Use `press-key` for single keys (Return, Escape, Tab, arrows). Use `hotkey` for one modifier chord plus one key (e.g. `CmdOrCtrl+A`).
- Use `click --modifiers <chord>` for modifier-clicks. Never synthesize separate modifier-down and modifier-up commands around a click.
- Coordinates are window-local. If a screenshot reports `scale` other than `1`, convert: `action_x = screenshot_pixel_x / scale`, `action_y = screenshot_pixel_y / scale`.

## Error Handling

- `app_not_found`: run `list-apps` and retry with the bundle ID. For web apps, select the desktop browser window containing it.
- `app_blocked`: stop; the target is intentionally blocked.
- `window_not_found` / `window_stale`: run `list-windows`, choose a current selector, rerun `get-app-state`.
- `window_not_focused`: retry once with `--restore-window`; if restore was already requested, stop retrying and check permissions.
- `element_not_found`: index is stale; run `get-app-state` again.
- `unsupported_capability`: use a semantic alternative or install the missing dependency the message names.
- `action_timeout`: inspect current state before retrying; use `--no-screenshot` if observation is slow.
- `screenshot_failed` / `accessibility_error`: run `ORCA computer permissions --json` or `--id <name>` for the specific permission.
