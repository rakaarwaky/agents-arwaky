# Step 5 details (Final report) and Step 3 Main/Local/Branch post-processing

## Step 5: Final report

Present a final report to the user. Item 1 is always included; item 2 is omitted on empty-diff exits; item 3 is omitted on empty-diff exits and on PR zero-issue early-exits; item 4 is always included. In **stack mode**, items 2-3 are subsumed by the per-PR table in item 4 (the orchestrator collected no single combined diff); item 1 still names the mode and lists the stack.

1. **Mode + target** -- e.g., "Current branch vs origin/main" (main mode) or "Local changes" or "Branch feature/foo vs origin/main" or "PR #4221: <pr_title>".
2. **Files reviewed** -- count and (if 10 or fewer) the list. Omit on empty-diff exits.
3. **Issues by severity** -- the bug/suggestion/nit counts. Omit on empty-diff exits and on PR zero-issue early-exits (counts are all zero by construction; the mode-specific bullet says so).
4. **Mode-specific output**:
   - Main / local / branch (successful review): full paths to `<review_file>` and `<summary_file>`, plus a one-line copy of the summary's top-issues list.
   - Main / local / branch (empty-diff exit): "No changes to review." (local mode) or "Branch has no changes vs `<BASE>`." (main mode) or "Branch `<target>` has no changes vs `<BASE>`." (branch mode). No file paths -- nothing was written.
   - PR (successful post): the structured block from Step 3 PR mode item 7, plus the review `id` from the response (for traceability). Default: the PENDING submit block (PR number, inline-comment count, body-findings count, Files-tab URL, submit reminder). If `submit` was true: the COMMENTED block (PR URL, comments already visible, no submit reminder). If `approve` was true: the APPROVED block stating the review was submitted (published) and the PR approved, with the PR URL and no submit reminder.
   - PR (zero-issue early-exit, no approve, no submit): "Reviewer found no issues on PR #<pr_number>. No PENDING review created."
   - PR (zero-issue, submit): "Reviewer found no issues on PR #<pr_number>. No COMMENT review created."
   - PR (zero-issue, approve): "Reviewer found no issues on PR #<pr_number>. Submitted an empty APPROVING review -- the PR is now approved."
   - PR (empty-diff exit): "PR #<pr_number> has no changes. Nothing to review." (if `--approve` was passed, add "Not approved -- an empty-diff PR has no changes to approve.")
   - PR (failed post): the verbatim stderr from `gh api` plus the HTTP status code, plus the preserved path to `<review_file>` so the user can recover the findings. If the failure was a self-approval 422, state that cause explicitly.
   - Stack (all PRs reviewed): a summary table over every PR in `stack_prs`, one row each, plus a totals line:

     ```
     PR    | Title              | bugs/sugg/nits | State    | Error
     #4221 | Add foo to bar     | 1/2/0          | APPROVED | -
     #4222 | Wire bar into baz  | 0/0/1          | APPROVED | -
     #4223 | Update callers     | 0/0/0          | APPROVED | -
     Totals: 3 PRs, 1 bug, 2 suggestions, 1 nit; 3 approved, 0 commented, 0 pending, 0 errored.
     ```

     Each row's State reflects that PR's own outcome: APPROVED (reviewed with `--approve`), COMMENTED (issues found and submitted with `--submit`), PENDING (issues found, no modifier -- default), NO CHANGES (empty diff -- never auto-approved), NO REVIEW (zero issues and not approving -- nothing posted), or ERROR (subagent failed to post; put the exact error text in the Error column). The totals line counts approved / commented / pending / errored PRs; NO CHANGES and NO REVIEW rows are shown but fall outside those buckets. (Because the modifiers are run-wide, APPROVED, COMMENTED, and PENDING do not mix within one run -- but errored / no-change / no-review rows can still appear alongside any.)

## Main/Local/Branch mode details (Step 3)

1. Read `<review_file>` via `read_file`.
2. Count issues by counting heading lines that match the regex `^### Issue \d+ -- Severity: (bug|suggestion|nit)$` and bucket them by the captured severity. Issues whose heading does not match this pattern (typo'd severity, missing severity field, malformed heading) are malformed -- log a one-line warning to the user listing the heading line and treat them as uncounted. Do not attempt to re-parse the body for a `Severity:` field; the heading is the canonical source. The same regex governs the parsing in Step 3 PR mode below.
3. Compute diff stats:

   ```text
   git -c color.ui=false -c color.diff=false diff --shortstat <range>
   ```

   For local mode, run `git -c color.ui=false -c color.diff=false diff --shortstat HEAD` and also count untracked files separately. For branch mode, inline the resolved merge base and target in `git -c color.ui=false -c color.diff=false diff --shortstat <MERGE_BASE>..<target>`. For main mode, inline the merge base in `git -c color.ui=false -c color.diff=false diff --shortstat <MERGE_BASE>..HEAD`.

   **Color-off on every git diff.** All `git diff` / `git diff --name-only` / `git diff --shortstat` / `git diff --no-index` invocations in this skill MUST pass `-c color.ui=false -c color.diff=false` (or equivalent `NO_COLOR=1` / `GIT_CONFIG_COUNT` overrides). ANSI color codes from a user-enabled `color.ui=always` frequently break agent parsing and force retries; never rely on ambient git color config.

4. Use the `write` tool to create `<summary_file>` with this structure:

   ```markdown
   # Review Summary

   - **Mode**: <mode>
   - **Target**: <target-summary>
   - **Files reviewed**: <count> (<list, truncated to 10 if longer>)
   - **Diff stats**: <shortstat-line>
   - **Issue counts**: <X> bugs, <Y> suggestions, <Z> nits

   ## Top issues

   <First 5 issue titles, one per line, in the form "[severity] file:line -- description (truncated to ~100 chars)">

   See the full review at: <review_file>
   ```

5. Print to the user:
   - Inline issue counts and the file paths to `<review_file>` and `<summary_file>`.

Do NOT delete `<review_file>` or `<summary_file>` in main/local/branch modes -- those files ARE the deliverable.
