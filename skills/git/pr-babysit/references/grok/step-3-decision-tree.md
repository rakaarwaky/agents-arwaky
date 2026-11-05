# Step 4 — Decision Tree and Auto-Fix Loop

The core per-cycle pass. Runs on every `check` and on every scheduled `/loop` trigger. Single PR, single worktree — no subagent dispatch, no resume, no parallel groups.

## When this file loads

After step 2 (watch CI) reports a red check, or after step 3 (auto-fix) has pushed a fix and needs to re-judge the PR. Runs before step 5 (merge) to confirm the PR is actually ready.

## Inputs

- The PR number, `OWNER`, `REPO` (from step 0)
- The worktree path (created in step 0)
- `stack_type: null` — this skill handles standalone PRs only; if the user's PR is part of a Graphite/GitHub stack, stop and tell them the stack tool owns those

## State

In-memory only (single invocation):

- `last_status` — `"healthy"` / `"pending"` / `"ci_failed"` / `"review_comments"` / `"conflicts"` / `"changes_requested"` / `"error"` / `"ship_blocked"`
- `fix_count` — per-cycle counter, observational only; does not gate or skip fixes
- `PROCESSED_THREAD_IDS`, `REPLIED_UNRESOLVED_THREAD_IDS`, `REPLY_FAILED_THREAD_IDS`, `FIX_FAILED_THREAD_IDS` — thread lifecycle lists

Persist `last_status` and `fix_count` to `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json` when the cycle ends.

## Worktree initialization

The subagent worktree from step 0 is the working boundary. `git fetch origin` before the first ref-sensitive operation; `has_fetched` flag guards repeat fetches.

```bash
git fetch origin || (sleep 2 && git fetch origin) || FETCH_FAILED=true
```

If `FETCH_FAILED`, set `last_status` to `"error"`, log both attempts, skip all git operations for this cycle.

## Query the PR

```bash
gh pr view <number> --json state,mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,headRefName,baseRefName
```

On network/rate-limit/auth error: log, set `last_status` to `"error"`, continue to next decision branch.

## Decision order

Evaluate in this order. A branch that matches does not stop evaluation — later branches still run. Only MERGED/CLOSED is terminal.

1. **MERGED or CLOSED** — set `removed: true`, stop.
2. **CONFLICTING / DIRTY** — resolve conflicts (below). Continue to CI and review checks in the same cycle.
3. **CI FAILED** — auto-fix each failed check (below). Continue.
4. **Always**: (a) changes-requested review-level body, (b) unresolved inline threads from humans and bots, (c) new bot/automated findings — regardless of 2–3.
5. **Terminal status** — from the state of CI + reviews: `"healthy"`, `"pending"`, `"ci_needs_attention"`, or fallback `"error"`.

## Conflict resolution

`mergeable` is `"CONFLICTING"` or `mergeStateStatus` is `"DIRTY"`.

```bash
git checkout -B <headRefName> origin/<headRefName>
git rebase origin/<baseRefName>
```

Read each conflicted file in full, understand both sides, combine changes, remove all conflict markers, verify the file is syntactically valid.

```bash
git add <resolved_files>
git rebase --continue
```

After the rebase completes, verify the build passes (`cargo check`, `npx tsc --noEmit`, `python -m py_compile`, etc.). Then push:

```bash
git push --force-with-lease
```

Post a comment:

```bash
gh pr comment <number> --body "Automated fix: resolved merge conflicts and rebased."
```

Set `last_status` to `"conflicts"`. Increment `fix_count`.

## CI auto-fix loop

`statusCheckRollup` has a `FAILURE` or `ERROR` check.

```bash
gh pr checks <number> --json name,state,link
# parse <run_id> from link, or:
gh run list --branch <headRefName> --json databaseId,name,conclusion \
  --jq '.[] | select(.conclusion == "failure")'
gh run view <run_id> --log-failed 2>/dev/null | tail -100
```

For each failed check:

