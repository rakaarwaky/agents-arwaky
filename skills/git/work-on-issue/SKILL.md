---
name: work-on-issue
description: Triage, decide, and implement one or many issues with isolated worktrees and verified results. Use when fixing a GitHub issue, working a batch of issues, auditing which open issues can close, or fanning issues out to parallel worktrees and subagents.
when-to-use:
  - work on issue
  - fix issue
  - fix many issues
  - batch fix issues
  - fan out issues
  - parallel worktrees for issues
  - audit open issues
  - which issues can close
argument-hint: <issue-number> [<issue-number>...]
metadata:
  tags:
    - GitHub
    - Issues
    - Worktrees
    - Delegation
    - Triage
  related_skills:
    - github-issues
    - github-pr-workflow
    - systematic-debugging
    - orca-cli
---

# Work on Issue

End-to-end pipeline for taking issue work from backlog to verified local commits.
Works for a single issue or a batch. Unit of isolation is always **1 issue → 1 Orca worktree**.

Worktrees are Orca-managed via `orca worktree create`. Prefer `orca-cli` for create,
status, terminal drive, and retire. Use raw `git worktree` only when Orca is unavailable,
and say so in the report.

Default until the user says otherwise: subagents commit locally only — no push, no PR.
After a wave of PRs merges, rebase every still-open branch before CI re-runs — see
[`references/wave-rebase.md`](references/wave-rebase.md).

## When to Use

- Implement one issue ("fix #123", "work this issue").
- Audit many open issues at once ("which open issues can be closed").
- Fix a batch with isolation ("1 issue 1 worktree", parallel subagents).
- A repo carries filed-audit issues needing per-issue verification against current HEAD.

For single-issue PR discipline (duplicate sweeps, regression sabotage runs), see
`github-pr-workflow`'s "Taking an Issue to a PR" section. This skill owns the
**verify → decide → isolate → implement → verify-again** pipeline, especially at batch scale.

## Phase A — Load and triage

Never close or skip work from a `status: done` label, an audit date, or a merged PR's
`Closes #N` line alone. GitHub can silently fail to close issues a PR body declares while
the fix itself did land. Verify every claim against the current tree.

1. Dump open issues once:
   `gh issue list --state open --limit 300 --json number,title,body,labels,updatedAt --jq '.[] | "### #\(.number)\n\(.title)\n\(.body)\n"' > /tmp/issues.md`
2. Check per-issue state: `gh issue view N --json state,closed` — OPEN despite a merged
   `Closes #N` means the closer didn't fire. Still verify the fix by code inspection before
   closing manually with an evidence comment.
3. Verify every claim at HEAD: grep the exact file:line the issue cites. Text still matching
   the code = still valid, keep open. A fix may have landed in an unrelated PR:
   `git log --oneline --since <issue-date> -- <path>`.
4. Cross-references when `gh` is old and rejects newer fields (the error prints valid ones):
   `gh api repos/{o}/{r}/issues/N/timeline --paginate --jq '[.[]|select(.event=="cross-referenced")|.source.issue.number]|unique'`
   and grep `gh pr list --state merged --json number,body` for `Closes #N`.
5. Close only verified ones, each with a comment stating the evidence (file:line or command
   output).

Full command recipes: [`references/triage-verification.md`](references/triage-verification.md).

## Phase B — Decision quiz before implementation

Issues the code cannot answer (versioning policy, whether to enforce a process gate, a bug
whose fix may already be in main) need the user's decision, not a guess. Collect **all**
open questions and ask them in **one** interactive quiz: one question per decision,
recommended option first, choices concrete enough to execute directly from the answer.
Do not start implementation before the quiz is answered.

Skip this phase when every remaining issue has a fully determined fix at HEAD.

## Phase C — Fan-out setup: 1 issue → 1 Orca worktree → 1 owner

Resolve the Orca CLI once (`orca-cli` skill): `$ORCA_CLI_COMMAND`, else `orca-dev` in a dev
checkout, else `orca-ide` on Linux outside Orca, else `orca`. Prefer `--json`.

```bash
ORCA repo list --json
# capture repoId for this repository
```

Create all worktrees from the repo default base in one loop. Independent issue work uses
`--no-parent` and omits `--base-branch` so Orca uses the repo default:

```bash
ORCA worktree create --repo id:<repoId> --name issue-N --no-parent --json
```

