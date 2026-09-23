# ROADMAP — agents-arwaky

State / Health: vocabulary below. Last Updated: 2026-09-23

## Current Condition

- Done: legacy `tools/` fully migrated to AES `modules/`; 10/10 feature
  FRD/BACKLOG pairs HOW-TO-clean; FRD redesign plan approved and written
  (single-row `execute` protocol per feature); `aa check skill` → PASSED
  (92 skills / 20 categories).
- In Progress: none at workspace level; per-feature QA sweeps live in each
  feature BACKLOG (tools TOL-02/TOL-03, config CFG-01/CFG-04, daemon DMN-01,
  service SVC-01, mcp MCP-01, skill SKL-01, backup BKP-01).
- Blocked: WS-05 (live `.env` home undecided).
- Next: WS-05, then WS-06 (port remaining legacy tests).

## State Definitions

| State | Meaning |
|-------|---------|
| Idea | Not examined; no spec. |
| Refinement | Being specced. |
| Ready | Specified; not started. |
| In Progress | Active now. |
| Blocked | Name the blocker in Actual Condition. |
| In Review | PR open. |
| QA | Awaiting verification pass. |
| Done | Command + commit evidence. |
| Released | Shipped. |
| Deferred | Out of scope; reason in Actual Condition. |

| Health | Meaning |
|--------|---------|
| On Track | No threat to the gate. |
| At Risk | Gaps may miss the gate. |
| Blocked | Cannot proceed. |
| Ready for QA | Open rows clear; sweep left. |
| Ready for Release | Evidence recorded. |
| Released | Shipped. |

## Status Policy

- Verified, not self-reported: re-run the cited command; name a commit hash
  (never "today"). A `Done` / `Released` row owes a code-span command plus
  that hash in Actual Condition.
