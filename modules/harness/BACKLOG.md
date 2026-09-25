# Feature Backlog: harness

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-25

## Current Condition

- Done: FRD realigned to the single-`execute` Protocol design (4 FRs,
  8 scenarios) and the capability protocols collapsed into one
  `execute` with `all_targets` on the aggregate; gates green —
  `python3 -m compileall -q modules/harness` +
  `python3 -m modules.root_cli_entry check docs modules/harness`
  → 0 findings at `f87a775`.
- Done: provider leaves moved into the harness capability layer and wired
  through `HARNESS_REGISTRY` in the composition root, each serving
  `IHarnessProtocol` (`supported` / `satisfied`) via shared mechanics; gates
  green — `python3 -m pytest modules/harness/tests -q` (35 passed) +
  `lint-arwaky-cli scan modules/harness` → 0 at `fef1b90`.
- In Progress: none (leaf-protocol slice complete).
- Blocked: none.
- Next Action: HRS-01 — per-harness connect/disconnect/skills sweep
  (5 harnesses) against the collapsed structure.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| HRS-01 | FR-HARNESS-001, FR-HARNESS-002, FR-HARNESS-003 | Per-harness connect/disconnect/skills sweep (5 harnesses) | P1 | Ready | FRD now states 8 scenarios; no automated per-harness sweep on the current tree. | @raka | HRS-06 | 2026-09-23 |
| HRS-02 | FR-HARNESS-001 | Shared MCP config + skill provisioning machinery | P1 | Deferred | `capabilities_harness_shared.py` superseded by the machinery + leaf-adapter split (HRS-04). | @raka | None | 2026-09-19 |
| HRS-03 | FR-HARNESS-001, FR-HARNESS-002, FR-HARNESS-003, FR-HARNESS-004 | FRD + BACKLOG pair authoring for harness | P1 | Done | `python3 -m modules.root_cli_entry check docs modules/harness` → 0 findings at `f87a775`. | @raka | None | 2026-09-23 |
| HRS-04 | FR-HARNESS-001, FR-HARNESS-002, FR-HARNESS-003 | Restructure harness module to 3 business capabilities + 5 leaf adapters | P1 | Done | `python3 -m compileall -q modules/harness` → 0 at `f87a775`; connector/disconnector/skills + 5 leaf adapters on the tree. | @raka | HRS-03 | 2026-09-23 |
| HRS-05 | FR-HARNESS-001, FR-HARNESS-002 | Router wiring as connect/disconnect clause | P2 | Ready | Clause specified under FR-HARNESS-001/FR-HARNESS-002 and gated by the adapter custom-API flag; behaviour sweep owed under HRS-01. | @raka | HRS-04 | 2026-09-19 |
| HRS-06 | FR-HARNESS-001, FR-HARNESS-002, FR-HARNESS-003, FR-HARNESS-004 | Collapse capability protocols to one `execute` method; aggregate gains `all_targets` | P1 | Done | `python3 -m compileall -q modules/harness` + `python3 -m modules.root_cli_entry check docs modules/harness` → 0 findings at `f87a775`. | @raka | HRS-04 | 2026-09-23 |
| HRS-07 | FR-HARNESS-001, FR-HARNESS-002, FR-HARNESS-003 | Provider leaves serve `IHarnessProtocol`; registry wired in the composition root | P1 | Done | `python3 -m pytest modules/harness/tests -q` → 35 passed + `lint-arwaky-cli scan modules/harness` → 0 at `fef1b90`; five leaves inherit the protocol and `HARNESS_REGISTRY` covers every supported id. | @raka | HRS-04 | 2026-09-25 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa connect hermes` writes an MCP config listing every manifest server and provisions the skill pack. | Manual | — | `aa connect hermes` + diff generated config | `5556fd5` |
| `aa connect --router grok-build` wires the local router only when the adapter declares custom-API support; otherwise reports the skip. | Gap | — | — | not yet verified |
| `aa disconnect --dry-run` reports what would be removed (MCP servers, env keys, router refs) and changes nothing. | Manual | — | `python3 -m modules.root_cli_entry disconnect --opencode --dry-run` → exit 0, all steps DRY-RUN | `f87a775` |
| Disconnecting a harness that was never connected is an idempotent no-op that exits 0. | Gap | — | — | not yet verified |
| `aa connect --skills-only qwencode` provisions the skill pack without touching MCP config. | Gap | — | — | not yet verified |
| Provisioning into a harness with no skill dir skips it with a report while remaining targets continue. | Gap | — | — | not yet verified |
| `aa connect --all` targets every supported harness id in a single run. | Gap | — | — | not yet verified |
| An unknown harness token fails with a message naming the supported harness set. | Manual | — | `python3 -m modules.root_cli_entry connect --notaharness` → exit 1, supported set named | `f87a775` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

Skill provisioning depends on `modules/skill` pack integrity (root WS-06 for the
migrated test suite). Router wiring depends on `modules/daemon` exposing the
9Router endpoint resolver.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Todo | No automated per-harness coverage; HRS-01 sweep pending |
| Scenario evidence | Done | 8 of 8 scenarios mapped (3 Manual, 5 Gap) |
| Docs | Done | FRD realigned to 1-row Protocol + 5-row Aggregate; `check docs modules/harness` → 0 findings at `f87a775` |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 3 business capabilities (connector/disconnector/skills); router setup folded into connect/disconnect. BACKLOG rebased: HRS-02 deprecated, HRS-03 closed, HRS-04 opened (restructure), HRS-05 added (router clause). | @raka |
| 2026-09-23 | Protocol collapsed to a single `execute` row; FRD rewritten to 4 FRs / 8 scenarios with `all_targets` on the aggregate; scenario evidence synced 8 of 8; HRS-04 + HRS-06 closed at `f87a775`. | @raka |
