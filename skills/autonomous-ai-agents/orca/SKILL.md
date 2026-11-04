---
name: orca
description: "Orca CLI agent environment: Orca-managed worktrees, folder contexts, terminals, repos, automations and cron jobs, embedded browser, artifacts, and skill sharing via the orca CLI; visible local app windows via orca computer; iOS and Android emulator control; Linear ticket work; per-workspace environment recipes; multi-agent orchestration with DAGs and decision gates. Use for $orca-cli, Orca worktree, child worktree, spawn codex/claude in a worktree, read/wait/send Orca terminal, handoff/handover/give this to another agent, Orca browser, orca artifacts, share skills, scheduled agent tasks or cron jobs, visible GUI windows, booted iOS Simulator or Android emulator, linked Linear issue, per-workspace environment recipe setup, multi-agent DAG coordination. Observed user phrasing: 'build the worktree in orca', 'worktree deleted from disk / recreate worktree', 'why isn't it showing in orca IDE', 'check all open PRs', 'resolve conflicts in another worktree', orca cli-commands, orca config-system."
when-to-use: "Use for any Orca CLI agent-environment task. Load references/cli.md for worktrees, terminals, repos, automations, artifacts, skill sharing, and the embedded browser; references/automations.md for scheduled agent runs and cron jobs; references/computer-use.md for visible GUI windows; references/emulator.md for a booted iOS Simulator; references/emulator-android.md for an adb-connected Android emulator or phone; references/linear.md for Linear ticket work; references/per-workspace-env.md for per-workspace environment recipes; references/orchestration.md for supervised multi-agent coordination with DAGs and decision gates. Also matches observed user phrasing: 'build the worktree in orca', 'worktree deleted from disk / recreate worktree', 'why isn't it showing in orca IDE', 'check all open PRs', 'resolve conflicts in another worktree'."
argument-hint: "open --json | skills get <skill-name> [--json] [--reference <path>] | <command> [<flags>]"
license: Apache-2.0
---

# Orca CLI Agent Environment

One consolidated skill for the Orca agent environment. Each sub-scenario is a
[reference file](references/); the shared rules live here once.

## Resolve the CLI for this session

Choose the executable once and reuse it for every later command:

- If the `ORCA_CLI_COMMAND` environment variable is set, use its value. Orca exports this
  for managed WSL sessions.
- Otherwise, in a dev checkout whose session exposes `ORCA_DEV_REPO_ROOT`, use `orca-dev`.
- Otherwise, on Linux outside an Orca-managed terminal, use `orca-ide`. Never run bare
  `orca` there — outside Orca's terminals it normally resolves to the
  GNOME Orca screen reader (`/usr/bin/orca`) and starts speech on the user's machine.
- Otherwise, use `orca`.

Below, `ORCA` is a placeholder for the executable you resolved. Substitute it before
running anything; do not create a shell variable or run `ORCA` literally. This works the
same way in POSIX shells, PowerShell, and cmd.exe.

If the selected executable cannot run, report its exact error and stop. Do not fall through
to another executable, which could silently target a different Orca build.

## Load the version-matched guide before running Orca commands

Each reference file names the guide its scenario loads. Prefer `ORCA skills get <skill-name> --json`.
Use the selected executable's `--help` for commands or flags the guide does not cover.

If a command reports that Orca is not running, start it with `ORCA open --json` and retry.
If it fails with `runtime_access_denied`, your sandbox blocked the connection: re-run it with
escalated permissions, and do not run `ORCA open` or restart Orca.
If `skills get` is unknown, explain that updating Orca restores the guide; use `--help` for
read-only discovery and do not guess unsupported commands.

## Scenario routing

| Scenario | Reference | Load guide with |
|---|---|---|
| Worktrees, folder contexts, terminals, repos, automations, artifacts, skill sharing, embedded browser | [cli.md](references/cli.md) | `ORCA skills get orca-cli` |
| Scheduled automations and cron jobs | [automations.md](references/automations.md) | `ORCA skills get orca-cli --reference references/automations.md` |
| Visible local app windows (native apps, browsers, webviews) | [computer-use.md](references/computer-use.md) | `ORCA skills get computer-use` |
| Booted iOS Simulator on macOS | [emulator.md](references/emulator.md) | `ORCA skills get orca-emulator` |
| adb-connected Android emulator or phone | [emulator-android.md](references/emulator-android.md) | `ORCA skills get orca-emulator-android` |
| Linear ticket work | [linear.md](references/linear.md) | `ORCA skills get orca-linear` |
| Per-workspace environment recipes | [per-workspace-env.md](references/per-workspace-env.md) | `ORCA skills get orca-per-workspace-env` |
| Supervised multi-agent coordination, DAGs, decision gates | [orchestration.md](references/orchestration.md) | `ORCA skills get orchestration` |
| Large briefs and long-context guidance | [large-briefs.md](references/large-briefs.md) | `ORCA skills get orca --reference references/large-briefs.md` |

