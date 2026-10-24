# Orca Automations — scheduled agent runs and cron jobs

Scheduled Orca prompt runs by a selected agent provider against either a newly
created worktree or an existing workspace.

## Load the bundled reference

```bash
ORCA skills get orca-cli --reference references/automations.md
```

## Inspect and List Automations

```bash
ORCA automations list --json
ORCA automations show <automationId> --json
ORCA automations runs --id <automationId> --json
```

## Create Automations

```bash
# Preset schedule: daily at specified time
ORCA automations create --name "Daily review" --trigger daily --time 09:00 --prompt "Review open changes" --provider codex --repo id:<repoId> --json

# Standard 5-field cron trigger
ORCA automations create --name "Weekday triage" --trigger "0 9 * * 1-5" --prompt "Triage issues" --provider claude --repo path:/abs/repo --disabled --json

# Hourly run with precheck guard (runs only if exit code is 0)
ORCA automations create --name "PR review" --trigger hourly --precheck "gh pr list --json number -q .[0].number" --prompt "Review requested PRs" --provider codex --json

# Reuse session in an existing workspace
ORCA automations create --name "Inbox digest" --trigger hourly --prompt "Summarize unread mail" --provider codex --workspace active --reuse-session --json

# Extra model and effort arguments
ORCA automations create --name "Docs pass" --trigger daily --prompt "Tidy the docs" --provider claude --extra-agent-args="--model opus --effort high --add-dir docs" --json
```

## Manage and Execute Automations

```bash
# Run immediately on demand
ORCA automations run <automationId> --json

# Edit schedule or options
ORCA automations edit <automationId> --trigger weekdays --time 09:30 --fresh-session --json

# Remove automation and run history
ORCA automations remove <automationId> --json
```

## Key Flags and Rules

- Trigger types: `hourly`, `daily`, `weekdays`, `weekly`, 5-field cron expression (e.g. `"0 9 * * 1-5"`), or RRULE strings.
- `--time <HH:MM>`: used with `daily`, `weekdays`, or `weekly` presets.
- `--day <0-6>`: used with `weekly` preset (Sunday is 0).
- `--repo <selector>` vs `--workspace <selector>`: mutually exclusive. `--repo` spins up a new isolated worktree per run; `--workspace` runs in an existing worktree.
- `--precheck <command>`: executes a shell command before the run. Exit code 0 proceeds; non-zero records a skipped run.
- `--reuse-session`: valid only for existing-workspace automations. Falls back to a fresh session if the terminal exited.
- `--extra-agent-args`: must use `=` syntax (e.g. `--extra-agent-args="--model opus --effort high"`). Supported providers include `claude`, `codex`, `codebuddy`, `cursor`, `grok`, and `omp`. Cannot combine with `--reuse-session`.
