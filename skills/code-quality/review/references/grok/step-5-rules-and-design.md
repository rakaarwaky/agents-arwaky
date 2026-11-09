# Step 5: Design notes (commit / uncommit / pr / path review)

## Why diff modes read the diff, and path mode reads the files

Diff modes (`commit`, `uncommit`, `pr`) review a change set. Each subagent receives the unified diff as the primary scope — the `+` lines are the new code, the `-` lines are the removed code. Pre-existing issues untouched by the diff are out of scope, keeping the review focused on what changed.

`path` mode reviews the current state of a file or directory in place — there is no base to diff against. Each subagent lists the files and reads them. A diff would answer "what changed"; path mode answers "is this module sound."

## Why the agent auto-selects 1–3 personas instead of a fixed roster

Running all 10 personas on every review is wasteful: most files are reviewed by a small set of lenses that actually matter. A backend-engineer lens adds little to a pure UI-component change; a security lens adds little to a docs-only diff. The orchestrator reads the diff summary (or directory tree) before launching subagents, picks the 1–3 most relevant personas, and launches only those. This cuts wall-clock time by roughly 3–5× on typical runs while keeping coverage proportional to risk.

If the signal is ambiguous (large mixed-language diff, or unclear scope), the orchestrator falls back to the 3 most general personas: backend-engineer, qa-engineer, software-architect.

## Why per-persona file names embed BOTH the REVIEW_ID and the persona

`grok-review-<REVIEW_ID>-<persona>.md` prevents collision when two reviews run in the same scratch directory (different `REVIEW_ID`), and keeps a multi-persona run from clobbering its own siblings (different persona). The `REVIEW_ID` alone is not enough; the persona name alone is not enough.

## Why ERROR-not-abort

A single persona subagent can fail (context window overflow on a very large diff, a malformed persona file, a transient subagent error). The other personas' findings are still useful and cost nothing to keep. Aborting the whole run because one lens failed would throw away the remaining reviews. The orchestrator records the failed persona as `ERROR` with the exact error text and aggregates the rest.

## Why `pr` mode uses `gh pr diff` and not `git diff`

`gh pr diff <n>` fetches the PR head directly from GitHub and shows the full diff against the base branch. It works even when the PR's head branch is not checked out locally. A local `git diff` would require the branch to be present, which is not guaranteed in a worktree.

## Why no GitHub posting

Findings land in per-persona review files plus a single summary file on disk. If the user wants the findings posted to a PR, that is a separate workflow (a `gh api` call or a dedicated posting skill) and is out of scope for this skill.
