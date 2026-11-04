---
name: issue-worker
description: "issue worker: analyze open GitHub issues and take each one from backlog to a PR opened to main — Hermes verifies at HEAD and runs the decision quiz, then 1 issue → 1 Orca worktree → Grok Build implements → Hermes verifies → Hermes pushes branch + opens a (draft) PR to main → close/reopen the issue per result. Never merges. Takes EXISTING issues to PRs; does not create issues (that is /issue-maker's domain). CRUD recipes stay as reference only; the spine is verify → decide → isolate → delegate → verify → PR."
argument-hint: <issue-number> [<issue-number>...]
disable-model-invocation: true
---

# Issue Worker — issue → PR

End-to-end skill for GitHub issue work: analyze issues to create PRs. The spine is **verify at HEAD → decide → 1 issue → 1 Orca worktree → Grok Build implements → Hermes verifies → Hermes pushes branch + opens a (draft) PR to main → close/reopen the issue per result**. Per-scenario CRUD recipes (search/view/label/assign/comment/close/reopen/branch) live in `references/grok/` as auxiliary recipes for the per-issue fix passes. Unit of isolation is always **1 issue → 1 Orca worktree → 1 PR to main**.

**All implementation is delegated to Grok Build.** Triage, the decision quiz, verification, and every git/PR/issue operation belong to Hermes (`references/hermes/`). The per-issue implement + verify + rebase mechanics belong to Grok (`references/grok/`), one worktree per issue, `--agent grok`.

## Global Rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build via Orca worktree)**: You never write the fix, run the implementation, or author a regression test yourself. Each `still-broken` issue gets one Orca worktree with `--agent grok`; Grok Build runs the fix pass inside it. No `spawn_subagent` — your only "subagent" is the Grok Build TUI.
- **Verify before deciding (Hermes's job)**: Never close or skip work from a `status: done` label, an audit date, or a merged PR's `Closes #N` line alone. Verify every claim against the current tree at HEAD in Hermes's own tools — this is coordination, not coding, and it stays in the Hermes lane.
- **One quiz for all decisions**: Collect all open questions and ask them in one interactive quiz — one question per decision, recommended option first — before spawning Grok. Skip when every remaining issue has a fully determined fix at HEAD. The user's answers are final and are written into every spawned brief as constraints.
- **One issue → one worktree → one PR**: unit of isolation is always 1 issue → 1 Orca worktree → 1 PR to main. Each Grok session works only inside its assigned worktree; never touch sibling worktrees or shared state dirs.
- **Build isolation**: each worktree MUST use its own build artifact directory — stated in the brief; shared dirs cause phantom sibling errors and lock/RAM contention.
- **One-shot task drop per issue**: one self-contained brief (goal, verified evidence it is still broken at HEAD, constraints, acceptance criteria), dropped once via `orca terminal send`. No mid-run course corrections, no status pings.
- **Self-report is not evidence**: re-check each finished Grok session's commits and verification inside that worktree path before reporting what landed — run the issue's symptom repro and the regression test yourself when the claim is load-bearing.
- **Hermes owns push + PR + issue state**: after a wave verifies, Hermes pushes each worktree branch and opens one PR per issue (draft by default; `--force-with-lease` only). `Closes #N` is written only after the PR merges; the skill never merges.
- **Wave limit**: ≤ 10 concurrent Grok worktrees; wave N+1 spawns after wave N's results arrive.
- **Prerequisites**: authenticated with GitHub (`github-auth`), inside a git repo with a GitHub remote, or specify the repo explicitly.
- **Overlap with `pr-babysit`**: single-issue PR mechanics live in `pr-babysit`. This skill owns the issue → PR spine end to end (verify → decide → isolate → delegate → verify → PR).

## Routing

Each reference file is step-scoped. Global rules above apply throughout; do not restate them in a step file.

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You triage, quiz, spawn Grok per issue, verify, and ship — you never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside an issue's Orca worktree, having just received `/issue-worker implement <N>`. Run the implement + verify + rebase mechanics in `references/grok/` (steps 4–10) — one issue, one worktree, one commit.

### Hermes lane (Steps 0–3)

| Step | Reference                                                                              | Purpose                                                                                                  |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-triage-and-spawn.md`](references/hermes/step-0-triage-and-spawn.md) | Verify claims at HEAD per issue; ask the decision quiz; spawn one Grok worktree per `still-broken` issue and drop the brief |
| 1    | [`references/hermes/step-1-wait-and-verify.md`](references/hermes/step-1-wait-and-verify.md) | Wait for each Grok session; verify commits, code, and re-run the symptom repro in that worktree        |
| 2    | [`references/hermes/step-2-ship-and-close.md`](references/hermes/step-2-ship-and-close.md) | Push each verified branch, open one draft PR per issue; close verified-on-main issues with evidence; rebase still-open branches |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report: verdicts, evidence, PRs, closed issues, failed items, worktree teardown                  |

### Grok lane (Steps 4–10, run by Grok Build per issue)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 4 | [`references/grok/step-4-verify-triage.md`](references/grok/step-4-verify-triage.md) | Load and triage: verify every claim at HEAD before closing. |
| 5 | [`references/grok/step-5-validate.md`](references/grok/step-5-validate.md) | Validate issue state before deciding — rejects stale/fake/duplicate/already-fixed issues. |
| 7 | [`references/grok/step-7-fanout.md`](references/grok/step-7-fanout.md) | Fan-out setup: 1 issue → 1 Orca worktree → 1 owner; child brief contract. |
| 8 | [`references/grok/step-8-build-isolation.md`](references/grok/step-8-build-isolation.md) | Build isolation per worktree. |
| 9 | [`references/grok/step-9-waves-verify.md`](references/grok/step-9-waves-verify.md) | Run waves, verify children (report files changed, mechanism, verification output, commit SHA). |
| 10 | [`references/grok/step-10-rebase.md`](references/grok/step-10-rebase.md) | Rebase still-open worktree branches onto the default tip after PRs land. |
| 1 | [`references/grok/step-1-viewing.md`](references/grok/step-1-viewing.md) | Auxiliary: list, search, view issues (gh + curl). |
| 2 | [`references/grok/step-2-managing.md`](references/grok/step-2-managing.md) | Auxiliary: label, assign, comment, close/reopen, link to PRs, branch from issue. |
| 3 | [`references/grok/step-3-triage-bulk.md`](references/grok/step-3-triage-bulk.md) | Auxiliary: issue triage workflow and bulk label/close operations. |
| 0 | [`references/grok/step-0-setup.md`](references/grok/step-0-setup.md) | Prerequisites, auth detection, `gh-env.sh` helper sourcing. |

