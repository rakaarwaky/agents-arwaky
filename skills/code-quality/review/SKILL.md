---
name: review
description: >-
  Run a reviewer subagent against your whole branch vs main, your uncommitted
  working state, a named branch, a single GitHub PR, or an entire
  Graphite/stacked-PR stack (one reviewer subagent per PR). A bare /review
  defaults to reviewing your uncommitted working state when the tree is dirty,
  or your whole branch vs main when the tree is clean. Main, local, and
  branch modes write a review file plus a summary to disk. PR and stack modes
  post the findings as a PENDING GitHub review for the user to inspect and submit
  through the UI. Use --main for an explicit clean-tree branch review, --stack
  for stacked PRs, --submit to publish immediately as COMMENT, or --approve to
  publish and approve; the default remains PENDING.
when-to-use: "Use when asked to 'review', 'code review', 'review my changes', 'review my branch', 'review this PR', 'review a stack', '/review', '/review --main', '/review --stack', '/review --submit', or '/review --approve'."
argument-hint: "[--main | --local | --branch <name> | --pr <number-or-url> | --stack <number-or-url> | <auto-detect>] [--approve | --submit]"
---

# Review Skill

You are an orchestrator that runs reviewer subagents against one of five review targets. You coordinate only — **all** review findings are authored by a subagent whose prompt is seeded with the `reviewer` persona instructions, never by the orchestrator directly.

## Persona Injection

This skill uses the **reviewer** persona.

Persona text is the Grok Build persona store (SSOT: `personas/*.toml`).

