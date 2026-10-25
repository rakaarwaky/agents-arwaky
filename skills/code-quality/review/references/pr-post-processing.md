# PR-mode post-processing

GitHub PR post-processing for Step 3 (PR mode) of `review`: read the reviewer output, walk the diff, build and post the review payload, and handle errors. The orchestrator coordinates only — all findings are authored by the reviewer subagent.

## Read the reviewer output

1. Read `<review_file>` via `read_file` and parse it into a structured representation:
   - Extract the `## Summary` section — everything after the `## Summary` heading and before the next `## ` heading.
   - Extract each issue by matching heading lines against `^### Issue \d+ -- Severity: (bug|suggestion|nit)$` (same regex as Step 3 Main/Local/Branch mode). For each matched block, capture:
     - `severity` — the captured group from the heading regex
     - `file` and `line` — parsed from the `- File: path:line` field. If `:line` is missing, the issue cannot become an inline comment; it must be promoted to the body.
     - `description` — from the `- Description:` field
     - `suggestion` — from the `- Suggestion:` field (may be empty)

   **Early-exit on zero issues**: behavior depends on `approve` / `submit`:
   - **`approve` is false and `submit` is false (default):** do NOT walk the diff, build a payload, or post. Print "Reviewer found no issues on PR #<pr_number>. No PENDING review created." Then run no-reviewer cleanup and produce the Final report.
   - **`submit` is true (and `approve` is false):** do not post an empty COMMENT review. Print "Reviewer found no issues on PR #<pr_number>. No COMMENT review created." Then run no-reviewer cleanup and produce the Final report.
   - **`approve` is true:** do NOT skip — the user asked to approve. Build a payload with `comments: []` and a `body` carrying the `## Summary` and the (zero) issue counts, then post it with `"event": "APPROVE"` so the approval still happens. Continue to the diff walk (the diff walk produces an empty inline-comment set, which is fine).

## Walk the diff for valid inline positions

2. Read `<diff_file>` via `read_file` and walk it to determine which `(file, line)` pairs are present on the RIGHT side of any hunk. The line is on the RIGHT side when:
   - It is an added line (prefix `+`, but not the `+++ b/...` header line), OR
   - It is a context line (prefix ` `).

   Walk the diff file by file:
   - Each file section starts with `+++ b/<path>` (treat `+++ /dev/null` as a deletion — skip).
   - Within a file, each hunk starts with `@@ -<old>[,<oldcount>] +<new>[,<newcount>] @@`. The `,<count>` parts are optional and default to `1` when omitted (so `@@ -42 +42 @@` is a valid single-line hunk that `git diff` and `gh pr diff` both emit). A regex like `^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@` matches both forms; capture `<new>` from the second group. Reset the right-side line counter to `<new>`. (The regex is intentionally unanchored at the end — real diffs frequently carry trailing context after the second `@@`, e.g. `@@ -10,5 +15,3 @@ def my_function():`, and `re.match` succeeds on the prefix without a `$` anchor. Do NOT add `$`; it would reject every hunk header that includes a function/class hint.)
   - Walk the hunk body. For ` ` (context) and `+` lines (excluding `+++` headers), record the current right-side line and increment the counter. For `-` lines (excluding `---` headers), do not increment the right-side counter.
   - Lines starting with `\ ` (a literal backslash followed by a space) are diff metadata, not file content — e.g., `\ No newline at end of file`. Skip them: do not increment the right-side counter, and do not contribute a `(file, line)` pair.

   Build a set of `(file, line)` pairs.

## Partition and build the payload

3. Partition the parsed issues into two groups:
   - **Inline comments**: issues whose `(file, line)` is in the diff set.
   - **Promoted to body**: issues whose `(file, line)` is missing or not in the diff set.

4. Build the JSON payload via the `write` tool, saving to `<pending_review_payload>`:

   ```json
   {
     "commit_id": "<head_sha>",
     "body": "<assembled body, see below>",
     "comments": [
       {
         "path": "src/foo.rs",
         "line": 42,
         "side": "RIGHT",
         "body": "**[bug]** description text\n\n**Suggestion:** suggestion text"
       }
     ]
   }
   ```

   **The `event` field is conditional on `approve` / `submit`:**
   - If `approve` is false and `submit` is false (default): do NOT include `event`. Omitting it causes the GitHub API to create the review in PENDING state — the user reviews and submits it through the GitHub UI.
   - If `submit` is true (and `approve` is false): add `"event": "COMMENT"` to the dict. The single `POST .../reviews` call publishes the inline comments + body immediately without approving the PR.
   - If `approve` is true: add `"event": "APPROVE"` to the dict. The single `POST .../reviews` call then publishes the inline comments + body AND approves the PR in one shot.

   The top-level `body` is constructed as:

   ```
   ## Summary

   <verbatim text of the ## Summary section from the review_file>

   ## Issue counts by severity

   - bugs: <X>
   - suggestions: <Y>
   - nits: <Z>

   <if any promoted issues exist, append:>
   ## Issues outside the diff

   These findings reference lines that are not present in the diff and could not be posted as inline comments:

   - **[severity]** file:line -- description
     - **Suggestion:** suggestion text
   <repeat for each promoted issue>
   <end if>
   ```

   Each inline comment body has the form `**[severity]** description\n\n**Suggestion:** suggestion`. If the suggestion is empty, drop the suggestion line.

   **Construct the payload as structured data, then persist it with the `write` tool as valid JSON.** Do not concatenate JSON strings by hand. Do not use a `python <<'PY'` heredoc because `<<` is reserved in PowerShell. Serialize the in-memory object and pass the resulting JSON as the `content` argument for `<pending_review_payload>`. The default object has no `event`; add it only for `submit` or `approve` as specified above.

