# BACKLOG — agents-arwaky

| Feature | Tier | Spec | Backlog |
|---------|------|------|---------|
| `modules/tools` | P0 | [FRD](modules/tools/FRD.md) | [BACKLOG](modules/tools/BACKLOG.md) |
| `modules/shared` | P0 | [FRD](modules/shared/FRD.md) | [BACKLOG](modules/shared/BACKLOG.md) |
| `modules/check` | P0 | [FRD](modules/check/FRD.md) | [BACKLOG](modules/check/BACKLOG.md) |
| `modules/mcp` | P0 | [FRD](modules/mcp/FRD.md) | [BACKLOG](modules/mcp/BACKLOG.md) |
| `modules/config` | P1 | [FRD](modules/config/FRD.md) | [BACKLOG](modules/config/BACKLOG.md) |
| `modules/daemon` | P1 | [FRD](modules/daemon/FRD.md) | [BACKLOG](modules/daemon/BACKLOG.md) |
| `modules/doctor` | P1 | [FRD](modules/doctor/FRD.md) | [BACKLOG](modules/doctor/BACKLOG.md) |
| `modules/harness` | P1 | [FRD](modules/harness/FRD.md) | [BACKLOG](modules/harness/BACKLOG.md) |
| `modules/service` | P1 | [FRD](modules/service/FRD.md) | [BACKLOG](modules/service/BACKLOG.md) |
| `modules/skill` | P1 | [FRD](modules/skill/FRD.md) | [BACKLOG](modules/skill/BACKLOG.md) |
| `modules/backup` | P2 | [FRD](modules/backup/FRD.md) | [BACKLOG](modules/backup/BACKLOG.md) |

State: defined once in § State Definitions below; feature backlogs cite, never restate.
Health: defined once in § State Definitions below.
Last Updated: 2026-09-23

## Current Condition

- Done: legacy `tools/` fully migrated to `modules/` AES layout; merge landed
  on main; CI entry fixed to `modules.root_cli_entry`; `lint-arwaky scan
  modules` → 0 violations; `ruff check modules/ tests/ --ignore E501` →
  intentional-only (B008 VO defaults, BLE001 probe excepts); `aa check` →
  All verifications PASSED; `aa docs check .` → 0 errors; 10/10 unit tests.
- In Progress: WS-04 — FRD/BACKLOG pairs completion.
- Blocked: WS-05 (live `.env` home undecided).
- Next Action: WS-05 (name XDG path for live env), then WS-06 (port remaining
  legacy tests into `tests/`).

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
| `modules/tools` | P0 | Done | On Track | AES + ruff clean; `aa check` green |
| `modules/check` | P0 | In Progress | At Risk | CHK-03 — FRD/BACKLOG pair still open (WS-04) |
| `modules/daemon` | P1 | QA | On Track | DMN-03 — verification sweep outstanding |
| `modules/harness` | P1 | QA | On Track | HRS-03 — verification sweep outstanding |

## Backlog

