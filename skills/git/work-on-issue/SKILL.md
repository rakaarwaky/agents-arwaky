---
name: work-on-issue
description: Create, search, triage, label, assign, and comment on GitHub issues via gh or REST, and take issues from backlog to verified local commits with isolated Orca worktrees and parallel subagents.
when-to-use: Work on one issue ("fix #123"), fix many issues in batch with isolation (1 issue → 1 worktree), audit which open issues can close, or file/search/label/assign/close/reopen an issue.
argument-hint: <issue-number> [<issue-number>...]
disable-model-invocation: true
---

# Work on Issue

End-to-end skill for GitHub issue work: the CRUD mechanics (create, search, view, label, assign, comment, close/reopen, branch-from-issue) and the verify → decide → isolate → implement → verify-again pipeline at batch scale. Unit of isolation is always **1 issue → 1 Orca worktree**. Per-scenario recipes live in `references/`; this file routes between them.

## Global Rules

Rules that apply to every work-on-issue operation. Reference files cite these; they never restate them.

- **Verify before closing**: Never close or skip work from a `status: done` label, an audit date, or a merged PR's `Closes #N` line alone. Verify every claim against the current tree at HEAD.
- **One quiz for all decisions**: Collect all open questions and ask them in one interactive quiz — one question per decision, recommended option first — before implementation. Skip when every remaining issue has a fully determined fix at HEAD.
- **One issue → one worktree**: Unit of isolation is always 1 issue → 1 Orca worktree. Children work only inside their assigned worktree; never touch sibling worktrees or shared state dirs.
- **Build isolation**: Each worktree MUST use its own build artifact directory — shared dirs cause phantom sibling errors and lock/RAM contention.
- **Child scope**: Local commits only (conventional messages); no push, no PR, no tracker writes.
- **Self-report is not evidence**: Re-check each finished child's commits and verification inside that worktree path before reporting what landed.
- **When to use**: Implement one issue, audit many open issues at once, fix a batch with isolation, work a repo carrying filed-audit issues needing per-issue verification, or file/search/label/assign/comment/close/reopen an issue.
- **Prerequisites**: Authenticated with GitHub (see `github-auth`), inside a git repo with a GitHub remote, or specify the repo explicitly. Source the `gh-env.sh` helper for auth and repo detection.
- **Overlap with `pr-babysit`**: Single-issue PR mechanics live in `pr-babysit`. This skill owns the CRUD mechanics plus the verify → decide → isolate → implement → verify-again pipeline end to end.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/step-0-setup.md`](references/step-0-setup.md) | Prerequisites, auth detection, `gh-env.sh` helper sourcing. |
| Step 1 | [`references/step-1-viewing.md`](references/step-1-viewing.md) | List, search, view issues (gh + curl). |
| Step 2 | [`references/step-2-creating.md`](references/step-2-creating.md) | Create an issue, pick a bug/feature template. |
| Step 3 | [`references/step-3-managing.md`](references/step-3-managing.md) | Label, assign, comment, close/reopen, link to PRs, branch from issue. |
| Step 4 | [`references/step-4-triage-bulk.md`](references/step-4-triage-bulk.md) | Issue triage workflow and bulk label/close operations. |
| Step 5 | [`references/step-5-verify-triage.md`](references/step-5-verify-triage.md) | Load and triage: verify every claim at HEAD before closing. |
| Step 6 | [`references/step-6-decision-quiz.md`](references/step-6-decision-quiz.md) | Decision quiz before implementation. |
| Step 7 | [`references/step-7-fanout.md`](references/step-7-fanout.md) | Fan-out setup: 1 issue → 1 Orca worktree → 1 owner. |
| Step 8 | [`references/step-8-build-isolation.md`](references/step-8-build-isolation.md) | Build isolation per worktree. |
| Step 9 | [`references/step-9-waves-verify.md`](references/step-9-waves-verify.md) | Run waves and verify children. |
| Step 10 | [`references/step-10-rebase.md`](references/step-10-rebase.md) | Rebase open branches after a wave merges. |
| Templates | `templates/bug-report.md`, `templates/feature-request.md` | Skeletons for new issues. |