1. Read the log. Load [step-3-troubleshoot.md](step-3-troubleshoot.md) if the failure is ambiguous (flake vs real).
2. Fix the code in the worktree.
3. Commit and push:
   ```bash
   git add -A
   git commit -m "fix: address CI failure in <check_name>"
   git push
   ```
4. Set `last_status` to `"ci_failed"`. Increment `fix_count` once per successful check fix.

## Changes requested (review-level body)

`reviewDecision` is `"CHANGES_REQUESTED"`.

```bash
NO_COLOR=1 gh api repos/{OWNER}/{REPO}/pulls/{number}/reviews \
  --jq '.[] | select(.state == "CHANGES_REQUESTED")'
```

Read the review body (not inline threads — those are handled below). If actionable:

1. Checkout the branch, fix in code.
2. Commit and push.
3. Post a summary comment: `gh pr comment <number> --body "Automated fix: addressed review feedback."`

Set `last_status` to `"changes_requested"`. Increment `fix_count`.

## Unresolved review threads (humans and bots)

**Every** unresolved thread is evaluated. No thread is skipped because its author is a bot.

### Fetch

`gh api graphql` injects ANSI codes even when piped — set `NO_COLOR=1` and strip escapes with `sed`. Write output under the OS temp dir from `host.py scratch`, not bare `/tmp`:

```bash
THREADS_FILE="<scratch_dir>/pr_review_threads.json"
CURSOR=""
ALL_THREADS="[]"
while true; do
  AFTER_ARG=""
  [ -n "$CURSOR" ] && AFTER_ARG="-f cursor=$CURSOR"
  PAGE=$(NO_COLOR=1 gh api graphql -f owner="<OWNER>" -f name="<REPO>" -F number=<number> $AFTER_ARG \
    -f query='query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          reviewThreads(first: 50, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes { id isResolved comments(last: 100) { nodes {
              author { __typename login }
              path line body databaseId url
            } }
          }
        }
      }
    }' | sed 's/\x1b\[[0-9;]*m//g')
  PAGE_NODES=$(echo "$PAGE" | jq '.data.repository.pullRequest.reviewThreads.nodes')
  ALL_THREADS=$(echo "$ALL_THREADS" "$PAGE_NODES" | jq -s '.[0] + .[1]')
  HAS_NEXT=$(echo "$PAGE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  [ "$HAS_NEXT" = "true" ] || break
  CURSOR=$(echo "$PAGE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
done
echo "$ALL_THREADS" > "$THREADS_FILE"
```

`comments(last: 100)` — not `first: 10` — so `nodes[-1]` is the newest comment. If `hasPreviousPage` is true, paginate the comments connection until the newest is included.

### Filter

`isResolved == false`. Author-agnostic: humans, `Bot` accounts, `[bot]` logins, Cursor, Copilot, Semgrep, Dependabot, Renovate, Graphite — all in scope.

### Reply and resolve

```bash
resolve_review_thread() {
  local out
  if ! out=$(NO_COLOR=1 gh api graphql -f query='
  mutation($id: ID!) {
    resolveReviewThread(input: {threadId: $id}) { thread { isResolved } }
  }' -f id="$THREAD_ID"); then
    return 1
  fi
  echo "$out" | sed 's/\x1b\[[0-9;]*m//g' | jq -e '.data.resolveReviewThread.thread.isResolved == true'
}

reply_and_resolve() {
  local reply_ok=false
  if NO_COLOR=1 gh api graphql -f query='
  mutation($threadId: ID!, $body: String!) {
    addPullRequestReviewThreadReply(input: {
      pullRequestReviewThreadId: $threadId
      body: $body
    }) { comment { url } }
  }' -f threadId="$THREAD_ID" -f body="$REPLY_BODY"; then
    reply_ok=true
  elif NO_COLOR=1 gh api repos/{OWNER}/{REPO}/pulls/{number}/comments/${DATABASE_ID}/replies \
        -X POST -f body="$REPLY_BODY"; then
    reply_ok=true
  fi
  [ "$reply_ok" = "true" ] || {
    echo "Reply failed for ${THREAD_ID}; track in REPLY_FAILED_THREAD_IDS; leave open for next cycle."
    REPLY_FAILED_THREAD_IDS+=("$THREAD_ID")
    return 1
  }
  if resolve_review_thread || resolve_review_thread; then
    PROCESSED_THREAD_IDS+=("$THREAD_ID")
    return 0
  fi
  echo "Reply succeeded but resolve failed for ${THREAD_ID}; track in REPLIED_UNRESOLVED_THREAD_IDS."
  REPLIED_UNRESOLVED_THREAD_IDS+=("$THREAD_ID")
  return 1
}
```