- Same PR updates every backlog row the change invalidates.
- Prefixes: workspace `WS-` · feature `<SCOPE>-` (feature rows stay in that
  feature's BACKLOG; this file carries cross-cutting rows only).
- `Last Updated` / `Updated` move only with a change in the file.

## Feature Roll-up

One table: every feature. Feature detail stays in each feature's BACKLOG.

| ID | Item | Priority | Spec | Backlog | State | Health | Owner | Next | Updated |
|---|---|---|---|---|---|---|---|---|---|
| modules/tools | Tool lifecycle (install / update / uninstall / run / resolve) | P0 | [FRD](modules/tools/FRD.md) | [BACKLOG](modules/tools/BACKLOG.md) | QA | At Risk | @raka | TOL-02, TOL-03 | 2026-09-23 |
| modules/check | Docs + skill verification gate | P0 | [FRD](modules/check/FRD.md) | [BACKLOG](modules/check/BACKLOG.md) | Done | On Track | @raka | keep `aa check` at 0 | 2026-09-23 |
| modules/mcp | MCP manifest → client config / list / probe | P0 | [FRD](modules/mcp/FRD.md) | [BACKLOG](modules/mcp/BACKLOG.md) | QA | On Track | @raka | MCP-01 sweep | 2026-09-23 |
| modules/config | Comment-safe config load / save / merge / env | P1 | [FRD](modules/config/FRD.md) | [BACKLOG](modules/config/BACKLOG.md) | QA | On Track | @raka | CFG-01 round-trip | 2026-09-23 |
| modules/daemon | Daemon lifecycle + Anytype auth / units | P1 | [FRD](modules/daemon/FRD.md) | [BACKLOG](modules/daemon/BACKLOG.md) | QA | On Track | @raka | DMN-01 live sweep | 2026-09-23 |
| modules/doctor | Host + tool readiness diagnosis | P1 | [FRD](modules/doctor/FRD.md) | [BACKLOG](modules/doctor/BACKLOG.md) | Done | On Track | @raka | none | 2026-09-23 |
| modules/harness | Connect / disconnect / skill provisioning | P1 | [FRD](modules/harness/FRD.md) | [BACKLOG](modules/harness/BACKLOG.md) | Ready | At Risk | @raka | HRS-01 sweep | 2026-09-23 |
| modules/service | systemd unit drive / status / logs | P1 | [FRD](modules/service/FRD.md) | [BACKLOG](modules/service/BACKLOG.md) | QA | On Track | @raka | SVC-01 live sweep | 2026-09-23 |
| modules/skill | Skill provision / audit / install / sync | P1 | [FRD](modules/skill/FRD.md) | [BACKLOG](modules/skill/BACKLOG.md) | QA | On Track | @raka | SKL-01 sweep | 2026-09-23 |
| modules/backup | Archive / restore / list / status | P2 | [FRD](modules/backup/FRD.md) | [BACKLOG](modules/backup/BACKLOG.md) | QA | On Track | @raka | BKP-01 gdrive leg | 2026-09-23 |
| modules/shared | Kernel (XDG, venv, launcher, engines) | P0 | — (kernel, not a feature) | — (no pair; see HOW-TO-MAKE-FRD) | In Progress | On Track | @raka | none | 2026-09-23 |

## Branches in Flight

| Branch | Backlog IDs | State |
|--------|-------------|-------|
| `main` | WS-05, WS-06 | green gates at tip |
| `develop` | WS-05 | integration tip |
| `refactor/standardize-xdg-uninstall` | TOL-03 | local, uninstall residual sweep |

## Workspace Backlog

Cross-cutting `WS-` rows only. Feature rows live in each feature's BACKLOG.

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|----------|-------|-------------------|-------|--------------|---------|
| WS-01 | — | Migrate legacy `tools/` into AES 7-layer `modules/` (P0-P4) | P0 | Done | Gate: `python3 -m modules.root_cli_entry check` → All verifications PASSED at `b9c8c62`; excludes live `.env` and legacy `tools/tests/`. | @raka | None | 2026-09-23 |
| WS-02 | — | Runner split per-tool (registry dispatch + RunnerBase + per-tool capabilities) | P0 | Done | Gate: `lint-arwaky scan modules` → 0 violations at `b9c8c62`; runner lives under `modules/tools`. | @raka | WS-01 | 2026-09-23 |
| WS-03 | — | Surface command consolidation into per-feature packages only | P0 | Done | Gate: `find modules -name 'surface_*.py'` → all under `modules/<feature>/src/` at `b9c8c62`; no `modules/cli`. | @raka | WS-01 | 2026-09-23 |
| WS-04 | — | FRD + BACKLOG pair for each module | P0 | Done | Pairs written + strict-only sweep; gate `aa check docs .` → 0 findings at `fffcd17` (working tree). | @raka | WS-01 | 2026-09-23 |
| WS-05 | — | Decide operator-local secrets location (live `.env` vs XDG config) after migration | P1 | Blocked | `config/` holds only `.env.example` + `manifest.json` + `version.txt`; live env files untracked. | @raka | None | 2026-09-22 |
| WS-06 | — | Migrate `tools/tests/` into `modules/tests/` | P1 | Deferred | 4 worktree tests in `tests/`; old suite not yet ported. | @raka | WS-01 | 2026-09-23 |
| WS-07 | — | Merge `refactor/aes-tools` into main, deleting legacy `tools/` there | P0 | Done | Gate: `git log --oneline -1` → merge on main at `b9c8c62`; legacy `tools/` gone; AES + ruff green. | @raka | WS-04, WS-08 | 2026-09-23 |
| WS-08 | — | Fix CI entry-point drift (`modules.cli` → `root_cli_entry`) | P0 | Done | Gate: `grep root_cli_entry .github/workflows/ci.yml` → 2 hits at `b9c8c62`; `aa check` green. | @raka | WS-03 | 2026-09-23 |

## Risk Register

- Risk: live `.env` files have no decided home (WS-05); a fresh clone has no
  daemon credentials and `aa anytype start` fails. Mitigation: WS-05 names a
  single XDG path before P1 daemon onboarding is trusted.
- Risk: tools clean-host fidelity (TOL-02 exit codes, TOL-03 residuals) is
  still QA-only; a host-specific failure would ship with the P0 tool gate
  green. Mitigation: run both sweeps before calling tools Done.
- Risk: harness has no automated per-harness coverage (HRS-01 Ready, tests
  Todo); a connector regression is only caught manually. Mitigation: land
  HRS-01 sweep before the next harness-facing release.
- Risk (closed 2026-09-23): CI entry-point drift (`modules.cli` →
  `root_cli_entry`). Resolved: `ci.yml` runs
  `python3 -m modules.root_cli_entry check`; gate green.
