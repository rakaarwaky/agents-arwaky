---
name: orca
description: Orca CLI agent environment: Orca-managed worktrees, folder contexts, terminals, repos, automations and cron jobs, embedded browser, artifacts, and skill sharing via the orca CLI; visible local app windows via orca computer; iOS and Android emulator control; Linear ticket work; per-workspace environment recipes; multi-agent orchestration with DAGs and decision gates. Use for $orca-cli, Orca worktree, child worktree, spawn codex/claude in a worktree, read/wait/send Orca terminal, handoff/handover/give this to another agent, Orca browser, orca artifacts, share skills, scheduled agent tasks or cron jobs, visible GUI windows, booted iOS Simulator or Android emulator, linked Linear issue, per-workspace environment recipe setup, multi-agent DAG coordination.
when-to-use: Use for any Orca CLI agent-environment task. Load references/cli.md for worktrees, terminals, repos, automations, artifacts, skill sharing, and the embedded browser; references/automations.md for scheduled agent runs and cron jobs; references/computer-use.md for visible GUI windows; references/emulator.md for a booted iOS Simulator; references/emulator-android.md for an adb-connected Android emulator or phone; references/linear.md for Linear ticket work; references/per-workspace-env.md for per-workspace environment recipes; references/orchestration.md for supervised multi-agent coordination with DAGs and decision gates.
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

## Handoff vs. supervision boundary

Full ownership handoff — "hand off", "handover", "give this to another agent", "another
worktree" — routes to [cli.md](references/cli.md) and stops after the prompt is accepted.
Supervised orchestration — the user asked to monitor, coordinate a DAG, use decision gates,
or manage ask/reply — routes to [orchestration.md](references/orchestration.md) and keeps the
original agent in control. The two are mutually exclusive.
