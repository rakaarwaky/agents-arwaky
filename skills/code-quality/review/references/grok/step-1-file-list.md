# Step 1: Collect the module's file list

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
- `files_file`: `${scratch_dir}/grok-review-files-<REVIEW_ID>.txt` — the module's tracked file list.
- `summary_file`: `${scratch_dir}/grok-review-summary-<REVIEW_ID>.md`.

## Run state

- `mode`: always `module`.
- `target`: the resolved absolute module path.
- `personas`: the ordered list of selected persona names (from the flags, or all 10 when the bare form / `--all` is used).

## Collection

Run `git -c color.ui=false -c color.diff=false -c core.quotepath=false ls-files <target>` and persist its stdout to `<files_file>`. Inline the absolute `target` and `files_file` paths.

If `<files_file>` is empty or whitespace-only, print "No tracked files under `<target>`. Nothing to review." and stop — no cleanup needed; use the empty-path Final report.

Otherwise read the tracked file list from `<files_file>` and report progress per [step-4-in-progress-reporting.md](step-4-in-progress-reporting.md).
