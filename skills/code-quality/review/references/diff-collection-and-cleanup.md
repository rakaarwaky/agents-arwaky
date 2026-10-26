# Diff collection & cleanup — Steps 1 and 4

## Step 1 details (Main / Local / Branch / PR / Stack modes)


The diff collection commands differ per mode.

### Main mode

Main mode reviews the committed diff of the current branch against its merge-base with the default branch. It is the clean-tree path selected by a bare `/review`.

1. Run `git status --porcelain`. If the tree is dirty, do not assemble a mixed diff with shell loops. Tell the user to use `/review --local` for the working state or clean the tree before `/review --main`, then stop. Local changes must always be collected by `COLLECT_PY` as described below.
2. Determine `BASE`. Check `origin/main`, then `origin/master`, with separate `git rev-parse --verify --quiet <ref>` calls. If neither exists, ask the user which base ref to use, offering the name from `git symbolic-ref refs/remotes/origin/HEAD` when available plus an "Other" option.
3. Compute `MERGE_BASE` with `git merge-base <BASE> HEAD`. Collect the diff and changed-file names with commands whose absolute output paths have been inlined:

   ```text
   git -c color.ui=false -c color.diff=false -c core.quotepath=false diff <MERGE_BASE>..HEAD
   git -c color.ui=false -c color.diff=false -c core.quotepath=false diff --name-only <MERGE_BASE>..HEAD
   ```

   Persist their stdout to `<diff_file>` and `<files_file>` with `run_terminal_command` redirection that is valid for the active shell. Read the resulting diff size from file metadata or `read_file`; do not invoke a byte-counting utility. Apply the local size gates. For a >10 MB main diff, suggest a narrower `--pr <number>` or named `--branch` target.
4. If `<diff_file>` is empty or whitespace-only, print "Branch has no changes vs `<BASE>`." Skip the reviewer, run main/local/branch cleanup, and use the matching empty-diff Final report. Otherwise read `changed_files` from `<files_file>`.

### Local mode

1. Run `git status --porcelain`. If it is empty, print "No local changes to review (working tree clean)." Skip the reviewer, run main/local/branch cleanup, and use the matching empty-diff Final report.
2. Resolve `COLLECT_PY` as `<dirname of this SKILL.md>/scripts/collect_local_diff.py`. Run:

   ```text
   <PYTHON> <COLLECT_PY> --diff <diff_file> --files <files_file>
   ```

   Inline the absolute interpreter and paths. Parse the JSON stdout fields `bytes`, `files`, and `empty`. This helper is the required path for staged, unstaged, and untracked local changes. Do not replace it with shell `git diff` plus untracked-file loops, and do not mutate the index.
3. Apply the size gate from `bytes`:
   - Above 10 MB, abort and point the user to `git status --porcelain` and an appropriate platform-native size inspection to find generated or untracked data that belongs in `.gitignore`. Run cleanup and stop.
   - Above 1 MB, ask for confirmation. On decline, run cleanup and stop.
   - Otherwise proceed silently.
4. Read `changed_files` from the collector's `files` array. The helper handles repositories without `HEAD`, expected nonzero `git diff --no-index` results, untracked files, and symlinks without modifying the worktree or index.

### Branch mode

1. Determine `BASE` exactly as in main mode: probe `origin/main`, then `origin/master`, with separate commands. Ask for a base ref if neither exists.
2. Verify `<target>` with `git rev-parse --verify --quiet <target>`, then `origin/<target>`. If neither resolves, report the error and stop.
3. Compute `MERGE_BASE` with `git merge-base <BASE> <target>`. Collect `MERGE_BASE..<target>` with color disabled and `core.quotepath=false`, persisting the diff to `<diff_file>` and names to `<files_file>`. Inline all resolved paths rather than relying on shell variables across calls.
4. If `<diff_file>` is empty or whitespace-only, print "Branch `<target>` has no changes vs `<BASE>`." Skip the reviewer, run main/local/branch cleanup, and use the matching Final report. Otherwise read `changed_files` from `<files_file>`.

### PR mode

1. Run `gh auth status`. If it fails, tell the user to run `gh auth login` and stop.
2. Fetch metadata in one call and persist it to `<prmeta_file>`:

   ```text
   gh pr view <target> --json number,title,body,headRefOid,baseRefOid,headRefName,baseRefName,url,headRepository,headRepositoryOwner,isCrossRepository,files
   ```

   Parse the JSON yourself. Populate `pr_number`, `pr_title`, `pr_url`, `head_sha`, `base_sha`, and `.files[].path`. Parse `owner` and `repo` from `pr_url` with `^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/\d+`; the URL identifies the upstream even for cross-repository PRs. Persist the changed-file paths to `<files_file>` with the `write` tool or retain them as structured state. Do not invoke a separate JSON parser binary. Validate `pr_number`, `head_sha`, `base_sha`, `owner`, and `repo`; on missing data show the parsed metadata and stop.
