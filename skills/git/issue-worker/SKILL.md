---
name: issue-worker
description: issue worker: analyze open GitHub issues and take each one from backlog to a PR opened to main — verify at HEAD → decide → 1 issue → 1 Orca worktree → implementer subagent → orchestrator verifies → orchestrator pushes branch + opens a (draft) PR to main → close/reopen the issue per result. Never merges. Takes EXISTING issues to PRs; does not create issues (that is `/issue-maker`'s domain). CRUD recipes (create/search/label/assign/comment/close/reopen) stay as reference only; the spine is verify → decide → isolate → implement → verify → PR.
argument-hint: <issue-number> [<issue-number>...]
disable-model-invocation: true
---

# Issue Worker — issue → PR

End-to-end skill for GitHub issue work: analyze issues to create PRs. The spine is **verify at HEAD → decide → 1 issue → 1 Orca worktree → implementer subagent → orchestrator verifies → orchestrator pushes branch + opens a (draft) PR to main → close/reopen the issue per result**. Per-scenario CRUD recipes (create, search, view, label, assign, comment, close/reopen) live in `references/` as auxiliary recipes — they are not the spine. Unit of isolation is always **1 issue → 1 Orca worktree → 1 PR to main**. This file routes between the spine and the reference recipes.

## Global Rules

Rules that apply to every issue-worker operation. Reference files cite these; they never restate them.

- **Verify before closing**: Never close or skip work from a `status: done` label, an audit date, or a merged PR's `Closes #N` line alone. Verify every claim against the current tree at HEAD.
- **One quiz for all decisions**: Collect all open questions and ask them in one interactive quiz — one question per decision, recommended option first — before implementation. Skip when every remaining issue has a fully determined fix at HEAD.
- **One issue → one worktree → one PR**: Unit of isolation is always 1 issue → 1 Orca worktree → 1 PR to main. Children work only inside their assigned worktree; never touch sibling worktrees or shared state dirs.
- **Build isolation**: Each worktree MUST use its own build artifact directory — shared dirs cause phantom sibling errors and lock/RAM contention.
- **Child scope**: Children edit files only inside their own worktree; children never commit, push, open a PR, or write to the tracker. The **orchestrator** owns push + PR (one PR per issue, draft by default).
- **Self-report is not evidence**: Re-check each finished child's commits and verification inside that worktree path before reporting what landed.
- **PR opens to main; skill never merges**: After a wave verifies, the orchestrator pushes each worktree branch and opens one PR per issue (draft by default; Mergify-style auto-merge is out of scope). `Closes #N` is written only after the PR merges; the skill does not merge.
- **When to use**: Implement one issue, audit many open issues at once, fix a batch with isolation (each to its own PR), work a repo carrying filed-audit issues needing per-issue verification, or file/search/label/assign/comment/close/reopen an issue (reference recipes).
- **Prerequisites**: Authenticated with GitHub (see `github-auth`), inside a git repo with a GitHub remote, or specify the repo explicitly. Source the `gh-env.sh` helper for auth and repo detection.
- **Overlap with `pr-babysit`**: Single-issue PR mechanics live in `pr-babysit`. This skill owns the issue → PR spine end to end (verify → decide → isolate → implement → verify → PR) plus the CRUD reference recipes.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/step-0-setup.md`](references/step-0-setup.md) | Prerequisites, auth detection, `gh-env.sh` helper sourcing. |
| Step 1 | [`references/step-1-viewing.md`](references/step-1-viewing.md) | List, search, view issues (gh + curl). |
| Step 2 | [`references/step-3-managing.md`](references/step-3-managing.md) | Label, assign, comment, close/reopen, link to PRs, branch from issue. |
| Step 3 | [`references/step-4-triage-bulk.md`](references/step-4-triage-bulk.md) | Issue triage workflow and bulk label/close operations. |
| Step 4 | [`references/step-5-verify-triage.md`](references/step-5-verify-triage.md) | Load and triage: verify every claim at HEAD before closing. |
| Step 5 | [`references/step-6-decision-quiz.md`](references/step-6-decision-quiz.md) | Decision quiz before implementation. |
| Step 6 | [`references/step-7-fanout.md`](references/step-7-fanout.md) | Fan-out setup: 1 issue → 1 Orca worktree → 1 owner. |
| Step 7 | [`references/step-8-build-isolation.md`](references/step-8-build-isolation.md) | Build isolation per worktree. |
| Step 8 | [`references/step-9-waves-verify.md`](references/step-9-waves-verify.md) | Run waves, verify children, then orchestrator pushes each worktree branch and opens one PR per issue (draft by default). |
| Step 9 | [`references/step-10-rebase.md`](references/step-10-rebase.md) | Rebase still-open worktree branches onto the default tip after PRs land. |
| Templates | `templates/bug-report.md`, `templates/feature-request.md` | Skeletons for new issues. |