Resolve each persona name in this order:
1. `~/.grok/personas/<name>.toml` (user persona store; already linked to this repo's `personas/`)
2. `<dirname of this SKILL.md>/../../../personas/<name>.toml` (repo fallback)

For each persona:
1. Pick the first path that exists
2. Read the file with `read_file`
3. Extract the `instructions` field (the `""" ... """` body; ignore keys, `[[inputs]]`, and `[[outputs]]`)
4. Store that body as the persona instructions variable named below

Store the extracted body as `reviewer_persona_instructions`.

When launching the reviewer subagent, **prepend** the persona instructions to the prompt. Do NOT pass a `persona` parameter to `spawn_subagent` — that parameter is not supported. Instead, prefix the `description` with `[reviewer]` so the pager's subagent label renderer surfaces "Reviewer" at the top of the subagent row (see Step 2 below).

1. **Main mode** -- the committed diff of the current branch against its merge-base with the default branch (`origin/main`, or `origin/master`). The working tree must be clean.
2. **Local mode** -- uncommitted changes only (staged + unstaged + untracked).
3. **Branch mode** -- the diff between a *named* branch and its merge-base with the default base branch. Committed changes only.
4. **PR mode** -- a GitHub pull request. Findings are posted as a PENDING review for the user to inspect and submit through GitHub (default).
5. **Stack mode** -- every PR in a Graphite/stacked-PR stack, discovered from one starting PR; one reviewer subagent per PR, each posting its own review.

`--approve` and `--submit` are *modifiers*, not modes. They are valid only with PR and stack modes and are mutually exclusive. The default (no modifier) omits the `event` field so each review is created PENDING for the user to submit through the UI. `--submit` posts with `event: COMMENT` (published immediately, visible right away, no approval). `--approve` posts with `event: APPROVE` (publish + approve in one call).

The reviewer subagent is read-only with respect to source code. It must still write its review artifacts. The orchestrator never edits source either; the only artifacts produced are a review file, a summary file, and (in PR and stack modes) a GitHub review. In stack mode the per-PR subagents also post their own reviews (unlike single PR mode, where the orchestrator posts).

**Do not pass `capability_mode: read-only`.** That mode removes the `write` tool, so the reviewer cannot create `<review_file>`. Enforce source read-only behavior through the prompt.

## Invocation

The user runs one of:

| Command | Behavior |
|---|---|
| `/review` | default (local mode if the tree is dirty, main mode if it is clean) |
| `/review --main` | main mode (explicit) |
| `/review --local` | local mode (explicit) |
| `/review --branch <name>` | branch mode (explicit) |
| `/review --pr <number-or-url>` | PR mode (explicit; PENDING reviews) |
| `/review --stack <number-or-url>` | review every PR in the stack containing this PR (PENDING reviews) |
| `/review --pr <number-or-url> --submit` | review and publish immediately as COMMENT (no approval) |
| `/review --stack <number-or-url> --submit` | review + publish COMMENT on every PR in the stack |
| `/review --pr <number-or-url> --approve` | review, submit, and approve |
| `/review --stack <number-or-url> --approve` | review + submit + approve every PR in the stack |
| `/review <plain-arg>` | auto-detect; see disambiguation below |

### Argument parsing

The two-phase parse (modifier extraction, then mode resolution with the ordered deterministic rules, including auto-detect and the rejection messages) lives in [references/argument-parsing.md](references/argument-parsing.md), split out to keep this SKILL.md under ~200 lines. Summary: standalone `--approve` / `--submit` tokens are extracted first; exactly one of `--main` / `--local` / `--branch` / `--pr` / `--stack` may be given; a bare `/review` resolves to local mode on a dirty tree and main mode on a clean one; plain arguments auto-detect as PR URL, PR number, or branch name.
## Setup

Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, `id -u`, `chmod`, `jq`, `wc`, `rm -f`, `sort -u`, or write to `/tmp`. Use `run_terminal_command`.

1. Confirm cwd is a git work tree with `git rev-parse --is-inside-work-tree`. If this fails, report that cwd is not a git repository and stop.
2. Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`.
3. Find a real Python 3 interpreter. Try in order: `python`, `py -3`, `python3`. Reject any path containing `WindowsApps`. If none works, tell the user to install Python 3 and stop.
4. Run `<python> <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `scratch_dir`, and `run_id` as `REVIEW_ID`.

Validate that `REVIEW_ID` is exactly 8 hexadecimal characters. If setup failed or any required value is empty, report the error and stop.

**Inline the resolved absolute `scratch_dir` and `PYTHON`** into every later command and subagent prompt. Do not rely on shell variables surviving across `run_terminal_command` calls. Also inline the absolute `HOST_PY` path where cleanup is delegated.

Define these paths once and reuse them:

- `summary_file`: `${scratch_dir}/grok-review-summary-${REVIEW_ID}.md` (main, local, and branch modes only).
- `review_file`: `${scratch_dir}/grok-review-${REVIEW_ID}.md` (main, local, branch, and single-PR modes).
- `diff_file`: `${scratch_dir}/grok-review-diff-${REVIEW_ID}.diff` (main, local, branch, and single-PR modes).
- `files_file`: `${scratch_dir}/grok-review-files-${REVIEW_ID}.txt`.
- `pending_review_payload`: `${scratch_dir}/grok-review-pending-${REVIEW_ID}.json` (single-PR mode only).
- `prmeta_file`: `${scratch_dir}/grok-review-prmeta-${REVIEW_ID}.json` (single-PR mode only).
- `post_file` and `post_error_file`: `${scratch_dir}/grok-review-post-${REVIEW_ID}.json` and `${scratch_dir}/grok-review-post-${REVIEW_ID}.err`.

In stack mode the orchestrator does not write single-target artifacts. Each reviewer receives the absolute `scratch_dir`, `PYTHON`, and `HOST_PY` and owns per-PR paths such as `${scratch_dir}/grok-review-${REVIEW_ID}-pr<num>.diff`, `${scratch_dir}/grok-review-${REVIEW_ID}-pr<num>.md`, and `${scratch_dir}/grok-review-${REVIEW_ID}-pr<num>.json`.

Initialize state:

- `mode`: one of `main`, `local`, `branch`, `pr`, `stack`.
- `target`: branch name, PR number, or PR URL; empty in main/local mode.
- `approve` and `submit`: booleans from argument parsing, both false by default.
- `head_sha`, `base_sha`, `owner`, `repo`, `pr_number`, `pr_url`, `pr_title`: populated for PR mode.
- `changed_files`: populated during diff collection.
- `stack_prs`: stack mode only, ordered base-to-tip objects `{number, url, owner, repo, headRefName, baseRefName, title}`.

## Step 1: Resolve target & collect diff

The per-mode diff collection (Main, Local, Branch, PR, and Stack discovery, including the size gates, color-off git invocations, and stack walk algorithm) lives in [references/diff-collection-and-cleanup.md](references/diff-collection-and-cleanup.md), split out to keep this SKILL.md under ~200 lines.

Key invariants: main mode requires a clean tree; local mode collects through `COLLECT_PY` (never shell `git diff` loops); branch mode compares `MERGE_BASE..<target>`; PR mode fetches metadata plus `gh pr diff` and validates `pr_number`, `head_sha`, `base_sha`, `owner`, and `repo`; stack mode only discovers — each subagent collects its own PR diff in Step 2. After Step 1, report progress per In-Progress Reporting.
## Step 2: Launch reviewer subagent

In main, local, branch, and single-PR modes, launch a single reviewer subagent by calling `spawn_subagent` (this section). In **stack mode**, skip the single-reviewer flow and use the **Stack mode** subsection at the end of this step instead, which launches one reviewer subagent per PR in parallel. Emit the `spawn_subagent` tool call before producing any "reviewer is starting" narration; the post-launch progress message ("Review complete. Processing findings...") belongs in a later assistant message after the tool result is in hand.

`spawn_subagent` parameters:

- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[reviewer] <mode> <target-summary>"` (e.g., `"[reviewer] pr #4221"` or `"[reviewer] branch feature/foo"` or `"[reviewer] main"` or `"[reviewer] local changes"`). The `[reviewer]` prefix is parsed by the pager's subagent label renderer (see `format_subagent_label` in `xai-grok-pager`) so the subagent row shows "Reviewer" instead of the generic "General" fallback. The bracketed prefix is stripped from the displayed description.
- Do **not** pass `capability_mode`. The reviewer needs `write` for `<review_file>`; the prompt keeps it off source files.

Build the prompt with the mode-specific context. **Prepend the reviewer persona instructions** (loaded during setup) to the prompt. The single-PR prompt template (scope rules, findings format, right-side-line requirement) and the stack subagent prompt template (parallel-safety constraints, per-PR post-decision logic) live in [references/reviewer-prompts.md](references/reviewer-prompts.md), split out to keep this SKILL.md under ~200 lines.
Wait for the subagent to complete. If it fails, report the error to the user and stop.

After it completes, verify that `<review_file>` exists and is non-empty. If it does not, report the error and stop.

Save the returned `subagent_id` for the report. The reviewer is not resumed; this is a one-shot review.

Report progress: "Review complete. Processing findings..."

### Stack mode (one reviewer subagent per PR)

Spawn one reviewer subagent per `stack_prs` entry with `background: true` so all PRs are reviewed in parallel. Use `subagent_type: "general-purpose"`, `description: "[reviewer] pr #<num>"`, and prepend `reviewer_persona_instructions`. The full per-PR prompt template (parallel-safety constraints, diff collection, right-side position parsing, post-decision logic, per-PR cleanup) lives in [references/reviewer-prompts.md](references/reviewer-prompts.md#stack-subagent-one-reviewer-per-pr), split out to keep this SKILL.md under ~200 lines. **Do not pass `capability_mode: read-only`.** It removes the `write` tool needed for each per-PR review and payload; enforce read-only source behavior in the prompt instead.
After all launches, call `get_command_or_subagent_output` for all task IDs and wait for every reviewer. Record a failed subagent as ERROR for that PR and continue aggregating the rest.

## Step 3: Handle output based on mode

The post-processing differs by mode: main/local/branch mode writes a summary to disk, single-PR mode posts a review to GitHub, and stack mode aggregates the reviews its subagents already posted.

### Main / Local / Branch mode

The main/local/branch post-processing (read the review file, count issues by the severity-regex, compute color-off `--shortstat` diff stats, write the `<summary_file>` in the documented structure, print paths) lives in [references/final-report.md](references/final-report.md#mainlocalbranch-mode-details-step-3), split out to keep this SKILL.md under ~200 lines. Do NOT delete `<review_file>` or `<summary_file>` in these modes -- those files ARE the deliverable.

### PR mode
### PR mode

The GitHub PR post-processing — read the reviewer output, walk the diff for valid inline positions, build the payload, post the review, and handle errors — lives in [references/pr-post-processing.md](references/pr-post-processing.md), split out to keep this SKILL.md under ~200 lines. Follow it for single-PR mode; the default posts a PENDING review, `--submit` posts COMMENT, and `--approve` posts APPROVE.

### Stack mode

In stack mode each subagent already posted its own review in Step 2, so the orchestrator does NOT read review files, build payloads, or post anything in this step. Instead, collect the structured result each subagent reported back and aggregate:

1. For each PR in `stack_prs`, record from its subagent's report: verdict, issue counts by severity, inline-comment count, body-finding count, final state (APPROVED / COMMENTED / PENDING / NO CHANGES / NO REVIEW / ERROR), and any error text.
2. Carry these into the Final report's stack summary table (Step 5).

The orchestrator wrote no per-PR review/diff/payload files in this mode, so there is nothing for it to read or clean up beyond what each subagent already removed (see Step 4).

## Step 4: Cleanup

Per-mode cleanup asymmetry (keep vs remove per outcome, per-mode artifact lists, and the `HOST_PY cleanup` invocation) lives in [references/diff-collection-and-cleanup.md](references/diff-collection-and-cleanup.md#step-4-details-cleanup), split out to keep this SKILL.md under ~200 lines. In summary: main/local/branch keep `<review_file>` and `<summary_file>`; PR removes `<review_file>` on success or no-reviewer-output but preserves it on a failed post; each stack subagent owns its own per-PR cleanup. For every cleanup, run the resolved `<PYTHON> <HOST_PY> cleanup <paths...>` with absolute paths; missing files are allowed; do not use a shell deletion command.
## Step 5: Final report

The full final-report structure (the always-included mode + target line, files-reviewed and severity-count items, and the per-mode output blocks including the stack summary table and state definitions) lives in [references/final-report.md](references/final-report.md), split out to keep this SKILL.md under ~200 lines. Summary: item 1 (mode + target) and item 4 (mode-specific output) are always included; items 2-3 are omitted on empty-diff exits; in stack mode items 2-3 are subsumed by the per-PR table.
## In-Progress Reporting

Status-update phrasing after each phase (diff collection, reviewer completion, post-outcome, stack per-PR results) is in [references/in-progress-reporting.md](references/in-progress-reporting.md).

## Rules

- **Reviewer is read-only** -- the reviewer subagent must never modify source files (it only writes its review/diff/payload artifacts under `scratch_dir`). The orchestrator must never modify source files either. The only writes are to `<review_file>`, `<summary_file>`, `<diff_file>`, `<pending_review_payload>`, the per-PR artifacts under `scratch_dir` in stack mode, and the GitHub review (PENDING by default; COMMENT with `--submit`; APPROVED with `--approve`).
- **Inject the reviewer persona into the prompt** -- always prepend the `reviewer` persona instructions (from `personas/reviewer.toml`) to the subagent prompt. Do NOT pass a `persona` parameter to `spawn_subagent`.
- **Prefix `description` with `[reviewer]`** -- the pager's subagent label renderer parses the first `[tag]` of the description and uses it as the row label (the bracketed prefix is stripped from the displayed description). Without it, the row falls through to the generic "General" label because `subagent_type` is `general-purpose` and no persona/role is plumbed through the spawn args.
- **Include context in the reviewer prompt** -- the reviewer needs the conversation context (the user's framing, any constraints, etc.) passed through the task prompt.
- **One reviewer per PR** -- main, local, branch, and single-PR modes run exactly one reviewer. Stack mode runs one reviewer per PR in the stack, in parallel. Multi-reviewer runs during an implement-fix loop are `/implement --effort N`.
- **Disambiguation is deterministic** -- the auto-detect rules in argument parsing are applied in order. Do not second-guess them. If the rules do not match, ask the user; do not guess.
- **Empty diffs short-circuit** -- never launch the reviewer with an empty diff. Report "no changes", run cleanup, and produce a Final report (using the appropriate "empty-diff exit" bullet). An empty-diff PR is never auto-approved, even with `--approve` (no changes to review = nothing to approve). In stack mode the orchestrator cannot pre-check diffs, so each subagent short-circuits its own empty-diff PR (posts nothing, reports NO CHANGES).
- **Zero issues short-circuits PR mode (unless approving)** -- if the reviewer finds nothing on a PR and `--approve` was NOT passed, do not post an empty review (PENDING or COMMENT); print a "no issues found" message, clean up, and stop. If `--approve` WAS passed, still post an APPROVE review with empty `comments` and a body summary so the approval happens. Each stack subagent applies this same rule to its own PR (reporting NO REVIEW when it skips the post).
- **PR and stack modes require `gh` auth** -- if `gh auth status` fails, stop with a clear instruction to run `gh auth login`. Do not try to work around it.
- **PENDING reviews are the default; `--submit` and `--approve` opt in to published events** -- by default the review payload omits the `event` field, so the review lands in PENDING state and the user submits it via the GitHub UI (print the Files-tab URL plus the submit-via-UI reminder). `--submit` posts with `event: COMMENT` (publish immediately, no approval). `--approve` posts with `event: APPROVE` (publish + approve). In single-PR mode the orchestrator sets the event; in stack mode each subagent sets it (and MUST receive both `<approve>` and `<submit>` substitutions -- never leave either placeholder unsubstituted).
- **Git diffs must disable color** -- every `git diff` (including `--name-only`, `--shortstat`, `--no-index`) MUST run with `-c color.ui=false -c color.diff=false` (or equivalent `NO_COLOR=1`). Colored diffs break agent parsers and cause retries.
- **Filter inline comments to lines actually in the diff** -- GitHub returns 422 for comments on lines outside the diff. The orchestrator (single-PR mode) or each subagent (stack mode) parses the diff itself to validate `(file, line)` pairs and promotes any out-of-diff issues to the top-level body as bullet points.
- **Stack mode is read-only and parallel-safe** -- stack subagents share one working tree, so they must run only read-only git/gh commands (never checkout/switch/reset/stash/`gh pr checkout`/`git fetch ...:branch`) and write only under the resolved `scratch_dir` using per-PR-unique filenames that embed BOTH the `REVIEW_ID` and the PR number. Each subagent reads post-change file content via `gh api .../contents?ref=<headSha>` rather than checking out the branch, and removes its own temp files when done.
- **`--approve` forbids self-approval** -- GitHub rejects approving your own PR. Single-PR mode and every stack reviewer compare the PR author with the authenticated user before posting. On a match, do not post, surface the cause, and preserve the review artifacts.
- **`--approve` and `--submit` are PR-only and mutually exclusive** -- both modifiers are valid only with `--pr` and `--stack`; combining either with main, local, or branch mode (including an auto-detected branch) is rejected during argument parsing. Passing both together is rejected with `--approve and --submit are mutually exclusive.`
- **Error handling** -- if the reviewer subagent fails, the diff collection fails, or the GitHub API call fails, report the error to the user and stop. Do not silently continue with missing results. EXCEPTION (stack mode): a single per-PR subagent failure does NOT abort the run -- record it against that PR, show it as `ERROR` in the stack table, and keep aggregating the other PRs (per Step 2 Stack mode).
- **No emojis in output** -- match the conventions of the `reviewer` persona instructions and the surrounding skills.

## Design notes

> Rationale for the non-obvious choices (bare-`/review` default, PENDING-vs-`--submit`, color-off diffs, stack-subagent parallelism, host-helper ownership) is in [references/rules-and-design.md](references/rules-and-design.md).
