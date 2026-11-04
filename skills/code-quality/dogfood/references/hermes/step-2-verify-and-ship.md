# Step 2: Verify & Ship

Hermes owns the final verification and delivery of the QA report. Read Grok's report, verify evidence integrity, and deliver it to the user.

## 2a: Read the Report

Read `{output_dir}/report.md` and cross-check:

- **Structure**: matches `templates/dogfood-report-template.md` shape — per-issue sections with evidence and severity.
- **Evidence integrity**: every issue cites evidence (screenshot path, transcript excerpt, log lines, or adb logcat). Spot-check 2–3 evidence files actually exist on disk under `{output_dir}/`. Missing or empty evidence files → the issue is unverifiable; flag it in the report to the user.
- **No source modification**: `git -C <worktree_path> status --short` (worktree case) must be clean — dogfood must not have modified the app under test. If the app tree is dirty, report it; do not commit the dirt.
- **Severity sanity**: issues marked `critical`/`blocker` should have the strongest evidence. If a critical has thin evidence, downgrade it in your summary to the user and say so.

## 2b: Triage Summary

Produce a short triage for the user (this is your value-add, not a re-do of the report):

1. **Total issues** by severity (critical / major / minor / nit).
2. **Top 3 issues** — the ones most likely to block a release or user flow, with their evidence paths.
3. **Patterns** — any repeated root cause across issues (e.g. same API endpoint failing in 3 flows).
4. **Deferred / unverified** — issues you could not verify evidence for.

## 2c: Deliver

The report stays in `{output_dir}/report.md` inside the worktree (or `--cwd`). If the user wants it out of the worktree:

- Copy `{output_dir}` to the user's requested location (`cp -r` / the user's own tooling).
- Do NOT commit the report into the app repo unless the user explicitly asks — it is a QA artifact, not app source.

## 2d: Report

Report to the user:

> Dogfood of <target> (<type>) complete. Report: <abs path to report.md>. <N> issues (<breakdown>). Top issues: ... Patterns: ... Worktree left in place (or: headless run, no worktree).

Then proceed to Step 3.
