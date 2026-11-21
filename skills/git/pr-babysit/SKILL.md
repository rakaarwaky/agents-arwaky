---
name: pr-babysit
description: "Watch pull requests, fix failing CI, merge via Mergify queue."
when-to-use: "Triggers on \"/pr-babysit\". Phrasing: \"watch PR 123 until green\", \"babysit PR 123 and merge when ready\", \"fix issue #123 and open a PR\", \"keep fixing PR 123 until it can merge\", \"pr-babysit ship 123\", \"pr-babysit setup 123\", \"pr-babysit setup add repo\", \"pr-babysit setup remove repo\", \"pr-babysit sweep\"."
argument-hint: "<ship|setup|sweep> <pr link|number|repo name>"
---

# PR Babysitter

Watch pull requests, parse failing CI logs, push incremental fixes, configure Mergify merge queues, and merge through coordinated agent lanes. Operates in three lanes — `ship` (babysit a single PR end to end), `setup` (register a repo in `repo.json`, bootstrap CI and Mergify configs, register the repo in the Orca event automation so PR/CI events fire), and `sweep` (nightly main-CI health check across all watched repos). Only PRs authored by `rakaarwaky` are ever processed, fixed, or merged; the author gate is enforced at three layers — Orca automation `from=me` filter, Mergify `author = rakaarwaky` in every repo's Mergify config (`.github/workflows/mergify.yml`), and the skill's own author check in `ship/step-0-add-pr.md` and `ship/step-7-merge.md`. The watchlist lives at `/home/raka/.agents/develop/repo.json` (symlinked to `/home/raka/.orca/bots/nany-pr-babysit/repo.json`); a repo absent from it is never watched.

## Rules

| ID | Rule | Check |
|----|------|-------|
| R1 | Determine execution lane strictly from physical environment variables (`HERMES_AGENT=1` or `GROK_AGENT=1`); stop if unset. | Verify agent attribution environment variable before loading lane references. |
| R2 | Read only the winning lane's references; never inspect or load the alternate lane's files. | Confirm reference file accesses match detected lane. |
| R3 | Enforce scope ceilings: maximum 3 fix commits per pass, no subagent dispatch inside a single worktree. | Count fix commits and verify single-agent execution in worktree. |
| R4 | Never modify skills outside `.agents/skills/pr-babysit/` during babysitting runs. | Check modified files match babysit skill path. |
| R5 | Verify live CI status and merge state directly on GitHub before declaring PR babysitting complete. | Run `gh pr view` to verify CI check runs and merge status. |
| R6 | Reject any PR whose author is not `rakaarwaky`, and any repo absent from `repo.json`. | Check author and watchlist before processing. |
| R7 | Reject any PR carrying the `release` label — release PRs are owned by Risa-AutoRelease and must not be processed, fixed, or merged by this skill. | Check `gh pr view <number> --json labels` for `release` label before processing; skip if present. |

## Routing

| Step | Reference | Purpose |
|------|-----------|---------|
| Hermes 0 | [`references/hermes/step-0-watch-and-spawn.md`](references/hermes/step-0-watch-and-spawn.md) | Verify auth, register PR in watchlist, compose detailed brief for Grok, spawn Grok worktree |
| Hermes 1 | [`references/hermes/step-1-wait-and-reverify.md`](references/hermes/step-1-wait-and-reverify.md) | Wait for Grok pass, read report, reverify CI on live head |
| Hermes 2 | [`references/hermes/step-2-merge.md`](references/hermes/step-2-merge.md) | Verify merge landed live on GitHub, retire Grok worktree |
| Hermes 3 | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to user with fixes, outcome, and watchlist state |
| Grok Ship 0 | [`references/grok/ship/step-0-add-pr.md`](references/grok/ship/step-0-add-pr.md) | Author gate, repo watchlist check, undraft when green, register PR with ship: true |
| Grok Ship 1 | [`references/grok/ship/step-1-watch-ci.md`](references/grok/ship/step-1-watch-ci.md) | Watch CI until green |
| Grok Ship 2 | [`references/grok/ship/step-2-auto-fix.md`](references/grok/ship/step-2-auto-fix.md) | CI red: parse logs, fix code, Conventional Commits, push |
| Grok Ship 3 | [`references/grok/ship/step-3-decision-tree.md`](references/grok/ship/step-3-decision-tree.md) | Conflict resolution, review threads; troubleshooter: [`references/grok/ship/step-3-troubleshoot.md`](references/grok/ship/step-3-troubleshoot.md) |
| Grok Ship 4 | [`references/grok/ship/step-4-mergify-detect.md`](references/grok/ship/step-4-mergify-detect.md) | Detect Mergify; bootstrap `.github/workflows/mergify.yml` with author gate if missing |
| Grok Ship 5 | [`references/grok/ship/step-5-mergify-diagnostics.md`](references/grok/ship/step-5-mergify-diagnostics.md) | Check `mergify events`, quarantine flaky tests, upload JUnit |
| Grok Ship 6 | [`references/grok/ship/step-6-merge-protections.md`](references/grok/ship/step-6-merge-protections.md) | Check active freezes (`mergify freeze`), dependencies, stacked PRs |
| Grok Ship 7 | [`references/grok/ship/step-7-merge.md`](references/grok/ship/step-7-merge.md) | Re-check author gate, auto-merge via Mergify queue, monitor queue, fallback |
| Grok Setup 0 | [`references/grok/setup/step-0-add-repo.md`](references/grok/setup/step-0-add-repo.md) | Register/remove repo in `repo.json`; initialize known PRs |
| Grok Setup 1 | [`references/grok/setup/step-1-presetup.md`](references/grok/setup/step-1-presetup.md) | Collect repo facts and customization answers; read templates |
| Grok Setup 2 | [`references/grok/setup/step-2-setup-ci.md`](references/grok/setup/step-2-setup-ci.md) | Detect language, write `.github/workflows/ci.yml` with lint-arwaky, build, test |
| Grok Setup 3 | [`references/grok/setup/step-3-setup-mergify.md`](references/grok/setup/step-3-setup-mergify.md) | Detect Mergify, write `.github/workflows/mergify.yml` from template, commit and push branch |
| Grok Setup 4 | [`references/grok/setup/step-4-open-pr.md`](references/grok/setup/step-4-open-pr.md) | Open configuration PR with `setup` label |
| Grok Setup 5 | [`references/grok/setup/step-5-automation.md`](references/grok/setup/step-5-automation.md) | Create dedicated per-repository Orca event automation for the new repo |
| Grok Sweep 0 | [`references/grok/sweep/step-0-init-sweep.md`](references/grok/sweep/step-0-init-sweep.md) | Verify auth, read watchlist from `repo.json`, initialize sweep |
| Grok Sweep 1 | [`references/grok/sweep/step-1-check-main-ci.md`](references/grok/sweep/step-1-check-main-ci.md) | Check latest CI run on default branch for each watched repo |
| Grok Sweep 2 | [`references/grok/sweep/step-2-fix-main-ci.md`](references/grok/sweep/step-2-fix-main-ci.md) | Fix main CI failures via Orca worktree worker, open fix PR |
| Grok Sweep 3 | [`references/grok/sweep/step-3-check-draft-prs.md`](references/grok/sweep/step-3-check-draft-prs.md) | Author-gated undraft of `rakaarwaky` PRs with green CI |
| Grok Sweep 4 | [`references/grok/sweep/step-4-report.md`](references/grok/sweep/step-4-report.md) | Compose and report sweep summary |