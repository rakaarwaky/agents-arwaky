# BACKLOG — agents-arwaky

| Feature | Tier | Spec | Backlog |
|---------|------|------|---------|
| `modules/tools` | P0 | [FRD](modules/tools/FRD.md) | [BACKLOG](modules/tools/BACKLOG.md) |
| `modules/shared` | P0 | [FRD](modules/shared/FRD.md) | [BACKLOG](modules/shared/BACKLOG.md) |
| `modules/cli` | P0 | [FRD](modules/cli/FRD.md) | [BACKLOG](modules/cli/BACKLOG.md) |
| `modules/check` | P0 | [FRD](modules/check/FRD.md) | [BACKLOG](modules/check/BACKLOG.md) |
| `modules/mcp` | P0 | [FRD](modules/mcp/FRD.md) | [BACKLOG](modules/mcp/BACKLOG.md) |
| `modules/config` | P1 | [FRD](modules/config/FRD.md) | [BACKLOG](modules/config/BACKLOG.md) |
| `modules/daemon` | P1 | [FRD](modules/daemon/FRD.md) | [BACKLOG](modules/daemon/BACKLOG.md) |
| `modules/doctor` | P1 | [FRD](modules/doctor/FRD.md) | [BACKLOG](modules/doctor/BACKLOG.md) |
| `modules/harness` | P1 | — (module absent in this worktree; connector lives in `modules/shared/src/`) | — |
| `modules/service` | P1 | [FRD](modules/service/FRD.md) | [BACKLOG](modules/service/BACKLOG.md) |
| `modules/skill` | P1 | [FRD](modules/skill/FRD.md) | [BACKLOG](modules/skill/BACKLOG.md) |
| `modules/backup` | P2 | [FRD](modules/backup/FRD.md) | [BACKLOG](modules/backup/BACKLOG.md) |

State: defined once in § State Definitions below; feature backlogs cite, never restate.
Health: defined once in § State Definitions below.
Last Updated: 2026-09-18

## Current Condition

- Done: legacy `tools/` (74 .py files, P0-P4) fully migrated to `modules/` AES
  layout on branch `refactor/aes-tools`; runner split per-tool at `5556fd5`;
  16/16 feature packages import clean (`python -c "import ..."` on all 16, at
  `5556fd5`); `aa check` passes (All verifications PASSED, at `5556fd5`);
  `aa docs check .` → 107 docs scanned, 0 errors, 91 warnings at `5556fd5`
  (warnings concentrated in `skills/research/research-paper-writing/` templates,
  out of migration scope).
