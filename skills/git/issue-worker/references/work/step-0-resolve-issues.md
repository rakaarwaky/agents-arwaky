# Step 0: Resolve & Inspect Issues

Resolve target GitHub issue numbers from user arguments, verify authentication, handle zero-issue and disabled-issue edge cases gracefully, query issue metadata, and stage issue data for triage.

## 0a: Verify GitHub Authentication & Remote

Check authentication and resolve repository identity:

```bash
gh auth status
```

If `gh` is unauthenticated or `GITHUB_TOKEN` is unset, halt immediately and prompt authentication (`gh auth login`).

Detect repository owner and name from the current git remote:

```bash
OWNER_REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null)"
if [[ -z "$OWNER_REPO" ]]; then
  echo "Error: Current directory is not a git repository with a recognized GitHub remote."
  exit 1
fi
OWNER="$(echo "$OWNER_REPO" | cut -d/ -f1)"
REPO="$(echo "$OWNER_REPO" | cut -d/ -f2)"
```

## 0b: Parse User Argument Hint & Query Issues

Parse the argument hint `<latest|oldest> <N> | <issue-numbers>` provided by the user:

- **`latest <N>`** — query the N most recently created open issues:
  ```bash
  QUERY_OUTPUT="$(gh issue list --state open --limit "$N" --json number,title,body,labels,createdAt,updatedAt 2>&1)"
  QUERY_STATUS=$?
  ```
- **`oldest <N>`** — query the N oldest open issues:
  ```bash
  QUERY_OUTPUT="$(gh issue list --state open --search "sort:created-asc" --limit "$N" --json number,title,body,labels,createdAt,updatedAt 2>&1)"
  QUERY_STATUS=$?
  ```
- **Explicit issue numbers** (e.g. `42 45 48` or `#42, #45`):
  Query each issue directly, recording missing or closed issues:
  ```bash
  ISSUES_JSON="[]"
  for NUM in $ISSUE_NUMBERS; do
    RAW="$(gh issue view "$NUM" --json number,title,body,labels,createdAt,updatedAt,comments 2>&1)"
    if [[ $? -eq 0 ]]; then
      ISSUES_JSON="$(echo "$ISSUES_JSON" | jq --argjson item "$RAW" '. += [$item]')"
    else
      echo "Notice: Issue #$NUM not found or inaccessible: $RAW"
    fi
  done
  ```
- **Filter query** (e.g. `--label bug`):
  ```bash
  QUERY_OUTPUT="$(gh issue list --state open --label "<label>" --limit "$N" --json number,title,body,labels,createdAt,updatedAt 2>&1)"
  QUERY_STATUS=$?
  ```

## 0c: Error Handling & Zero-Issue Early Exit

Before proceeding to triage or worktree creation, evaluate the query results for edge cases:

### Case 1: Issues Disabled for Repository
If the GitHub API responds that issues are disabled:
```bash
if echo "$QUERY_OUTPUT" | grep -qi "issues are disabled"; then
  echo "Error: GitHub Issues are disabled for repository $OWNER_REPO in repository settings."
  echo "Enable issues at https://github.com/$OWNER_REPO/settings (under General > Features > Issues) to use /issue-worker."
  exit 1
fi
```

### Case 2: Zero Open Issues in Repository
If `gh issue list` exits 0 but returns an empty list (`[]` or 0 items):
```bash
COUNT="$(echo "$QUERY_OUTPUT" | jq 'length' 2>/dev/null || echo 0)"
if [[ "$COUNT" -eq 0 ]]; then
  echo "Repository $OWNER_REPO has 0 open issues. No action required."
  
  # Check if specification documents exist that could produce issues
  if ls ROADMAP.md BACKLOG.md PRD.md 1>/dev/null 2>&1; then
    echo "Notice: Spec documents detected (ROADMAP/BACKLOG/PRD). To audit specs and create tracking issues, run: /issue-maker"
  fi
  exit 0
fi
```
**Zero Worktrees Invariant**: On zero open issues, halt immediately. Do not create Orca worktrees, do not launch decision quizzes, and do not invoke child agents.

### Case 3: Explicit Numbers All Invalid / Closed
If explicit issue numbers were provided but none could be resolved:
```bash
VALID_COUNT="$(echo "$ISSUES_JSON" | jq 'length' 2>/dev/null || echo 0)"
if [[ "$VALID_COUNT" -eq 0 ]]; then
  echo "None of the specified issue numbers exist or are accessible in $OWNER_REPO. Halting cleanly."
  exit 0
fi
```

## 0d: Extract Issue Metadata & Stage

For all validated issues, extract and stage the core operational metadata:

1. **Issue Number and Title**: `#<number>` — `<title>`.
2. **Cited Files and Code Locations**: Grep the issue body for file paths, line references (`file.rs:42`), function/class names, or error stack traces.
3. **Reported Symptoms**: Expected vs actual behavior, steps to reproduce, error snippets.
4. **Labels**: Categorization (`bug`, `enhancement`, `refactor`, `documentation`).

Stage the resolved issues in `/tmp/issue-worker/staged-issues.json` so subsequent steps do not repeatedly query the GitHub API.

Proceed to Step 1 (`step-1-triage-and-verify.md`).
