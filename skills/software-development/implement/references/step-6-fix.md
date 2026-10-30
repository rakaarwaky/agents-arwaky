# Step 6: Fix (resume implementer)


**Use `spawn_subagent` only** — do not apply fixes yourself.

Resume the original implementer to address **all** review findings.

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<implementer_subagent_id>`
- `description`: `"[implementer] Fix review issues"`

**resume_from on follow-ups** — never launch a fresh subagent for fix or re-review rounds. Always resume the previous one so it retains its working memory. Exception: if `resume_from` fails (subagent expired), launch a fresh one and log a warning.

Prompt:
```
The reviewer found issues. The review_file is at: <review_file>

Read the review_file. Address ALL issues with Status: open — including nits, suggestions, and any style or hint-level feedback. Nothing is too small to fix. Requests that would add a helper, type, config, or extra file for a single current caller may be `wontfix`. Apply findings that ask to delete extra helpers, files, or abstractions.

For each issue, implement the fix, then update the review_file:
- Change Status: open → Status: fixed
- Add a Response field explaining what you changed

You are encouraged to push back on feedback that doesn't make sense, is contradictory, or would make the implementation worse. If you disagree with an issue:
- Set Status: wontfix
- Write a clear, technical explanation of why the reviewer's suggestion is wrong or counterproductive
- Do NOT comply with feedback just to make a reviewer happy — defend good implementation decisions

Append an updated Implementation Summary at the bottom of the review_file.
```

Wait for completion. If it fails, report the error to the user and stop.

Update the saved implementer `subagent_id` with the new one returned.

Report to the user: "Fixes applied. Running parallel re-review (round N)..." where N is the current `round_count` + 1. After re-review (Step 7), the loop returns to Step 5 (Merge & Check).