To spawn the owner in the same call, add `--agent <id> --prompt "<child brief>"`. For a
single issue you implement yourself, omit `--agent` and open a shell/agent later.

Defaults (override only when the user names different options):

| Knob | Default |
| --- | --- |
| Worktree manager | Orca (`worktree create` / `set` / `rm`) |
| Lineage | `--no-parent` for independent issue work |
| Name / selector | `issue-N`; selector `path:<absPath>` or full `id:<repoId>::<path>` |
| Branch | Orca default from repo base ref (do not base on the current feature branch) |
| Isolation | one build artifact dir per worktree — see [`references/isolation-recipes.md`](references/isolation-recipes.md) |
| Wave size | ≤ concurrency limit (typically 10) |
| Child scope | local commits only; no push, no PR, no tracker writes |

Write decisions + per-issue evidence to a session state file the children can read
(e.g. `.agents/session-notes.md`). It is the source for every child's context — children
see nothing else of this conversation.

When driving an already-running agent terminal: wait for TUI idle before send.

```bash
ORCA terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
# only when satisfied: true
ORCA terminal send --terminal <handle> --text "<child brief>" --enter --json
```

Every child brief must state:

- Work **only** inside the assigned worktree; never touch sibling worktrees or shared state dirs.
- Use **per-worktree build isolation** (own artifact/cache dir; never the repo-shared one).
- Targeted checks only (`<tool> check/test -p <package>` or the language equivalent); never
  workspace-wide gate scripts — they serialize and slow every sibling.
- Local commits allowed (conventional messages); **no push, no PR, no tracker writes**.
- Close the report with: files changed, mechanism, verification command + real output, commit sha.

For "verify first, fix if still broken" issues, the child brief asks for a verdict
(`fixed-on-main` / `still-broken`) plus the regression test pinning the behavior — never for
issue closure (the parent decides closure).

## Phase D — Build isolation

Each worktree MUST use its own build artifact directory — shared dirs cause phantom
sibling errors and lock/RAM contention, and a cold-dir retry never falls back to the
shared dir. Rationale plus setup recipes for Cargo, Node, and Python:
[`references/isolation-recipes.md`](references/isolation-recipes.md).

## Phase E — Run waves and verify children

Wave N+1 spawns after wave N's results arrive. Stacking all waves at once multiplies
isolation contention.

A child's summary is a self-report, not evidence. For each finished child, inside **its**
worktree:

1. `git log --oneline <default>..HEAD` and `git status` — clean tree, expected commits only.
2. Read the changed code at the cited file:line.
3. Re-run the key test yourself when the claim is load-bearing (e.g. "already fixed on main").
4. Only then report what landed to the user.
5. When the issue is done and ready for review, mark the Orca worktree:
   `ORCA worktree set --worktree path:<WT> --workspace-status in-review --json`.

Scan a worktree by `cd`ing **into** Orca's checkout path (`ORCA worktree show --worktree
id:<repoId>::<path> --json` → path). Running checkers against a worktree path from the
repo root often produces phantom violations from broken relative paths.

## Phase F — Rebase open work after merges

After a wave of PRs lands on the default branch, rebase every still-open branch onto the
new tip before letting CI re-run. A stale base fails self-lint and format against
already-merged code, and the fix is a one-command rebase.

Rebase **one** branch at a time and confirm `git status` is clean before force-pushing — a
blind rebase-and-force-push loop across worktrees leaves dirty rebase states that block the
next wave.

Sibling-PR conflict shape, stale-CI diagnosis, and the rebase checklist:
[`references/wave-rebase.md`](references/wave-rebase.md).

## Completion checklist

- [ ] Every candidate issue verified against HEAD, or closed with evidence comment.
- [ ] All non-code decisions answered in one quiz (or none needed).
- [ ] One Orca worktree per issue (`worktree create --no-parent`, json id captured).
- [ ] Each child used isolated build artifacts; no shared-target fallback.
- [ ] Each child's commits and verification re-checked in that worktree path.
- [ ] User report cites files, mechanism, and real command output — not child self-reports.
- [ ] Finished worktrees marked `--workspace-status in-review` (or retired when done).
- [ ] If PRs merged mid-batch: remaining branches rebased onto current default tip.

## Overlap note

Single-issue triage CRUD (create, label, assign, comment) lives in `github-issues`.
Single-issue PR mechanics live in `github-pr-workflow`. This skill owns the
verify → decide → isolate → implement → verify-again pipeline end to end.
