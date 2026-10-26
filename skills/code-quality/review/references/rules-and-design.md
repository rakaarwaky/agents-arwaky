# Review rules and design notes

Background notes explaining the rationale behind the choices in the `review` skill. These are NOT rules; they are pointers for future maintainers.

## The bare `/review` default trades one previously-empty case for a useful one

Before this change a bare `/review` always meant local mode, so on a clean tree (everything committed) it reported "no changes to review" and did nothing. The default keeps local mode whenever the tree is dirty (no regression for the common mid-edit gut-check) and only switches to main mode when local mode would otherwise have been a no-op. GitHub-writing modes stay strictly opt-in: a bare `/review` never resolves to `--pr` or `--stack`, so it can never post to GitHub on its own.

## Main mode reviews the current branch tip

It is selected only when the working tree is clean and compares `MERGE_BASE..HEAD`. Local mode remains the owner of staged, unstaged, and untracked changes through `collect_local_diff.py`; named branch mode compares `MERGE_BASE..<target>`.

## Host helpers do not own review parsing

`scripts/host.py` owns portable setup and cleanup. `scripts/collect_local_diff.py` owns portable local diff collection. Review markdown parsing, unified-diff hunk walking, and GitHub payload assembly stay inline.

## Owner/repo are derived from the PR `url`, not from a `baseRepository` field

`gh pr view --json baseRepository` returns `Unknown JSON field: "baseRepository"` — only `headRepository`, `headRepositoryOwner`, and `isCrossRepository` are exposed. Parsing the URL is the simplest universal approach and works correctly for cross-repo PRs.

## The constructed `/files` URL is used for PENDING output only, not the response's `html_url`

The Files tab is where the "Finish your review" / "Submit review" button surfaces in the GitHub UI; that is what the user needs for a PENDING review. The response's `html_url` deep-links to the review object and is less useful for this workflow. When `--submit` or `--approve` is used there is no PENDING state and no submit button, so the user output reports the PR URL instead.

## Default stays PENDING; `--submit` opts into COMMENT (2026-07-27)

Changing the default would surprise users who open GitHub to iterate on draft reviews before publishing. `--submit` mirrors `--approve` as an explicit opt-in for a published event (`event: COMMENT` vs `event: APPROVE`) without flipping the default.

## Color-off on git diffs

Agents parse unified diffs as plain text; ANSI color sequences from `color.ui=always` corrupt that parse and force retries. The skill pins `-c color.ui=false -c color.diff=false` on every `git diff` invocation rather than relying on ambient config.

## Stack subagents post their own reviews; the orchestrator does not

A stack can be 8+ PRs; collecting every diff and posting every review from the orchestrator would serialize the work and bloat its context. Spawning one read-only subagent per PR parallelizes the reviews. Because they share one working tree, each subagent reads post-change content via `gh api .../contents?ref=<headSha>` instead of checking out the branch, and writes only per-PR-unique files under `scratch_dir` (REVIEW_ID + PR number) so concurrent subagents never collide.

## Stack discovery is a deterministic walk over open PRs

Rather than depend on the `gh` Graphite extension (not guaranteed installed), the skill fetches all open PRs once and walks the `baseRefName`->`headRefName` chain down to the base and up to the tip. This needs only core `gh` and degrades gracefully (a PR with no neighbors is reviewed alone; a branching stack includes all reachable descendants).

## Surface every `gh api` error verbatim

If the GitHub API call exits non-zero (422, 403, 404, 5xx, anything else), do not retry, with one exception: a stack subagent may perform the single documented fold-into-body retry on a 422 (per Step 2 Stack mode) before reporting failure. Show the user the raw stderr plus the HTTP status code so they can debug, and preserve `<review_file>` on disk so the findings are not lost.

## Helpers stay host-focused

Use `scripts/host.py` for setup and cleanup and `scripts/collect_local_diff.py` for local changes. Keep review markdown parsing and payload assembly inline.

## Cleanup is asymmetric by mode and outcome

Main/local/branch modes keep `<review_file>` and `<summary_file>` (they are the deliverable). PR mode removes `<review_file>` on a successful post (the GitHub review -- PENDING, COMMENT, or APPROVED -- is the deliverable) and on a no-reviewer-output exit (zero issues OR empty diff -- nothing actionable to preserve), but preserves it on a failed post so the user can recover the findings. In stack mode each subagent cleans up its own per-PR temp files and the orchestrator has nothing extra to remove.

## Thread the same file paths across all steps

Never regenerate paths between steps. The `REVIEW_ID` is fixed for the run.