3. Run `gh pr diff <target>` and persist stdout to `<diff_file>`.
4. If the diff is empty, print "PR #<pr_number> has no changes." If `approve` is true, add "Nothing to review or approve; not approved." Never auto-approve an empty diff. Skip the reviewer, run the PR no-reviewer cleanup, and use the matching Final report.

### Stack mode

Stack mode reviews every PR in a Graphite/stacked-PR stack. Step 1 only **discovers** the stack; the per-PR diffs are collected by each subagent in Step 2 (the orchestrator collects no diff itself in this mode).

**Discovery algorithm** (deterministic):

1. Verify `gh` authentication with `gh auth status` (same as PR mode). If it exits non-zero, stop with the same guidance -- warn that the stack cannot be fetched without `gh` auth and tell the user to run `gh auth login`.
2. Resolve the start PR (works for both numeric IDs and full URLs):

   Run `gh pr view <target> --json number,headRefName,baseRefName,url,title,state`.

   Parse `owner`/`repo` from the start PR's `url` (same regex as PR mode: `^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/\d+`). The `target` may be a full URL (or `GH_REPO` may be set), so the start PR can live in a different repository than the current checkout. Inline the resolved `<owner>/<repo>` in every subsequent discovery call and hand it to each per-PR subagent. Do not rely on a `REPO` shell variable surviving across commands.

3. Determine the repo default branch with `gh repo view <owner>/<repo> --json defaultBranchRef --jq '.defaultBranchRef.name'`. If the result is empty, fall back to whichever of `origin/main` / `origin/master` resolves via separate `git rev-parse --verify --quiet` calls, else `main`.
4. Fetch all open PRs once with `gh pr list --repo <owner>/<repo> --state open --limit 1000 --json number,headRefName,baseRefName,url,title` and build a map keyed by `headRefName`.

   `gh pr list` returns at most `--limit` PRs. If the number returned equals the limit, the list was truncated and stack neighbors beyond that window may be missing -- warn the user that stack discovery may be incomplete (rerun with a higher `--limit`) before proceeding with whatever was fetched.

5. **Walk down** (toward the base): start at the start PR. While its `baseRefName` is the `headRefName` of another open PR in the map, AND that base is not the default branch, AND it has not already been visited, prepend that base PR and continue the walk from it.
6. **Walk up** (toward the tip): traverse outward from the start PR over all open PRs. Maintain a frontier of already-included heads (initially just the start PR's `headRefName`); repeatedly add every not-yet-visited open PR whose `baseRefName` matches any already-included head, adding each newly added PR's `headRefName` to the frontier, until no open PR matches. This collects every reachable descendant -- a single child in the common linear chain, or all branches of a *branching* stack -- ordered by base-depth (distance from the start PR), rather than following only one child.
7. Produce `stack_prs` ordered base->tip, de-duplicated, always including the start PR. For each entry, parse `owner` and `repo` from its `url` with the same regex PR mode uses (`^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/\d+`) so every subagent has a defined owner/repo source. If no neighbors are found, proceed with a single-element stack and note: "starting PR has no detected stack neighbors; reviewing it alone."
8. Report the discovered stack to the user as an ordered list (`#<num> -- <title>`) BEFORE launching any subagents.

There is no orchestrator-side empty-diff or zero-issue short-circuit in stack mode -- each subagent makes those decisions for its own PR.

After Step 1, report progress: "Collected diff for <mode> target <summary>. Launching reviewer..." (in stack mode there is no single diff -- report the discovered stack instead, per the Stack mode subsection above and In-Progress Reporting.)

## Step 4 details (Cleanup)


Cleanup is asymmetric by mode and outcome:

- **Main, local, and branch:** keep `<review_file>` and `<summary_file>`. Remove only `<diff_file>` and `<files_file>`.
- **PR successful post:** remove `<review_file>`, `<diff_file>`, `<pending_review_payload>`, `<prmeta_file>`, `<files_file>`, `<post_file>`, and `<post_error_file>`.
- **PR failed post:** keep `<review_file>` and remove the other PR artifacts. Mention the preserved review path.
- **PR no reviewer output:** remove `<review_file>`, `<diff_file>`, `<pending_review_payload>`, `<prmeta_file>`, and `<files_file>`. Missing files are harmless.
- **Stack:** each subagent owns cleanup of its per-PR paths. It removes them after a successful post or no-post result and preserves the review, payload, and diff after a failed post. The orchestrator has no stack artifacts to remove.

For every cleanup, run the resolved `<PYTHON> <HOST_PY> cleanup <paths...>` command with absolute paths. Missing files are allowed. Do not use a shell deletion command. `--approve` and `--submit` use the same successful-post cleanup as the default PR path.
