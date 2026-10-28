# In-Progress Reporting


## In-Progress Reporting

Give the user a brief status update after each significant event:

- After parse: `"Parsed PR Plan: <N> PRs, <L> levels, max parallelism: <P>"`
- After linearize: `"Linearized stack order: PR1 -> PR4 -> PR2 -> PR5 -> PR3"`
- After branch creation: `"Created branches for <N> level-0 PRs. Starting implementation..."`
- After launching a PR: `"Launching <pr.id> (<pr.title>)..."`
- After PR implementation completes: `"<pr.id> (<pr.title>) implemented in <duration>. <N> files changed. Starting review..."`
- After per-PR specialization selection: `"<pr.id> review (effort <E>): <composition>, e.g. 1 general + security + plan + simplicity (PR touches auth). Simplicity is always pinned."`
- After all of a PR's reviewers complete: `"<pr.id>: all <K> reviewers complete. Merging findings..."`
- After review (0 issues): `"<pr.id> review: 0 issues found. PR complete."`
- After review (N issues): `"<pr.id> merged review: <N> issues (<X> bugs [tag breakdown], <Y> suggestions, <Z> nits). Fixing..."`
- After fix cycle: `"<pr.id> fix applied. Re-reviewing with <K> reviewers (round <N>)..."`
- After PR fully complete: `"<pr.id> complete. <M> of <total> PRs done. <K> newly ready."`
- After failure: `"<pr.id> FAILED: <reason>. Skipping <N> dependents. <M> independent PRs continue."`
- After all PRs done: `"All PRs complete. Building <Graphite|git branch> stack..."` (pick the label based on `graphite_available`)
- After stack submission (Graphite mode): `"Stack submitted: <N> PRs. URLs: [...]"`
- After stack push (plain-git mode, no `--auto-pr`): `"Stack pushed: <N> branches. Open these compare URLs (or run the gh pr create commands) to open PRs: [...]"`
- After stack push (plain-git mode, with `--auto-pr`, all succeeded): `"Stack pushed and draft PRs created: <N> branches. URLs: [...]"`
- After stack push (plain-git mode, with `--auto-pr`, mixed results): `"Stack pushed: <N> branches. <X> PRs created via gh, <Y> need manual creation via the printed compare URLs."`
- After stack push (plain-git mode, non-GitHub remote): `"Stack pushed: <N> branches to non-GitHub remote. Open PRs via your forge UI."`
- After cleanup: `"Cleanup complete."`
- After memory flush: `"Memory updated with N patterns from this run."` (or `"Memory file created with N patterns."` for first run)
- After final report (Graphite mode only): `"Run '/pr-babysit add <bottom-pr-number>' to monitor CI."`

## Safety Guardrails

See [`references/safety-guardrails.md`](references/safety-guardrails.md).
