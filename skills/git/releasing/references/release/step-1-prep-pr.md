# Step 1 — release prep PR

The prep PR commits the version stamp and changelog that the workflow reads; it is not a manual edit of version files. **All work happens in an Orca worktree so the main clone stays clean. Never edit files in the main clone.**

1. Create an Orca worktree for the release branch:

   ```shell
   orca worktree create --repo path:<repo> --name "release/$NEW_VERSION" --agent grok --no-parent --json
   ```

   Read the worktree path from `result.worktree.path`.

2. Inside the worktree, run the bump script to write the version stamp and changelog:

   ```shell
   cd <worktree path>
   bash scripts/bump.sh "$NEW_VERSION"
   git add -A
   git commit -m "chore(release): $NEW_VERSION"
   ```

3. Push the branch and open the PR with the `release` label:

   ```shell
   git push -u origin "release/$NEW_VERSION"
   gh pr create --base main --head "release/$NEW_VERSION" \
     --title "chore(release): $NEW_VERSION" \
     --body "Calver release prep for $NEW_VERSION." \
     --label release
   ```

   Verify the label was applied:

   ```shell
   gh pr view <pr-number> --json labels --jq '[.labels[].name]'
   # Must include "release" — Risa's auto-release automation skips PRs with this label.
   ```

4. Set the worktree status to in-review and wait for green CI:

   ```shell
   orca worktree set --worktree <worktree id> --workspace-status in-review
   gh pr checks <pr-number> --watch
   ```

5. Auto-approve and merge with admin:

   ```shell
   # If PR author differs from current token user:
   gh pr review <pr-number> --approve 2>/dev/null || true
   # Admin squash merge directly:
   gh pr merge <pr-number> --admin --squash
   ```

6. Create and push the git tag (if the repo's release pipeline is tag-driven and no auto-tag workflow exists):

   ```shell
   cd <worktree path>
   git fetch origin main
   git checkout -b temp-tagging origin/main
   git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"
   git push origin "$NEW_VERSION"
   git checkout -
   git branch -D temp-tagging
   ```

   IF the repo has an auto-tag workflow (e.g. a `release.yml` `create-tag` job that tags on `chore(release):` PR merge) -> skip this step; the workflow creates the tag automatically.

7. Retire the worktree:

   ```shell
   orca worktree rm --worktree <worktree id> --json
   ```

**Never touch the main clone.** If the workflow or bump script itself needs fixing (e.g. a workflow expression bug, a test gate misconfiguration), create a separate Orca worktree for that fix, push a branch, open a PR to main, and merge it. Only then continue the release prep PR.

Recovery: if the prep PR merge failed, fix in the same worktree branch, re-push, re-merge, then retire the worktree and continue from Step 2.
