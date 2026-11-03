---
name: review
description: >-
  Review a module, crate, or package in place with parallel reviewer subagents
  seeded with one of 10 lens personas. A bare /review on a path runs all 10
  personas in parallel; select a single persona with its flag (e.g.
  /review modules/skills --qa-engineer) or any combination of flags;
  /review on a path with --all is equivalent to the bare form. Each reviewer
  subagent reads the module's current files (no diff collection) and writes a
  per-persona review file to the host scratch directory. The orchestrator
  aggregates per-persona issue counts and writes a module summary file to disk.
when-to-use: "Use when asked to 'review a module', 'review this package', 'review this crate', 'review modules/skills', 'review with a persona', 'review this code from the QA perspective', 'run a security review on this folder', '/review', or when the user drops a directory path and wants a code review rather than a PR or diff review."
argument-hint: "<path> [--backend-engineer | --business-analyst | --devops-engineer | --frontend-engineer | --product-engineer | --qa-engineer | --security-engineer | --software-architect | --system-analyst | --ui-ux-designer | --all]"
# Review Skill

You are an orchestrator that runs reviewer subagents in parallel against a
module, crate, or package path. Each subagent is seeded with one lens persona's
instructions, reviews the module's current source files, and writes a per-persona
review file to the host scratch directory. You coordinate only — all findings
are authored by the subagents, never by the orchestrator directly.

## Personas

