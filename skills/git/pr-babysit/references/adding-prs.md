## Adding PRs

When the user runs `/pr-babysit add [--ship] <number> [<number>...]`:

If `--ship` is present, set `ship: true` on every PR registered in this invocation (the whole stack when a stack is detected). Otherwise leave `ship` at the default `false`.

### Step 1: Verify authentication

```bash
gh auth status
```

If not authenticated, report the error and stop.

### Step 2: Fetch PR details

For each PR number:

```bash
gh pr view <number> --json headRefName,baseRefName,url,title,state,number
```

Verify the PR exists and is open. If MERGED or CLOSED, inform the user and skip.

Determine the current repository:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Store this value as the `repo` field for all PR entries created in this invocation.

### Step 3: Detect stack membership

Stack detection determines whether the PR is standalone or part of a stack (Graphite or GitHub stacked PRs). Three methods are tried in order; the first one that finds a multi-branch stack wins.

#### Method A: API-based chain detection (universal, always runs first)

This method works regardless of which tool created the stack. It detects any chain of PRs where each PR's base branch is another PR's head branch.

```bash
# Get the default branch for the repo
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')

# Get the base branch of the added PR
BASE=$(gh pr view <number> --json baseRefName --jq '.baseRefName')
HEAD=$(gh pr view <number> --json headRefName --jq '.headRefName')
```

If `BASE == DEFAULT_BRANCH`, the PR might still be mid-stack (other PRs could target its head branch). Check both directions:

Fetch all open PRs in the repo once and reuse for both directions:

```bash
# Fetch all open PRs in the repo (used for both downstack and upstack walks)
ALL_PRS=$(gh pr list --state open --json number,headRefName,baseRefName --limit 200)
```

**Walk downstack** (toward trunk): Starting from the added PR, follow `baseRefName` by looking up which open PR’s `headRefName` matches the current PR’s `baseRefName`. Repeat until `baseRefName == DEFAULT_BRANCH`.

**Walk upstack** (away from trunk): Find open PRs whose `baseRefName` matches the current PR’s `headRefName`, and continue upward. Repeat until no more PRs are found.
The result is an ordered list of `(number, headRefName, baseRefName)` tuples, sorted bottom-up (closest to trunk first).

If only one PR was found (no chain), this PR is standalone. Proceed to Step 4.

If multiple PRs were found, this is a stack. Continue to Method B/C to determine the stack type and tool.

#### Method B: Graphite CLI detection

Run only if the API chain detected multiple PRs.

```bash
# Check if graphite CLI is available
gt --help 2>/dev/null | grep -qi graphite
```

If graphite is available:

```bash
git fetch origin <headRefName>
gt checkout <headRefName> 2>/dev/null
```

If `gt checkout` succeeds (the branch is tracked by graphite locally), verify the stack by walking:

```bash
# Go to the bottom of the stack
gt bottom 2>/dev/null

# Collect branches bottom-up
STACK_BRANCHES=()
while true; do
  BRANCH=$(git branch --show-current)
  STACK_BRANCHES+=("$BRANCH")
  # Try to move up; if gt up fails, we're at the top
  gt up 2>/dev/null || break
done
```

If `gt checkout` fails (branch not tracked — **common when the PR was created on a different machine**), import the stack into graphite using the API-detected chain:

```bash
# Sync graphite metadata from remote.
# Warning: --force overwrites all local Graphite metadata. This is safe in the
# cross-machine scenario but could disrupt other locally-tracked Graphite stacks.
# Log whether this succeeds or fails for debugging.
gt sync --force --no-interactive 2>/dev/null || true

# Try checkout again after sync
gt checkout <headRefName> 2>/dev/null
```

If checkout still fails, manually track each branch in the chain using the API-detected topology:

```bash
# Save current branch to restore after tracking
ORIG_BRANCH=$(git branch --show-current || echo "main")

# For each branch in the API-detected chain (bottom-up order):
# First branch's parent is the default branch
git fetch origin
for i in "${!CHAIN_BRANCHES[@]}"; do
  BRANCH="${CHAIN_BRANCHES[$i]}"
  if [ $i -eq 0 ]; then
    PARENT="$DEFAULT_BRANCH"
  else
    PARENT="${CHAIN_BRANCHES[$((i-1))]}"
  fi
  git checkout -B "$BRANCH" "origin/$BRANCH" 2>/dev/null
  gt track --parent "$PARENT" --no-interactive 2>/dev/null || true
done

# Restore original branch to avoid polluting the main workspace
git checkout "$ORIG_BRANCH" 2>/dev/null || git checkout "$DEFAULT_BRANCH" 2>/dev/null
```

After tracking, verify with `gt bottom` / `gt up` as above. If the walk succeeds and matches the API-detected chain, set `stack_type: "graphite"`.

If graphite tracking still fails (e.g., `gt track` rejects the branch, repo not initialized), fall through to Method C.

#### Method C: GitHub Stacked PRs detection

Run only if Method B did not claim the stack (graphite not available or tracking failed).

**Note**: GitHub Stacked PRs (`gh stack`) is currently in private preview. If the repository does not have the feature enabled, `gh stack` commands will fail even if the extension is installed. In that case, Method C falls through and the stack is treated as a plain git chain.

```bash
# Check if gh-stack extension is installed (don't use `gh stack view` — it exits
# non-zero (code 2) when the current branch isn't in a tracked stack, giving
# false negatives even when the extension is installed)
gh extension list 2>/dev/null | grep -q gh-stack
```

If `gh stack` is installed:

```bash
# Try to check out the stack from the PR number
# Exit code 2 = not a GitHub stack (fall through)
# Exit code 4 = API failure (log error, fall through)
# Exit code 0 = success
gh stack checkout <number> 2>/dev/null
```

If `gh stack checkout` succeeds (exit code 0):

```bash
# Get the stack structure
STACK_JSON=$(gh stack view --json 2>/dev/null)
```

Parse `STACK_JSON` to extract the ordered list of branches and their PR numbers. Set `stack_type: "github"`.

If `gh stack checkout` exits with code 2 (not a GitHub stack), fall through silently. If it exits with code 4 (API failure), log a warning and fall through. For any other non-zero exit code, log and fall through.

If `gh stack` is not installed, fall through.

#### Final classification

| Condition | `stack_type` | `stack_id` |
|-----------|-------------|------------|
| Method B succeeded (graphite tracks the stack) | `"graphite"` | Bottom branch name |
| Method C succeeded (GitHub stacked PR) | `"github"` | `"gh-stack-<bottom_pr_number>"` |
| API chain found multiple PRs but neither tool claims them | `null` | `"chain-<bottom_pr_number>"` |
| Only one PR found (no chain) | `null` | `null` |

For all stack types, assign `stack_position` by index: 0 = bottom (closest to trunk), incrementing upward.

For each branch in the stack, resolve its PR number:

```bash
gh pr view <branch> --json number --jq '.number'
```

If `gh pr view <branch>` fails for a branch (no associated PR, or PR is closed), skip that branch and warn the user.

### Step 4: Register PR(s)

Register the PR(s) determined by Step 3:
- **Stack detected**: Register **all** PRs in the stack with the appropriate `stack_id`, `stack_type`, and `stack_position`.
- **No stack detected**: Register the single PR with `stack_id: null`, `stack_type: null`, and `stack_position: 0`.

### Step 5: Write state and report

- Deduplicate: skip any PR number + repo combination already in the watchlist. If `--ship` was passed and the PR is already watched, set `ship: true` on that PR. If that PR's `stack_id` is a non-null string, also set `ship: true` on every other PR that shares that `stack_id`. Do not match other PRs when `stack_id` is `null`.
- Write the updated state file.
- Report what was added, including stack information if applicable.

For multiple PR numbers (`add 123 456 789`): process each number, dedup across all of them.