- In Progress: WS-04 — FRD/BACKLOG pairs for the 7 P0 modules being written
  (this file's index targets them); CI entry-point drift WS-08.
- Blocked: none.
- Next Action: WS-08 (CI `aa check` still runs `python3 -m modules.cli check`
  but the entry is `modules/root_cli_entry.py`) — cheapest risk reducer before
  merge; then WS-05 (live `.env` location) and the `refactor/aes-tools` merge.

## State Definitions

| State | Meaning |
|-------|---------|
| Idea | Captured, not yet examined; no spec exists for it. |
| Refinement | Being specced; a spec or product decision is needed first. |
| Ready | Specified enough to start; nobody has started it. |
| In Progress | Someone is in it now. |
| Blocked | Cannot proceed; name the blocker in `Actual Condition`. |
| In Review | PR open, awaiting review/CI. |
| QA | Implemented; awaiting a verification pass against evidence. |
| Done | Evidenced complete — cites the command/commit/PR. |
| Released | Done and shipped in a release. |
| Deferred | Intentionally out of current scope; reason in `Actual Condition`. |

| Health | Meaning |
|--------|---------|
| On Track | Nothing threatens the tier's scope. |
| At Risk | Open gaps could compromise the tier's gate. |
| Blocked | Work cannot proceed; name the blocker. |
| Ready for QA | No open backlog items; a verification sweep is outstanding. |
| Ready for Release | All evidence for the feature is recorded. |
| Released | Shipped. |

## Status Policy

- Status is **verified, not self-reported**. A row reaches `Done` only after
  someone re-ran the evidence command and read its output. `Ready` means
  "specified, not started", not "broken".
- A recorded verification names a **commit hash**, not "today".
- A PR that merges a fix updates **every** backlog row that fix invalidates, in
  the same PR.
- `Last Updated` / `Updated` move only with a change in the file.
- ID prefixes: workspace rows `WS-`; feature rows use the module's short prefix
  (`INS-`, `UPD-`, `UNL-`, `RUN-`, `SHR-`, `CLI-`, `CHK-`, `DMN-`, `HRS-`).

## Feature Roll-up

| Feature | Tier | State | Health | Next Action |
|---------|------|-------|--------|-------------|
| `modules/installer` | P0 | In Progress | At Risk | INS-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/updater` | P0 | In Progress | At Risk | UPD-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/uninstaller` | P0 | In Progress | At Risk | UNL-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/runner` | P0 | In Progress | At Risk | RUN-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/shared` | P0 | In Progress | At Risk | SHR-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/cli` | P0 | In Progress | At Risk | CLI-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/check` | P0 | In Progress | At Risk | CHK-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/daemon` | P1 | QA | On Track | DMN-03 — verification sweep outstanding |
| `modules/harness` | P1 | QA | On Track | HRS-03 — verification sweep outstanding |

## Backlog

Cross-cutting and workspace-level rows only. Feature rows live beside each feature.

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|----------|-------|-------------------|-------|--------------|---------|
| WS-01 | — | Migrate legacy `tools/` into AES 7-layer `modules/` (P0-P4) | P0 | Done | `tools/` tree absent in worktree; 16/16 feature packages import (`python -c "import modules.<feat>.src"`, 16/16) at `5556fd5`; `aa check` → All verifications PASSED at `5556fd5`. Excludes: live `.env` files and `tools/tests/` (not yet in worktree). | @raka | None | 2026-09-18 |
| WS-02 | — | Runner split per-tool (registry dispatch + RunnerBase + 14 per-tool capabilities) | P0 | Done | `modules/runner/src/` contains `utility_runner_base.py`, 14 `capabilities_*_runner.py`, `agent_runner_orchestrator.py` (RunnerOrchestrator + ToolOrchestrator) at `5556fd5`; `capabilities_runner.py` deleted; `aa check` PASSED at `5556fd5`. | @raka | WS-01 | 2026-09-18 |
| WS-03 | — | Surface command consolidation into `modules/cli/src/` only | P0 | Done | `find modules -name 'surface_*.py'` → all results under `modules/cli/src/` at `5556fd5`; 4 feature `__init__.py` re-export from `modules.cli.src.surface_*_command`; `aa check` PASSED at `5556fd5`. | @raka | WS-01 | 2026-09-18 |
| WS-04 | — | FRD + BACKLOG pair for each module (15 features: installer, updater, uninstaller, runner, shared, cli, check, mcp, config, daemon, doctor, harness, service, skill, backup) | P0 | In Progress | 15 of 15 pairs written in this sweep (root index updated to 16 rows at `5556fd5` + this doc commit); gate `aa docs check .` → 0 errors at tip. | @raka | WS-01 | 2026-09-18 |
| WS-05 | — | Decide operator-local secrets location (live `.env` vs XDG config) after migration | P1 | Blocked | `config/` in worktree holds only `.env.example` + `manifest.json` + `version.txt`; live `anytype.env`/`ninerouter.env` are untracked in the main repo (`tools/config/*.env` in the primary checkout; repo-relative) and absent from the worktree. Blocker: no decided XDG path for live env files. | @raka | None | 2026-09-18 |
| WS-06 | — | Migrate `tools/tests/` into `modules/tests/` | P1 | Deferred | 3 old test files (`test_doc_pack`, `test_lib_smoke`, `test_skill_provision`) absent from worktree; 5 worktree tests (`tests/test_completion`, `test_envfile`, `test_gdrive_mock`, `test_manifest`, `test_xdg`) exist but are not yet the migrated suite. Deferred: old imports `tools.lib.*` need rewrite to `modules.shared.src.*`. | @raka | WS-01 | 2026-09-18 |
| WS-07 | — | Merge `refactor/aes-tools` into main, deleting legacy `tools/` there | P0 | Ready | Branch is at `5556fd5`, clean tree, 16/16 import + `aa check` green; main repo still ships `tools/` (74 .py files) as the live `aa`. Excludes: merge itself (user action). | @raka | WS-04, WS-08 | 2026-09-18 |
| WS-08 | — | Fix CI entry-point drift: `ci.yml` runs `python3 -m modules.cli check` but entry is `modules/root_cli_entry.py` | P0 | Ready | `.github/workflows/ci.yml` line 46 still references `modules.cli`; module `modules.cli` no longer exposes `__main__` at that path post-`fdf5faf`. Verified: `grep 'modules.cli check' .github/workflows/ci.yml` → 1 hit at `5556fd5`. | @raka | WS-03 | 2026-09-18 |

## Blockers

- WS-05: no decided location for live `.env` (XDG config vs per-repo `.env`).

## Dependencies

- WS-07 (merge) waits on WS-04 (FRD/BACKLOG pairs) and WS-08 (CI drift fix).
- WS-08 waits on WS-03 (surface consolidation moved the entry point).
- Feature rows INS/UPD/UNL/RUN/SHR/CLI/CHK-03 (FRD/BACKLOG authoring) wait on
  WS-04's sweep; they are tracked in each feature's own BACKLOG.

## Release Readiness

Definition of "deployment ready" (target: post-merge `refactor/aes-tools`):

| Area | Status | Notes |
|------|--------|-------|
| All P0 done | In Progress | WS-04, WS-07, WS-08 open |
| All P1 done + verified | Ready | WS-05 (env decision), WS-06 (tests) open |
| Tests pass, lint clean, build works | Done | `aa check` → All verifications PASSED at `5556fd5`; CI `python -m compileall modules/` + `ruff check modules/` + JSON validation (ci.yml lines 27-43) |
| Docs complete | In Progress | WS-04 in flight; 91 doc-check warnings remain, concentrated in `skills/research/research-paper-writing/` templates (out of scope) |

## Deferred

- WS-06: legacy `tools/tests/` migration — imports need a full rewrite
  (`tools.lib.*` → `modules.shared.src.*`); deferred behind P0 merge so the old
  tree is deleted anyway and the suite is rebuilt against the new paths.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | Root BACKLOG created (spec/status split, master index, roll-up, risk register) as part of WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-18 | Runner per-tool split, surface consolidation, contract decentralization merged into branch tip `5556fd5`. | @raka |

## Branches in Flight

| Branch | Backlog IDs | State |
|--------|-------------|-------|
| `refactor/aes-tools` (worktree `.worktrees/aes-tools`) | WS-01…WS-04, WS-06…WS-08 | at `5556fd5`; not yet merged to main; worktree pending removal after merge |

## Risk Register

- **Risk:** merge happens with CI still pointing at `modules.cli` (WS-08), so the
  `aa check (internal gate)` job fails on main. **Mitigation:** WS-08 lands in the
  same PR as the merge.
- **Risk:** live `.env` files have no decided home (WS-05); a fresh clone has no
  daemon credentials and `aa anytype start` fails. **Mitigation:** WS-05 names a
  single XDG path before P1 is unblocked.
- **Risk (closed 2026-09-18):** runner per-tool split left a monolithic
  `ToolResolver` that duplicated installer logic. **Resolved by** `5556fd5`:
  `utility_runner_base.py` + registry dispatch; `capabilities_runner.py` deleted.
