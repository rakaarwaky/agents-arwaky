# Step 5: Push, Open PRs & Final Report

Push verified branches, open draft pull requests linking all grouped issues, rebase open worktrees if PRs merge mid-batch, retire worktrees, and synthesize the final run report.

## 5a: Push Verified Branches

For each verified worktree:

```bash
git -C "$WT_PATH" push --force-with-lease origin "$WT_BRANCH"
```

Never use bare `--force`. If the push is rejected due to remote updates, fetch origin, rebase locally in `$WT_PATH`, re-verify, and push with `--force-with-lease`.

## 5b: Open Draft Pull Requests

Open exactly one draft PR per issue group:

```bash
gh pr create \
  --base main \
  --head "$WT_BRANCH" \
  --draft \
  --title "$PR_TITLE" \
  --body "$PR_BODY"
```

### PR Formatting
- **Title**: Descriptive summary of the change, citing the primary issue numbers (e.g. `fix(auth): resolve redirect loop and token refresh (fixes #42, #45)`).
- **Body**:
  - Summary of changes implemented by Grok Build.
  - List of closing keywords for every issue in the cohort:
    ```markdown
    Closes #42
    Closes #45
    ```
  - Summary of reproduction steps and verification evidence.
- *Note*: Auto-merging is strictly forbidden. The skill produces draft PRs for user review and CI gate evaluation.

## 5c: Rebase Open Worktrees (if PRs merge mid-batch)

If a PR merges into the default branch during batch processing, rebase remaining open worktrees before continuing:

```bash
cd "$OTHER_WT_PATH"
git fetch origin
git rebase origin/main
git push --force-with-lease origin "$OTHER_WT_BRANCH"
```

## 5d: Retire Verified Worktrees

Once the branch is pushed and the draft PR is opened, retire the worktree to free resources:

```bash
"$ORCA" worktree rm --worktree "id:$REPO_ID::$WT_PATH" --force --json
```

## 5e: Synthesize Final Report

Deliver a clear, factual completion report to the user:

1. **Issues Processed**:
   - Total issues evaluated from argument hint.
   - Issues verified `fixed-on-main` (closed with evidence comments).
   - Issues categorized as `still-broken`.
2. **Issue Groupings**:
   - Explanation of cohorts formed: which issues were grouped together into a single `/implement` session and why (shared files/subsystems).
   - Which issues were isolated into separate sessions and why.
3. **Execution & Grok Sessions**:
   - Number of Grok Build sessions spawned.
   - Verification command outputs and test results.
4. **Pull Requests Opened**:
   - List of draft PR links with branch names and associated issue numbers.
5. **Open / Blocked Items**:
   - Any issues that failed implementation or verification, with verbatim error output and recommendations.
