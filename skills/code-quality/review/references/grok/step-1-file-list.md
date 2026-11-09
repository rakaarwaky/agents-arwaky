# Step 1: Collect the review scope file list

## Before Step 1: setup

Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, `id -u`, `chmod`, `jq`, `wc`, `rm -f`, or `sort -u`, and do not write to `/tmp`. Use `run_terminal_command`.

1. Confirm cwd is a git work tree with `git rev-parse --is-inside-work-tree`. If this fails, report that cwd is not a git repository and stop.
2. Resolve `HOST_PY` as `<dirname of SKILL.md>/scripts/host.py`.
3. Find a real Python 3 interpreter. Try in order: `python`, `py -3`, `python3`. Reject any path containing `WindowsApps`. If none works, tell the user to install Python 3 and stop.
4. Run `<python> <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `scratch_dir`, and `run_id` as `REVIEW_ID`.

Validate that `REVIEW_ID` is exactly 8 hexadecimal characters. If setup failed or any required value is empty, report the error and stop.

**Inline the resolved absolute `scratch_dir` and `PYTHON`** into every later command and subagent prompt. Do not rely on shell variables surviving across `run_terminal_command` calls. Also inline the absolute `HOST_PY` path where cleanup is delegated.

## Derived paths

Define these paths once and reuse them:

- `review_file_<persona>`: `${scratch_dir}/grok-review-<REVIEW_ID>-<persona>.md` — one per selected persona.
- `files_file`: `${scratch_dir}/grok-review-files-<REVIEW_ID>.txt` — the review scope file list.
- `diff_file`: `${scratch_dir}/grok-review-diff-<REVIEW_ID>.txt` — the unified diff (commit/uncommit/pr modes only; not written for `path` mode).
- `summary_file`: `${scratch_dir}/grok-review-summary-<REVIEW_ID>.md`.

## Run state

- `mode`: one of `commit`, `uncommit`, `pr`, `path` (set by Step 0).
- `target`: the resolved review target (see per-mode rules below).
- `personas`: the ordered list of selected persona names (1–3, set by Step 0 auto-selection).

## Per-mode collection

### `mode = commit`

Review the changes in the **last commit** (`HEAD`).

1. Get the changed file list: `git -c color.ui=false diff --name-only HEAD~1..HEAD` → persist to `<files_file>`.
2. Get the unified diff: `git -c color.ui=false diff --no-color HEAD~1..HEAD` → persist to `<diff_file>`.
3. `target` = `<last commit short hash + subject>`, e.g. `a1b2c3d "fix: handle null pointer"`.

If `<files_file>` is empty, print "Last commit has no changed files. Nothing to review." and stop — no cleanup needed.

### `mode = uncommit`

Review **uncommitted changes** (staged + unstaged in the working tree, relative to `HEAD`).

1. Get the changed file list: `git -c color.ui=false diff --name-only HEAD` → persist to `<files_file>`. This covers both staged and unstaged tracked modifications.
2. Get the unified diff: `git -c color.ui=false diff --no-color HEAD` → persist to `<diff_file>`.
3. `target` = `uncommitted changes (working tree vs HEAD)`.

If `<files_file>` is empty, print "No uncommitted changes. Working tree is clean. Nothing to review." and stop — no cleanup needed.

### `mode = pr`

Review the diff of **PR `<pr-number>`** on GitHub.

1. Run `gh pr diff <pr-number>` → persist stdout to `<diff_file>`.
2. Get the changed file list from the diff: parse the `diff --git a/<path> b/<path>` lines and extract `<path>`; one file per line → persist to `<files_file>`.
3. `target` = `PR #<pr-number>`.
4. If `gh pr diff` fails (PR not found, not authenticated, or no network), report the error and stop.

If `<files_file>` is empty after parsing, print "PR #<pr-number> has no diff. Nothing to review." and stop.

### `mode = path`

Review the **current content** of a file or directory, ignoring commit status.

1. `target` = the resolved absolute path from Step 0.
2. If `<target>` is a **file**: write its single path to `<files_file>` (one line). No `<diff_file>` is written.
3. If `<target>` is a **directory**: run `git -c color.ui=false -c core.quotepath=false ls-files <target>` → persist to `<files_file>`. No `<diff_file>` is written.
4. If `<files_file>` is empty (directory with no tracked files), fall back to listing regular files under the directory with `find <target> -type f | sort` (POSIX) or `Get-ChildItem <target> -Recurse -File | Sort-Object` (PowerShell) and persist to `<files_file>`.
5. If `<files_file>` is still empty, print "No files under `<target>`. Nothing to review." and stop — no cleanup needed.

## Report progress

After collection, report per [step-4-in-progress-reporting.md](step-4-in-progress-reporting.md).
