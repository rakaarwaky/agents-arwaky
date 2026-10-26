# Reviewer subagent prompts

## Single-PR template

Build the prompt with the mode-specific context. **Prepend the reviewer persona instructions** (loaded during setup) to the prompt. Use this template:

```
<reviewer_persona_instructions>

---

You are reviewing code changes. Mode: <mode>.

Target: <target-summary-line>
<if PR mode: PR URL: <pr_url>>
<if PR mode: head SHA: <head_sha>, base SHA: <base_sha>>
<if branch mode: base: <BASE>, merge-base: <MERGE_BASE>, head: <target>>
<if main mode: base: <BASE>, merge-base: <MERGE_BASE>, head: HEAD (clean working tree)>

The unified diff is at: <diff_file>
The list of changed files is at: <files_file>

Read the diff first to understand the scope. The diff alone is often not enough
context, so you should also `read_file` the source files referenced in the diff
to understand call sites, types, and surrounding logic before flagging issues.

Diff-review scope (overrides any conflicting persona Scope text):
- Report issues in ADDED or MODIFIED diff lines. Also flag breakages from
  deleted/renamed symbols even when call sites are outside the diff, after
  verifying those call sites.
- Do not report pre-existing problems in untouched code unless the diff newly
  depends on them in a way that will break.
- If a high-risk finding is the clearly intended, well-constrained purpose of
  the change, do not report it. Report it only if the author likely missed
  downstream impact or the change looks unconstrained/malicious.
- Flag feature-flag / internal-only gate leaks (new user-visible paths that
  skip an existing gate, or gates removed without a matching product intent).

Write your structured findings to: <review_file>

Format:

## Summary

<2 to 4 sentence overall assessment of the changes -- what they do, whether
they look correct, the dominant risk areas. This goes at the very top of the
file, before any individual issues.>

## Issues

### Issue 1 -- Severity: bug
- File: path/to/file.ext:LINE
- Description: <what is wrong>
- Suggestion: <how to fix>
- Status: open

### Issue 2 -- Severity: suggestion
- File: path/to/file.ext:LINE
- Description: ...
- Suggestion: ...
- Status: open

Severity must be one of: bug, suggestion, nit. Each issue's Status field must be set to "open" (as shown in the example above).

<if PR mode, include this paragraph verbatim:>
IMPORTANT: For each issue, the File line MUST reference a single line number on
the RIGHT side of the diff (the line number in the new/post-change file, not
the pre-change file). If a finding spans a range, pick the most representative
single line on the RIGHT side. This requirement is mandatory because the
orchestrator will post these findings as inline comments on the GitHub PR, and
the GitHub API rejects comments that do not target a line present in the diff.
<end if>

If the diff is genuinely fine and you have no issues, write the Summary and an
empty `## Issues` section (or omit the Issues section entirely). Do not invent
issues to fill space.
```


## Stack subagent (one reviewer per PR)

### Stack mode (one reviewer subagent per PR)

Spawn one reviewer subagent per `stack_prs` entry with `background: true` so all PRs are reviewed in parallel. Use `subagent_type: "general-purpose"`, `description: "[reviewer] pr #<num>"`, and prepend `reviewer_persona_instructions`.

**Do not pass `capability_mode: read-only`.** It removes the `write` tool needed for each per-PR review and payload. Enforce read-only source behavior in the prompt instead.

Substitute the per-PR values plus the resolved absolute `scratch_dir`, `PYTHON`, `HOST_PY`, run-wide `<approve>`, and run-wide `<submit>` into this prompt:

```
<reviewer_persona_instructions>

---

Review ONE pull request in a stack. Review only this PR's delta, not the whole stack.

PR: #<num> -- <title>
PR URL: <url>
Repo: <owner>/<repo>
REVIEW_ID: <REVIEW_ID>
Approve after review: <approve>
Submit as COMMENT after review: <submit>
Scratch directory: <absolute scratch_dir>
Python: <absolute PYTHON>
Host helper: <absolute HOST_PY>

Treat the three values above as already resolved absolute paths. Inline them in every command. Do not rely on shell variables between `run_terminal_command` calls.

Parallel-safety constraints:
- Run only read-only git and gh commands. Never checkout, switch, reset, stash,
  run `gh pr checkout`, or fetch into a branch. Do not modify the worktree,
  index, or HEAD.
- Write only under the resolved scratch directory. Every filename must include
  both REVIEW_ID and the PR number. Use:
  - <scratch_dir>/grok-review-<REVIEW_ID>-pr<num>.diff
  - <scratch_dir>/grok-review-<REVIEW_ID>-pr<num>.md
  - <scratch_dir>/grok-review-<REVIEW_ID>-pr<num>.json
  - <scratch_dir>/grok-review-<REVIEW_ID>-pr<num>-post.json
  - <scratch_dir>/grok-review-<REVIEW_ID>-pr<num>-post.err
- Pass `--repo <owner>/<repo>` to every `gh pr` call. The `gh api` endpoint
  must include `repos/<owner>/<repo>`.

Steps:
1. Fetch the diff with `gh pr diff <num> --repo <owner>/<repo>` and persist it
   to the per-PR diff file. Fetch `headRefOid` with `gh pr view ... --json
   headRefOid` and parse the JSON yourself or use `gh --jq`. If the diff is
   empty, post nothing, clean up all per-PR artifacts with `<PYTHON> <HOST_PY>
   cleanup`, and report NO CHANGES. Empty diffs are never approved.
2. Read the diff. The shared worktree may be on another branch. Fetch full
   post-change files with `gh api "repos/<owner>/<repo>/contents/<path>?ref=<headSha>"
   -H "Accept: application/vnd.github.raw+json"`; do not checkout the PR.
3. Write structured findings to the per-PR markdown file. Use `## Summary` and
   `## Issues`; severities are bug, suggestion, or nit. Each issue has a
   right-side `File: path:line`, Description, Suggestion, and `Status: open`.
4. Parse right-side diff positions exactly as documented in single-PR mode.
   Inline valid positions and promote missing or out-of-diff findings to the
   review body. Construct the payload as structured data, then persist valid
   JSON with the `write` tool. Do not hand-concatenate JSON and do not use a
   Python heredoc. Set `commit_id` to <headSha>.
5. Post one review:
   - Default, zero issues: post nothing and report NO REVIEW.
   - Default, issues: omit `event` for PENDING and report the `/files` URL.
   - Submit true, zero issues: post nothing and report NO REVIEW.
   - Submit true, issues: set `event` to `COMMENT` and report COMMENTED.
   - Approve true: compare the PR author's login with `gh api user`. If they
     match, do not post; preserve the review markdown, payload, and diff, and
     report ERROR with the self-approval cause. Otherwise set `event` to
     `APPROVE`, including an empty comments array when there are zero issues,
     and report APPROVED.
   On an HTTP 422 caused by an inline position, fold inline findings into the
   body and retry once. Do not retry other failures.
6. On success or a no-post outcome, clean up every per-PR artifact with the
   resolved `<PYTHON> <HOST_PY> cleanup` command. On post failure, preserve the
   review markdown, payload, and diff; clean only post capture files and report
   every preserved path.

Report PR number, verdict, bug/suggestion/nit counts, inline/body counts, final
state (APPROVED, COMMENTED, PENDING, NO CHANGES, NO REVIEW, or ERROR), exact
error text, and preserved paths when applicable.
```

