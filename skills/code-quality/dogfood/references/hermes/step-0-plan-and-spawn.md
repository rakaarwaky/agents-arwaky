# Step 0: Plan the Task & Spawn Grok Build

Hermes never writes code. This run has exactly one subagent — the Grok Build TUI in a dedicated Orca worktree. Plan the brief, create the worktree, drop the task, stop.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — run the exploratory QA pipeline over `<target>`: plan → explore → collect evidence → categorize → report.
2. **Target type** — infer if `--type` is omitted: a URL is `web`, a command or TUI binary is `terminal`, an app name is `desktop`, an APK or Android package name is `mobile`. State the inferred type explicitly in the brief so Grok picks the right step-1 variant.
3. **Scope** — `--scope` (feature/flow names, or `full`). If omitted, tell Grok to use `full`.
4. **Output directory** — `--output-dir` (default `./dogfood-output` inside the worktree).
5. **Constraints** — per-target toolset from the matching `grok/` reference (browser tools for web, terminal capture for TUI, cua-driver for desktop, adb for mobile); evidence-before-move; capture screenshots/transcripts/log lines before leaving a step.
6. **Acceptance criteria** — `{output_dir}/report.md` exists, built from `templates/dogfood-report-template.md`, with per-issue evidence (file paths, screenshots, log excerpts) and severity categorization; every issue has a reproducible evidence trail.
7. **Deliverable** — the report file in the worktree. Do NOT modify the app under test, do NOT fix found bugs, do NOT commit the app source. Do NOT push or open a PR.

## Create the Orca Worktree

For `web`/`terminal`/`desktop` targets that live in a repo, resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo, create:

```
"$ORCA" worktree create --repo path:<repo_path> --name dogfood-<target-slug> --agent grok --no-parent --surface terminal --json
```

For `mobile` targets or ad-hoc exploration with no repo (a raw APK / external app), skip the worktree and run Grok headless instead:

```
grok -p "/dogfood <target> --type mobile ...<brief>" --cwd <workdir> --always-approve
```

Parse JSON (worktree case): `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).

- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone for repo targets.

## Drop the Task

For the worktree case, send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/dogfood <target> --type <type> --scope <scope> --output-dir <output-dir>

<constraints and acceptance criteria from the brief>
```

Confirm `accepted: true`. **After this send, do not send any more text to Grok.**

## Report & Stop

> Dropped /dogfood into Grok Build at <worktree_path> (target: <target>, type: <type>, scope: <scope>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (or the headless `grok -p` call returns), proceed to Step 1.