### Per-thread decision

- **Fixable** — the comment points at a bug, requests a refactor, suggests an improvement:
  1. Fix the code in the worktree, commit, push.
  2. `COMMIT_SHA=$(git rev-parse HEAD)`
  3. `REPLY_BODY="Addressed in ${COMMIT_SHA}: <brief description>"`
  4. Call `reply_and_resolve`. Increment `fix_count`.

- **Question / out-of-scope / false positive** — the current code is correct, or the suggestion is out of scope:
  1. Reply with a substantive technical explanation of why no code change is needed.
  2. Call `reply_and_resolve`.

- **Never** reply with "Will fix", "Acknowledged", "Acked", "Noted", "Good point", "Makes sense", "Thanks for the feedback" — or any bare acknowledgment or deferral to a follow-up PR.

- **Bot slash commands** — only when that bot documents them: `semgrep-code-scan` accepts `/fp`, `/ar`, `/other`. Cursor Bugbot and Copilot have none; use the normal GraphQL reply + resolve path.

### Thread lifecycle guard

Before posting a new reply on a thread:

- `THREAD_ID` in `FIX_FAILED_THREAD_IDS` or `REPLY_FAILED_THREAD_IDS` → skip for the rest of this cycle.
- `THREAD_ID` in `REPLIED_UNRESOLVED_THREAD_IDS` → call `resolve_review_thread` only (no second reply).
- Newest comment is already a *closing* babysitter reply (fix SHA or FP/OOS/clarification) → `resolve_review_thread` only.
- Newest comment is a prior-cycle "will address next cycle" note → **not** closing; apply the fix (or substantive reply) this cycle, then SHA reply + resolve.

### Bot and automated comments

Run alongside the human-thread pass. Automated reviewers re-run after new pushes and can leave new unresolved threads.

**Identity** — treat as automated when any of:

- GraphQL `author.__typename == "Bot"`, or REST `user.type == "Bot"`
- `author.login` / `user.login` ends with `[bot]`
- Known logins: `cursor` / `cursor[bot]`, `copilot` / `copilot-pull-request-reviewer`, `github-actions`, `renovate`, `dependabot`, `semgrep-code-scan`, `graphite-app`

**Strip markup before judging.** Automated reviewers wrap the real finding in HTML, HTML comments, and vendor footers. Dump the raw body to a file, strip `<!-- … -->`, strip HTML tags, drop only **trailing** vendor chrome lines — never a mid-body "Generated by" DOTALL cut.

```python
# <scratch_dir>/strip_bot_body.py
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
text = re.sub(r"<[^>]+>", " ", text)
lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
footer = re.compile(
    r"^(Reviewed by\b.*Bugbot|Fix in Cursor\b|Configure here\b)",
    re.I,
)
while lines and (not lines[-1] or footer.match(lines[-1])):
    lines.pop()
print(re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip())
```

**Also fetch** bot review bodies and issue comments:

