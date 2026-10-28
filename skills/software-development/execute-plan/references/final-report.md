# Final Report

## Final Report

After stack assembly, cleanup, and memory flush, present a final report:

1. **Summary** -- which PRs were implemented, total files changed across all PRs.
2. **Execution stats**:
   - Total PRs: N (M completed, K failed, J skipped)
   - Levels: L, Max parallelism achieved: P
   - Effort level: E (reviewers per PR, per the Step 5 table); specializations used across the run: <deduped list from all PRs' `reviewer_configs`>. Simplicity is always pinned.
3. **Review stats** -- total review rounds across all PRs, total issues found and fixed (broken down by severity). Also break the issue counts down by source tag (General / Tests / Security / Plan / Simplicity) aggregated across all PRs.
4. **Stack** -- linearized order, branch names, and URLs.
   - **Graphite mode**: label this section "Graphite stack" and list the PR URLs from `gt ls --json`.
   - **Plain-git mode**: label this section "Git branch stack" and render `pr_urls` entries by `kind`. If a `note` field is present on the entry, append it verbatim to the rendered line (in parentheses or on a continuation line).
     - `kind: "pr"`: print as "PR: `<url>`" (plus `note` if present — no current code path attaches one, but the renderer accepts a `note` field on this kind to keep the rendering rules uniform across all three kinds).
     - `kind: "compare"`: print as "Compare URL: `<url>` — open this to create the PR", append the matching command from `pr_create_commands`, and append `note` if present.
     - `kind: "pushed-only"`: print as "Pushed: `<branch>` — `<note>`" (the `note` is always present for this kind; it carries the user-facing explanation, e.g., "non-GitHub remote (<remote_url>) — open a PR via your forge UI").
5. **Failed PRs** (if any) -- which PRs failed and why, which were skipped as a result.
6. **Resumption** -- if any PRs failed: `"Resume with: /execute-plan --resume <PLAN_ID>"`
7. **Memory update** -- what patterns were written or updated in the workspace memory file. Use the `existed_before` flag from the helper's Step 10d update output to choose between "file created" and "file updated" wording.
8. **Next steps**:
   - **Graphite mode**: suggest `/pr-babysit add <bottom-pr-number>` to monitor CI and reviews.
   - **Plain-git mode**: do NOT suggest `/pr-babysit` (it depends on `gt` for stack walking — see its Step 2/3). The Stack section above already lists the URLs / commands; the Next-Steps text just adds a one-line note: "No automated CI/review monitoring is available in plain-git mode; open the PR URLs / compare URLs above and monitor them in the GitHub UI."