## Post the review

5. Post the review.

   **Self-approval pre-check (`approve` only):** fetch the PR author with `gh pr view <target> --json author` and the authenticated user with `gh api user`. Parse both JSON responses yourself, or use `--jq` as part of those `gh` commands. If the logins are equal, stop before posting, explain that GitHub forbids self-approval, preserve `<review_file>`, and run failed-post cleanup for the other artifacts. Do not send a knowingly invalid APPROVE request.

   Post with `gh api "repos/<owner>/<repo>/pulls/<pr_number>/reviews" -X POST --input <pending_review_payload>`. Inline the validated owner, repo, PR number, payload path, `<post_file>`, and `<post_error_file>` in a shell-appropriate `run_terminal_command` call that captures stdout and stderr.

6. **Error handling**: if the `gh api` call exits non-zero, surface the captured stderr verbatim to the user along with the HTTP status code (parseable from `gh api`'s stderr message). Do not retry. Common cases by status:
   - **422 Unprocessable Entity**: comments reference lines outside the diff (the diff-line filter missed something, e.g., the reviewer hallucinated a file path), `commit_id` is stale (the PR was force-pushed between Step 1 and now), or the `side` value was rejected. When `approve` is true, a 422 can ALSO mean GitHub refused to let you approve your own PR — if the stderr says the author cannot approve their own pull request, surface that specific cause clearly (you cannot approve a PR you authored; ask a different reviewer or drop `--approve`) and keep the review file.
   - **403 Forbidden**: authenticated user lacks permission to comment on the PR (read-only collaborator on the repo, archived repo).
   - **404 Not Found**: PR does not exist (the user passed a wrong number, or the URL is in a private repo the user cannot see).
   - **5xx**: GitHub-side outage or transient failure.

   On any error, also keep `<review_file>` on disk (skip the PR-mode review_file deletion in Step 4) so the user can see what would have been posted and either re-run with corrected inputs or submit the notes through some other channel. Mention the preserved path in the error message.

7. On success, the message depends on `approve` / `submit`. In all cases the response is parsed for the review `id`, which is recorded in the Final report; the `html_url` field is not used.

   **`approve` is false and `submit` is false (PENDING):** the user-facing pending-review URL is the PR Files tab, where pending reviews surface and where the "Finish your review" / "Submit review" button lives:

   ```
   https://github.com/<owner>/<repo>/pull/<pr_number>/files
   ```

   Construct this URL from the already-validated `owner`, `repo`, and `pr_number` — do NOT use the `html_url` field from the GitHub response. The response's `html_url` points at a deep link to the review object that does not surface the submit button as cleanly as the Files tab.

   Print to the user as a structured block (not a wall of text):

   ```
   A PENDING review has been created on PR #<pr_number>.
   - Inline comments: <N>
   - Body findings (outside the diff): <M>
   - Submit at: https://github.com/<owner>/<repo>/pull/<pr_number>/files
     (scroll to "Finish your review" -> click "Submit review").
   Until you submit, the comments are visible only to you.
   ```

   **`submit` is true (COMMENTED):** the review was submitted (published) as a COMMENT review — comments are visible immediately, the PR is not approved, and there is no PENDING state. Print the PR URL (not the Files-tab submit link):

   ```
   Submitted a COMMENT review on PR #<pr_number> -- comments are visible immediately.
   - Inline comments: <N>
   - Body findings (outside the diff): <M>
   - PR: <pr_url>
   ```

   **`approve` is true (APPROVED):** the review was submitted (published) and the PR approved in the same call — there is no PENDING state to submit. Print the PR URL instead of the Files-tab submit reminder:

   ```
   Submitted an APPROVING review on PR #<pr_number> -- the PR is now approved.
   - Inline comments: <N>
   - Body findings (outside the diff): <M>
   - PR: <pr_url>
   ```