## Grok Build in Orca worktrees (agent slot)

Attach Grok Build to a worktree with `orca worktree create ... --agent grok --no-parent` — the
Grok TUI runs in the worktree's first terminal (`--surface terminal`; `--surface chat` for
pure read-only analysis). Two ways to use that slot:

- **Supervised (default for /implement, /execute-plan runs)**: subagents bind to the
  worktree via `cwd`; task text is NEVER sent to the TUI (`--prompt` stays off). The TUI
  is the orchestrator's monitoring surface only. A monitoring TUI that stays idle or holds
  unmerged local changes blocks later `worktree rm --force` — kill the terminal or retire
  the worktree before assembly/teardown.
- **Full handoff**: send the brief via `orca terminal send` after
  `orca terminal wait --for tui-idle`; confirm `accepted: true`, then stop
  driving it. Hermes-style agents (Hermes orchestrating a Grok Build TUI in
  the worktree) use this mode exclusively: plan the brief, drop it once, wait
  for idle, then verify the worktree state and ship (commit/push/PR)
  themselves.

**Full-handoff pitfalls** — these cost rework when ignored:

- **`tui-idle` is not a reliable progress signal.** The terminal stream can
  stay empty (`tail: []`, 0 returned lines) while Grok is actively writing
  files and committing in the worktree. Never assume idleness from an empty
  `orca terminal read` output. Verify progress directly in the worktree
  directory: `git log --oneline -3`, `git status --short`,
  `git show --stat <head-sha>`, and `ls <expected-new-file>`.
- **`orca terminal wait` promotes past the 600s cap.** When a wait exceeds
  the foreground cap it becomes a tracked background process with
  `notify_on_complete=true` instead of being refused. Do not re-run the
  wait; poll with `process_manage(action="poll", session_id=<session_id>)`
  or wait for its completion notification.
- **After `orca terminal send` returns `accepted: true`, stop driving.**
  Grok owns the worktree from there; continued sends interleave with its
  work. Confirm acceptance, then disengage and verify via worktree state.
- **Grok can omit pieces it considers incidental.** Grok may drop functions
  or methods it thinks are "legacy" (e.g. `load_rows`, `read_catalog_text`)
  while keeping callers that need them. Always run the full test suite in
  the worktree before declaring done — not just the subset Grok mentions —
  and `git show --stat <head>` to confirm exactly which files changed.
- **Base the worktree intentionally.** `worktree create` bases on
  `origin/main` regardless of `--prompt`. For a task stacked on a sibling
  feature branch, check `git log --oneline -3` in the worktree and
  `git reset --hard <base-sha>` (or recreate) before sending the brief —
  otherwise the work conflicts or misses predecessor commits. The full
  handoff contract — including what to put in the brief, how to wait, and how
  to verify + ship after Grok finishes — is codified in the agents-arwaky repo
  skills `implement` and `execute-plan` under `references/hermes/` (their
  Hermes lane). Load those step files before running a /implement or
  /execute-plan handoff; they are the authoritative procedure for that class
  of task.

Mutually exclusive per worktree — pick one per worktree, never both. The `implement` and
`execute-plan` skills in the agents-arwaky tree use the supervised mode; their step files
are the authoritative protocol for that class of task.

- **Verify the worktree's base before dropping a brief.** `worktree create`
  bases the new branch on the remote default (`origin/main`) regardless of
  `--prompt`; for a task stacked on a sibling feature branch, check
  `git log --oneline -3` in the worktree and `git reset --hard <base-sha>`
  (or recreate) before sending the brief — otherwise the work conflicts or
  misses its predecessor's commits. `--prompt` (if used) reaches the TUI
  only as queued text; an empty TUI stream does not mean the prompt was
  never delivered — check worktree state instead.

## Handoff vs. supervision boundary

Full ownership handoff — "hand off", "handover", "give this to another agent", "another
worktree" — routes to [cli.md](references/cli.md) and stops after the prompt is accepted.
Supervised orchestration — the user asked to monitor, coordinate a DAG, use decision gates,
or manage ask/reply — routes to [orchestration.md](references/orchestration.md) and keeps the
original agent in control. The two are mutually exclusive.
