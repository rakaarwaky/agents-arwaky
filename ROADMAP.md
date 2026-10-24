# ROADMAP — agents-arwaky

State / Health: vocabulary below. Last Updated: 2026-10-24

## Current Condition

- Done: legacy `tools/` fully migrated to AES `modules/`; 10/10 feature
  FRD/BACKLOG pairs HOW-TO-clean; FRD redesign plan approved and written
  (single-row `execute` protocol per feature); the skill pack is served by
  `modules/skills/` through `aa skills` — read-only discovery (`list`,
  `show`, `validate`, `catalog`, `discover`, `weed`, `merge-plan`, `rules`)
  plus dry-run-by-default authoring (`repair`, `move`, `archive`,
  `new-category`).
- Removed: `modules/check`, the `aa check` gate, and the `aa skill` provisioning
  surface (install/uninstall/update/check) were deleted on 2026-09-28;
  `modules/skills/` now owns discovery *and* authoring, exposed as 12
  `aa skills` verbs.
- In Progress: none at workspace level; per-feature QA sweeps live in each
  feature BACKLOG (tools TOL-02/TOL-03, config CFG-01/CFG-04, daemon DMN-01,
  service SVC-01, mcp MCP-01, skills SKL-01, backup BKP-01).
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

### Cross-Cutting Backlog

Cross-cutting `WS-` rows only. Feature rows live in each feature's BACKLOG.
One table: every feature. Feature detail stays in each feature's BACKLOG.

| ID | Feature | Priority | State | Dependencies | Next Action | Updated |
|---|---|---|---|---|---|---|
| modules/tools | Tool lifecycle (install / update / uninstall / run / resolve) | P0 | QA | TOL-01 | TOL-02, TOL-03 | 2026-09-23 |
| modules/mcp | MCP manifest → client config / list / probe | P0 | QA | MCP-03 | MCP-01 sweep | 2026-09-23 |
| modules/config | Comment-safe config load / save / merge / env | P1 | QA | CFG-03 | CFG-01 round-trip | 2026-09-23 |
| modules/daemon | Daemon lifecycle + Anytype auth / units | P1 | QA | DMN-03 | DMN-01 live sweep | 2026-09-23 |
| modules/doctor | Host + tool readiness diagnosis | P1 | Done | DOC-03 | none | 2026-09-23 |
| modules/harness | Connect / disconnect / skill provisioning | P1 | Ready | HRS-04 | HRS-01 sweep | 2026-09-23 |
| modules/service | systemd unit drive / status / logs | P1 | QA | SVC-03 | SVC-01 live sweep | 2026-09-23 |
| modules/skills | Skill pack discovery: list / show (read-only) | P1 | QA | SKL-01 | none | 2026-09-23 |
| modules/backup | Archive / restore / list / status | P2 | QA | BKP-03 | BKP-01 gdrive leg | 2026-09-23 |
| modules/shared | Kernel (XDG, venv, launcher, engines) | P0 | In Progress | none | none | 2026-09-23 |

### Branches in Flight

| Branch | Backlog IDs | State |
|--------|-------------|-------|
| `main` | WS-05, WS-06 | green gates at tip |
| `develop` | WS-05 | integration tip |
| `refactor/standardize-xdg-uninstall` | TOL-03 | local, uninstall residual sweep |


| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|----------|-------|-------------------|-------|--------------|---------|
| WS-01 | — | Migrate legacy `tools/` into AES 7-layer `modules/` (P0-P4) | P0 | Done | Gate: `python3 -m compileall modules/` → clean at `b9c8c62`; excludes live `.env` and legacy `tools/tests/`. | @raka | None | 2026-09-23 |
| WS-02 | — | Runner split per-tool (registry dispatch + RunnerBase + per-tool capabilities) | P0 | Done | Gate: `lint-arwaky scan modules` → 0 violations at `b9c8c62`; runner lives under `modules/tools`. | @raka | WS-01 | 2026-09-23 |
| WS-03 | — | Consolidate surface commands into per-feature packages | P0 | Done | Gate: `find modules -name 'surface_*'` → all under `modules/<feature>/src/` at `b9c8c62`; no `modules/cli`. | @raka | WS-01 | 2026-09-23 |
| WS-04 | — | FRD + BACKLOG pair for each module | P0 | Done | Pairs written + strict-only sweep; 0 findings at `fffcd17` (working tree). | @raka | WS-01 | 2026-09-23 |
| WS-05 | — | Decide operator-local secrets location (live `.env` vs XDG config) after migration | P1 | Blocked | `config/` holds only `.env.example` + `manifest.json` + `version.txt`; live env files untracked. | @raka | None | 2026-09-22 |
| WS-06 | — | Migrate `tools/tests/` into `modules/tests/` | P1 | Deferred | 4 worktree tests in `tests/`; old suite not yet ported. | @raka | WS-01 | 2026-09-23 |
| WS-07 | — | Merge `refactor/aes-tools` into main, deleting legacy `tools/` there | P0 | Done | Gate: `git log --oneline -1` → merge on main at `b9c8c62`; legacy `tools/` gone; AES + ruff green. | @raka | WS-04, WS-08 | 2026-09-23 |
| WS-08 | — | Fix CI entry-point drift (`modules.cli` → `root_cli_entry`) | P0 | Done | Gate: `grep root_cli_entry .github/workflows/ci.yml` → 2 hits at `b9c8c62`; CI green. | @raka | WS-03 | 2026-09-23 |

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
  `python3 -m modules.root_cli_entry mcp generate`; gate green.