```bash
NO_COLOR=1 gh api --paginate repos/{OWNER}/{REPO}/pulls/{number}/reviews \
  --jq '.[] | select(.user != null and (.user.type == "Bot" or (.user.login != null and (.user.login | test("\\[bot\\]$|^(cursor|copilot|semgrep-code-scan|graphite-app)$"))))) | {user: .user.login, state, body, submitted_at, html_url}'

NO_COLOR=1 gh api --paginate repos/{OWNER}/{REPO}/issues/{number}/comments \
  --jq '.[] | select(.user != null and (.user.type == "Bot" or (.user.login != null and (.user.login | test("\\[bot\\]$|^(cursor|copilot|semgrep-code-scan|graphite-app)$"))))) | {user: .user.login, body, created_at, html_url}'
```

`--paginate` is required: without it only the first page is returned and newer bot summaries on busy PRs are missed.

A summary lists a finding as open → verify against the thread's `isResolved`. Trust the thread, not the aggregate. A summary finding with no matching thread → look harder (pagination, HTML-wrapped body, more comment pages) before ignoring.

**Human conversation comments.** Paginate `GET repos/{OWNER}/{REPO}/issues/{number}/comments` with no bot filter. Skip a comment when any of:

- author is the PR author
- body starts with `Addressed in ` or `Automated fix:`
- a later closer from the PR author or the authenticated `gh` user already exists

Remaining comments are open findings. Fix or reply substantively. Then post `Addressed in ${SHA}: ...` on the conversation tab. Do not use `Automated fix:` for that closer.

**Never mark `healthy`** while any unresolved bot or human thread remains. New findings posted after this cycle's push are picked up on the next scheduled check — that is expected.

## Worktree recovery after a failed code-change attempt

Run this before any further edit/commit/push on the same PR. `git add -A` is mandatory on success and will otherwise stage leftover partial edits.

```bash
# Abort in-progress rebase first.
git rebase --abort 2>/dev/null || true
git merge --abort 2>/dev/null || true

CURRENT=$(git branch --show-current)
if [ -n "$CURRENT" ] && [ "$CURRENT" != "<headRefName>" ]; then
  echo "HEAD is ${CURRENT}, not <headRefName>; skip reset (would rewrite ${CURRENT})."
  git clean -fd
elif <restack completed and only push failed>; then
  git restore --staged --worktree . 2>/dev/null || true
  git clean -fd
else
  git reset --hard "origin/<headRefName>"
  git clean -fd
fi
```

Do **not** use `git clean -x` / `-xfd` — that wipes ignored build artifacts.

After a failed review-thread code change: append `THREAD_ID` to `FIX_FAILED_THREAD_IDS`. Do not reply. Do not increment the counter. Continue to the next thread.

## Cancelled / timed-out CI checks

`statusCheckRollup` has a check with conclusion `CANCELLED`, `TIMED_OUT`, `STARTUP_FAILURE`, or `STALE` (and no `FAILURE`/`ERROR`). Set `last_status` to `"ci_needs_attention"`. Do not attempt fixes — these need manual re-triggering or investigation.

## Checks pending

Any check with status `IN_PROGRESS` or `QUEUED` (and no failure/cancel). Set `last_status` to `"pending"`. Do **not** let pending CI block action on already-identified issues — human review comments, bot/automated findings, and known failures from prior runs must still be addressed while checks are in progress.

## All green

All of:

- `mergeable` is `"MERGEABLE"`
- No check has conclusion `FAILURE`, `ERROR`, `CANCELLED`, `TIMED_OUT`, `STARTUP_FAILURE`, or `STALE`
- `reviewDecision` is not `"CHANGES_REQUESTED"`
- No unresolved review threads (human or bot) — confirmed by the passes above
- No open conversation-tab comment without a later `Addressed in ` closer

Set `last_status` to `"healthy"`. No action. The PR is ready to merge. If `--ship` is active, load [step-4-merge.md](step-4-merge.md).

## Last-status precedence

When multiple sections set `last_status` in one cycle, the last section to execute wins. Review-related statuses (`review_comments`, `changes_requested`) run after CI/conflict statuses and take priority.

## Cleanup

After the decision tree completes, remove the scratch dir with `host.py cleanup`. Do not `rm -f`.