Cross-cutting and workspace-level rows only. Feature rows live beside each feature.

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|----------|-------|-------------------|-------|--------------|---------|
| WS-01 | — | Migrate legacy `tools/` into AES 7-layer `modules/` (P0-P4) | P0 | Done | Gate: `python3 -m modules.root_cli_entry check` → All verifications PASSED at `b9c8c62`; excludes live `.env` and legacy `tools/tests/`. | @raka | None | 2026-09-23 |
| WS-02 | — | Runner split per-tool (registry dispatch + RunnerBase + 14 per-tool capabilities) | P0 | Done | Gate: `lint-arwaky scan modules` → 0 violations at `b9c8c62`; runner lives in `modules/tools/src/`. | @raka | WS-01 | 2026-09-23 |
| WS-03 | — | Surface command consolidation into per-feature packages only | P0 | Done | Gate: `find modules -name 'surface_*.py'` → all under `modules/<feature>/src/` at `b9c8c62`; no `modules/cli`. | @raka | WS-01 | 2026-09-23 |
| WS-04 | — | FRD + BACKLOG pair for each module | P0 | In Progress | Pairs written; gate `aa docs check .` → 0 errors at `320c422`. | @raka | WS-01 | 2026-09-23 |
| WS-05 | — | Decide operator-local secrets location (live `.env` vs XDG config) after migration | P1 | Blocked | `config/` holds only `.env.example` + `manifest.json` + `version.txt`; live env files untracked. | @raka | None | 2026-09-22 |
| WS-06 | — | Migrate `tools/tests/` into `modules/tests/` | P1 | Deferred | 4 worktree tests in `tests/`; old suite not yet ported. | @raka | WS-01 | 2026-09-23 |
| WS-07 | — | Merge `refactor/aes-tools` into main, deleting legacy `tools/` there | P0 | Done | Gate: `git log --oneline -1` → merge on main at `b9c8c62`; legacy `tools/` gone; AES + ruff green. | @raka | WS-04, WS-08 | 2026-09-23 |
| WS-08 | — | Fix CI entry-point drift (`modules.cli` → `root_cli_entry`) | P0 | Done | Gate: `grep root_cli_entry .github/workflows/ci.yml` → 2 hits at `b9c8c62`; `aa check` green. | @raka | WS-03 | 2026-09-23 |

## Blockers

- WS-05: no decided location for live `.env` (XDG config vs per-repo `.env`).

## Dependencies

- WS-07 (merge) waits on WS-04 (FRD/BACKLOG pairs) and WS-08 (CI drift fix).
- WS-08 waits on WS-03 (surface consolidation moved the entry point).
- Feature rows INS/UPD/UNL/RUN/SHR/CLI/CHK-03 (FRD/BACKLOG authoring) wait on
  WS-04's sweep; they are tracked in each feature's own BACKLOG.

## Release Readiness

Definition of "deployment ready":

| Area | Status | Notes |
|------|--------|-------|
| All P0 done | Done | WS-01…WS-04, WS-07, WS-08 closed |
| All P1 done + verified | Ready | WS-05 (env decision), WS-06 (tests) open |
| Tests pass, lint clean, build works | Done | `aa check` PASSED; `lint-arwaky scan modules` → 0; ruff intentional-only; 10/10 tests |
| Docs complete | In Progress | WS-04 in flight; 91 doc-check warnings remain (advisory, mostly research templates) |

## Deferred

- WS-06: port remaining legacy tests into `tests/` against current
  `modules.shared.src.*` paths.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | Root BACKLOG created (spec/status split, master index, roll-up, risk register) as part of WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-18 | Runner per-tool split, surface consolidation, contract decentralization merged into branch tip `5556fd5`. | @raka |
| 2026-09-23 | AES scan → 0, ruff reduced to intentional-only, ConnectOpts `adapters` field fixed, stale `tools/`/`modules/cli` docs refreshed; WS-07/WS-08 closed. | @raka |

## Branches in Flight

| Branch | Backlog IDs | State |
|--------|-------------|-------|
| `main` | WS-04, WS-05, WS-06 | green gates at tip |

## Risk Register

- **Risk (closed 2026-09-23):** CI entry-point drift (`modules.cli` → `root_cli_entry`). **Resolved:** `ci.yml` runs `python3 -m modules.root_cli_entry check`; gate green.
- **Risk:** live `.env` files have no decided home (WS-05); a fresh clone has no
  daemon credentials and `aa anytype start` fails. **Mitigation:** WS-05 names a
  single XDG path before P1 is unblocked.
- **Risk (closed 2026-09-18):** runner per-tool split left a monolithic
  `ToolResolver` that duplicated installer logic. **Resolved by** `5556fd5`:
  `utility_runner_base.py` + registry dispatch; `capabilities_runner.py` deleted.