This skill uses **10 lens personas**. The persona roster and the per-persona
flag name live in [references/argument-parsing.md](references/argument-parsing.md#persona-roster).

Persona text is the Grok Build persona store (SSOT: `personas/*.toml`).

Resolve each persona name in this order:
1. `~/.grok/personas/<name>.toml` (user persona store; already linked to this repo's `personas/`)
2. `<dirname of this SKILL.md>/../../../personas/<name>.toml` (repo fallback)

For each selected persona:
1. Pick the first path that exists
2. Read the file with `read_file`
3. Parse with `python3 -c "import tomllib,sys; print(tomllib.load(open(sys.argv[1],'rb'))['subagents']['personas']['<name>']['instructions'])" <path>` and take the `instructions` value under the `[subagents.personas.<name>]` table (ignore the `[[subagents.personas.<name>.inputs]]` and `[[...outputs]]` arrays)
4. Store that body as `<name>_persona_instructions`

When launching each reviewer subagent, **prepend** that persona's instructions to the prompt. Do NOT pass a `persona` parameter to `spawn_subagent` — that parameter is not supported. Prefix the `description` with `[<persona-name>]` so the pager's subagent label renderer surfaces the persona name at the top of the subagent row.

**Parallel fan-out.** Spawn one subagent per selected persona with `background: true`, wait on all task IDs via `get_command_or_subagent_output`, then aggregate.

- **All 10 personas** when no persona flag is given (the bare form), or when `--all` is given.
- **Exactly the selected personas** when one or more persona flags are given.

## Invocation

| Command | Behavior |
|---|---|
| `/review modules/skills` | review that module with all 10 personas in parallel |
| `/review modules/skills --all` | same as above (explicit) |
| `/review modules/skills --qa-engineer` | that module with only the QA Engineer persona |
| `/review modules/skills --qa-engineer --security-engineer` | that module with both the QA Engineer and Security Engineer personas |
| `/review internal/lint-arwaky --software-architect` | a specific crate with one persona |

Argument parsing (the persona roster, the `--all` handling, and the rejection
messages) lives in [references/argument-parsing.md](references/argument-parsing.md), split out to keep this SKILL.md under ~200 lines.

## Setup

Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, `id -u`, `chmod`, `jq`, `wc`, `rm -f`, `sort -u`, or write to `/tmp`. Use `run_terminal_command`.

1. Confirm cwd is a git work tree with `git rev-parse --is-inside-work-tree`. If this fails, report that cwd is not a git repository and stop.
2. Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`.
3. Find a real Python 3 interpreter. Try in order: `python`, `py -3`, `python3`. Reject any path containing `WindowsApps`. If none works, tell the user to install Python 3 and stop.
4. Run `<python> <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `scratch_dir`, and `run_id` as `REVIEW_ID`.

Validate that `REVIEW_ID` is exactly 8 hexadecimal characters. If setup failed or any required value is empty, report the error and stop.

**Inline the resolved absolute `scratch_dir` and `PYTHON`** into every later command and subagent prompt. Do not rely on shell variables surviving across `run_terminal_command` calls. Also inline the absolute `HOST_PY` path where cleanup is delegated.

Define these paths once and reuse them:

- `review_file_<persona>`: `${scratch_dir}/grok-review-<REVIEW_ID>-<persona>.md` — one per selected persona.
- `files_file`: `${scratch_dir}/grok-review-files-<REVIEW_ID>.txt` — the module's tracked file list.
- `summary_file`: `${scratch_dir}/grok-review-summary-<REVIEW_ID>.md`.

State initialized here and used throughout:

- `mode`: always `module`.
- `target`: the resolved absolute module path.
- `personas`: the ordered list of selected persona names (from the flags, or all 10 when the bare form / `--all` is used).

## Step 1: Collect the module's file list

Run `git -c color.ui=false -c color.diff=false -c core.quotepath=false ls-files <target>` and persist its stdout to `<files_file>`. Inline the absolute `target` and `files_file` paths.

If `<files_file>` is empty or whitespace-only, print "No tracked files under `<target>`. Nothing to review." and stop — run cleanup and use the empty-diff Final report.

Otherwise read `changed_files` (here: the module's tracked file list) from `<files_file>` and report progress per In-Progress Reporting.

## Step 2: Launch reviewer subagents in parallel

Spawn one reviewer subagent per entry in `personas`, all with `background: true`, all with `subagent_type: "general-purpose"`. Each subagent's `description` is `[<persona-name>] module <target>`. Prepend that persona's instructions to the prompt (see the Persona Injection section above).

The full per-persona prompt template (module-scope rules, parallel-safety constraints, per-persona file naming, and the reporting contract) lives in [references/reviewer-prompts.md](references/reviewer-prompts.md), split out to keep this SKILL.md under ~200 lines.

**Do not pass `capability_mode: read-only`.** It removes the `write` tool that each subagent needs to write its per-persona review file. Enforce source read-only behavior in the prompt instead.

After all launches, call `get_command_or_subagent_output` for all task IDs and wait for every subagent. Record a failed subagent as `ERROR` for that persona and continue aggregating the rest — one failed persona does not abort the run.

Report progress: "All <N> reviewers complete. Aggregating findings..."

## Step 3: Aggregate

The aggregation (read every per-persona review file, count issues by the severity regex, handle a missing or empty per-persona file as `ERROR`, and write the summary) lives in [references/final-report.md](references/final-report.md#step-3-details-aggregation), split out to keep this SKILL.md under ~200 lines.

- Read each `<review_file_<persona>>` via `read_file`.
- Count issues by matching heading lines against `^### Issue \d+ -- Severity: (bug|suggestion|nit)$` and bucket by the captured severity.
- If a per-persona file is missing, empty, or contains no valid issue headings, record that persona as `ERROR` (with the exact subagent error text, if any) and continue with the others.
- Compute aggregate totals across all personas.
- Write `<summary_file>` with the documented structure (per-persona table plus a totals line).
- Do NOT delete the per-persona review files or the summary file — those files ARE the deliverable.

## Step 4: Cleanup

Cleanup rules (what to keep, what to remove, and the `HOST_PY cleanup` invocation) live in [references/final-report.md](references/final-report.md#step-4-details-cleanup), split out to keep this SKILL.md under ~200 lines.

In summary: keep every `<review_file_<persona>>` and `<summary_file>`. Remove only `<files_file>`. For the removal, run the resolved `<PYTHON> <HOST_PY> cleanup <files_file>` with the absolute path. Missing files are allowed. Do not use a shell deletion command.

## Step 5: Final report

The full final-report structure (the always-included mode + target line, the per-persona table, and the totals line) lives in [references/final-report.md](references/final-report.md), split out to keep this SKILL.md under ~200 lines.

## In-Progress Reporting

Status-update phrasing after each phase lives in [references/in-progress-reporting.md](references/in-progress-reporting.md).

## Rules

- **Reviewers are read-only** — each reviewer subagent must never modify source files (it only writes its per-persona review file under `scratch_dir`). The orchestrator must never modify source files either.
- **Inject the persona into the prompt** — always prepend the selected persona's instructions (from `personas/<name>.toml`) to that subagent's prompt. Do NOT pass a `persona` parameter to `spawn_subagent`.
- **Prefix `description` with `[<persona-name>]`** — the pager's subagent label renderer parses the first `[tag]` of the description and uses it as the row label. Without it, the row falls through to the generic "General" label because `subagent_type` is `general-purpose` and no persona/role is plumbed through the spawn args.
- **Include module context in every prompt** — the subagent needs the absolute module path, the file list, the `REVIEW_ID`, and the absolute scratch directory inlined, because subagent shell variables do not survive across `run_terminal_command` calls.
- **Parallel fan-out is the execution model** — all selected subagents run in parallel. A failed or timed-out subagent records `ERROR` for that persona and the rest of the run continues.
- **No git checkout or worktree mutation in subagents** — module reviewers share one working tree, so they must run only read-only git commands (no `checkout`, `switch`, `reset`, `stash`, `fetch`) and write only under the resolved scratch directory.
- **One module, one run** — the path is a single module, crate, or package directory. Subdirectories of that path are all in scope; paths outside it are not.
- **Git ls-files must disable color** — every `git` invocation in this skill MUST run with `-c color.ui=false -c color.diff=false` (or equivalent `NO_COLOR=1`).
- **Error handling** — if the file-list collection fails, report the error to the user and stop. A single failed persona subagent does not abort the run; record `ERROR` for that persona and aggregate the rest.
- **No emojis in output** — match the conventions of the persona instructions and the surrounding skills.

## Design notes

> Rationale for the non-obvious choices (parallel fan-out, per-persona file naming, ERROR-not-abort, and why module mode does not collect a diff) is in [references/rules-and-design.md](references/rules-and-design.md).
