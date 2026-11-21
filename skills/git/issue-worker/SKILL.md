---
name: issue-worker
description: "issue → PR: analyzes and groups open GitHub issues, verifies claims at HEAD, asks user decisions via quiz, isolates work in Orca worktrees, delegates implementation to new Grok Build session(s) via /implement, verifies fixes, and pushes draft PRs. Unified flow for Hermes and Grok with work and setup lanes."
when-to-use: "Use when resolving open GitHub issues into PRs (/issue-worker work <latest|oldest> <N> or /issue-worker work <issue-numbers>), setting up a repository for issue tracking and event automations (/issue-worker setup <repo> or /issue-worker setup add|remove <repo>), triaging and grouping issues by subsystem, verifying bug reproduction at HEAD, delegating fixes to Grok Build via /implement in Orca worktrees, or opening draft PRs. Never creates issues (handled by /issue-maker) and never auto-merges."
argument-hint: "<work|setup|sweep> [<latest|oldest> <N> | <issue-numbers> | <repo>]"
---

# Issue Worker — issue → PR

End-to-end workflow for managing repository issues and resolving open GitHub issues into draft pull requests. Operates in three distinct lanes: `work` (parse issue hints, verify claims at HEAD, group into cohorts, delegate implementation to Grok Build in isolated Orca worktrees, verify fixes, and open draft PRs), `setup` (register repository in `repo.json`, audit issue tracking capability, configure standard triage labels, and register repository event filters in Orca automations), and `sweep` (nightly background pass that re-verifies stale issues at HEAD, groups queueable issues into /implement cohorts, and opens draft PRs). Never merges.

## Rules

