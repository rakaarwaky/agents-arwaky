# Step 1 — release prep PR

Working directory: project root. The prep PR commits the version stamp and changelog that the workflow reads; it is not a manual edit of version files.

1. Create the prep branch and open the PR:

   ```shell
   git checkout -b "release/$NEW_VERSION"
   git push -u origin "release/$NEW_VERSION"
   gh pr create --base main --head "release/$NEW_VERSION" \
     --title "release: $NEW_VERSION" \
     --body "Calver release prep for $NEW_VERSION." \
     --label release
   ```

2. The PR must be green (CI passing on the release branch) before proceeding:

   ```shell
   gh pr checks <pr-number> --watch
   ```

3. Auto-approve and merge with admin, then switch back to main:

   ```shell
   gh pr review <pr-number> --approve
   gh pr merge <pr-number> --admin --squash
   git checkout main
   git pull origin main
   ```
