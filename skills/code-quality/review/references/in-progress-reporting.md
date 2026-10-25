# Review in-progress reporting

Status-update phrasing emitted after each phase of the `review` skill. Keep lines short; the user sees them between subagent runs.

## In-Progress Reporting

Give the user a brief status update after each phase:

- After argument parsing: "Reviewing <mode> target: <target-summary>." (omit target for local mode -- "Reviewing local changes." -- and for main mode -- "Reviewing this clean branch vs its base branch."; the exact base ref is not resolved until Step 1, so do not template a specific ref into this line). When no flag was given, say which mode the default chose and why (e.g. "Working tree is clean, so reviewing the whole branch vs its base branch.").
- After Step 1 (diff collection): "Collected diff (<N> files, <M> changed lines). Launching reviewer..."
- After Step 1 (empty diff): "No changes to review. Proceeding to final report."
- After Step 1 (stack discovery): "Discovered N-PR stack: #a, #b, #c (base->tip). Launching reviewers..."
- After Step 2 (stack launch): "Launched N reviewers (one per PR) in parallel."
- After all stack subagents complete: "All stack reviewers complete. Aggregating results..."
- After Step 2 (reviewer complete): "Review complete. Processing findings..."
- After Step 3 (main / local / branch): "Found N issues (X bugs, Y suggestions, Z nits). Wrote <review_file> and <summary_file>."
- After Step 3 (PR, zero issues, no approve, no submit): "Reviewer found no issues on PR #<pr_number>. No PENDING review created."
- After Step 3 (PR, zero issues, submit): "Reviewer found no issues on PR #<pr_number>. No COMMENT review created."
- After Step 3 (PR, zero issues, approve): "Reviewer found no issues on PR #<pr_number>. Submitted an empty APPROVING review; PR approved."
- After Step 3 (PR, success, no approve, no submit): "Posted PENDING review with N inline comments and M body findings. Visit <url> to submit."
- After Step 3 (PR, success, submit): "Submitted COMMENT review on PR #<pr_number> with N inline comments and M body findings."
- After Step 3 (PR, success, approve): "Submitted and APPROVED review on PR #<pr_number> with N inline comments and M body findings."
- After Step 3 (PR, error -- 422 or any other non-zero exit): "Failed to post review. HTTP <status>. GitHub returned: <verbatim stderr>. Review notes preserved at <review_file>."
- After Step 3 (stack): one line per PR -- "PR #<num>: <APPROVED | COMMENTED | PENDING | NO CHANGES | NO REVIEW> -- X bugs, Y suggestions, Z nits." (or that PR's error) -- followed by "Stack review complete: <P> PRs, <A> approved, <C> commented, <Pn> pending, <E> errored."