| ID | Rule | Check |
|----|------|-------|
| R1 | **Unified orchestrator flow.** Orchestration logic is identical whether executed by Hermes or Grok: the orchestrator coordinates issue resolution, triage, grouping, worktree management, verification, and PR creation; all implementation is delegated to new Grok Build session(s) via `/implement`. | Confirm caller orchestrates and spawns new Grok sessions in Orca worktrees without lane divergence. |
| R2 | **Verify at HEAD before deciding.** Never trust issue labels, audit dates, or commit message claims alone. Inspect the cited file:line at HEAD and check git log for existing fixes before planning fixes. Close `fixed-on-main` issues immediately with concrete evidence comments. | Verified code inspection or reproduction output documented prior to scheduling implementation. |
| R3 | **Interactive decision quiz.** If open ambiguities or architectural decisions exist across issues, collect all questions into a single interactive quiz with recommended options first before implementation. | All unresolved questions presented in a single quiz; user choices recorded as brief constraints. |
| R4 | **Issue grouping and isolation.** Actionable issues are grouped into cohorts based on shared files, subsystems, or root causes for a single `/implement` pass. Disjoint or conflicting issues are strictly isolated into separate worktrees. | Cohort groupings documented with shared file justification; disjoint issues assigned distinct worktrees. |
| R5 | **Orchestrator-implementer separation.** The orchestrator drives coordination and never edits repo code directly. Each implementation group is delegated to a new Grok session running `/implement` in an isolated Orca worktree. | Zero direct code commits on orchestrator branch; implementation confined to child Grok sessions in worktrees. |
| R6 | **Build isolation per worktree.** Each worktree maintains dedicated build artifact and cache directories (e.g. `CARGO_TARGET_DIR`, `.venv`, isolated cache dirs) to avoid concurrency locks and cache corruption. | Worktree configuration verifies dedicated isolated target/cache paths. |
| R7 | **Independent verification.** A child Grok session's summary is a self-report. The orchestrator independently verifies file:line changes, confirms clean git status, and re-executes reproduction and test commands in the worktree. | Reproduction command re-executed and exit code 0 confirmed inside worktree before marking verified. |
| R8 | **Safe push and draft PRs.** Pushes use `git push --force-with-lease origin <branch>` and open draft PRs via `gh pr create --draft`. PR descriptions explicitly cite all grouped issues. Auto-merge is forbidden. | Push uses `--force-with-lease`; PR is created in draft mode referencing all cohort issues. |
| R9 | **Concurrency and wave ceilings.** Maximum concurrent worktrees ≤ 10. Groups beyond the wave limit execute in subsequent waves after active worktrees complete. | Active concurrent worktrees do not exceed 10. |
| R10 | **Worktree teardown & final report.** Verified worktrees are marked `in-review` during inspection, then retired via `orca worktree rm` after push and PR creation. Orchestrator synthesizes a comprehensive final report. | Worktrees cleaned up via `orca worktree rm`; final summary reports all issues, groups, and PRs. |
| R11 | **Zero-issue graceful halt.** If the repository has issues disabled, contains zero open issues, or no issues match the query, report the exact status cleanly, spawn zero worktrees, and halt without error. Suggest `/issue-maker` when spec docs exist. | Query returns zero matching issues or issues disabled; run halts immediately with clean status. |
| R12 | **Repository watchlist enforcement.** Only repositories registered in `repo.json` (`/home/raka/.agents/develop/repo.json`) are processed in the `work` lane. Unregistered repositories must first be set up via the `setup` lane. | Verify repository exists in `repo.json` prior to processing issues. |

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Work 0 | [`references/work/step-0-resolve-issues.md`](references/work/step-0-resolve-issues.md) | Parse issue hints, verify GitHub auth, query issues, and fetch live metadata |
| Work 1 | [`references/work/step-1-triage-and-verify.md`](references/work/step-1-triage-and-verify.md) | Verify issues against HEAD, close fixed-on-main issues with evidence, run decision quiz |
| Work 2 | [`references/work/step-2-grouping-and-planning.md`](references/work/step-2-grouping-and-planning.md) | Cluster related issues into cohesive /implement groups, separate conflicting issues, formulate briefs |
| Work 3 | [`references/work/step-3-spawn-grok-implement.md`](references/work/step-3-spawn-grok-implement.md) | Create Orca worktree per group, wait for TUI idle, dispatch /implement to new Grok session |
| Work 4 | [`references/work/step-4-wait-and-verify.md`](references/work/step-4-wait-and-verify.md) | Poll Grok sessions to completion, independently verify code changes and test runs in worktrees |
| Work 5 | [`references/work/step-5-ship-and-report.md`](references/work/step-5-ship-and-report.md) | Push verified branches, open draft PRs, tear down worktrees, and synthesize final report |
| Setup 0 | [`references/setup/step-0-add-repo.md`](references/setup/step-0-add-repo.md) | Register or remove repository in source-of-truth `repo.json` watchlist and verify accessibility |
| Setup 1 | [`references/setup/step-1-presetup.md`](references/setup/step-1-presetup.md) | Audit issue tracker settings, template availability, and collaborator permissions |
| Setup 2 | [`references/setup/step-2-setup-labels.md`](references/setup/step-2-setup-labels.md) | Configure standard issue triage labels (`triage`, `in-progress`, `fixed-on-main`, `spec-issue`, `wontfix`) |
| Setup 3 | [`references/setup/step-3-automation.md`](references/setup/step-3-automation.md) | Create dedicated per-repository Orca issue event automation for the new repo |
| Sweep 0 | [`references/sweep/step-0-init-sweep.md`](references/sweep/step-0-init-sweep.md) | Verify auth, read watchlist, and initialize nightly issue sweep |
| Sweep 1 | [`references/sweep/step-1-audit-open-issues.md`](references/sweep/step-1-audit-open-issues.md) | Fetch open issues and classify by staleness bucket |
| Sweep 2 | [`references/sweep/step-2-reverify-and-group.md`](references/sweep/step-2-reverify-and-group.md) | Re-verify stale issues at HEAD, close fixed-on-main issues, and group queueable issues into /implement cohorts |
| Sweep 3 | [`references/sweep/step-3-verify-cohorts.md`](references/sweep/step-3-verify-cohorts.md) | Poll /implement worktrees, independently verify, and open draft PRs |
| Sweep 4 | [`references/sweep/step-4-report.md`](references/sweep/step-4-report.md) | Compose and report sweep summary |
