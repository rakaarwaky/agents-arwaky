# Feature Backlog: harness

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-19

## Current Condition

- Done: `IHarnessConnector` contract + 5 provider-named capabilities +
  `agent_harness_orchestrator.py` + shared generation logic at `5556fd5`;
  import OK; `aa check` PASSED at `5556fd5`. FRD rewritten to the 3-capability
  business-action model (connector / disconnector / skills; router wiring folded
  into connect+disconnect).
- In Progress: HRS-04 — restructure `modules/harness/src/` to the 3-capability
  model: split `utility_harness_shared.py` into machinery + 5 leaf adapters,
  replace the 5 provider-named capabilities with 3 business-named ones, rewire
  orchestrator + container.
- Blocked: none.
- Next Action: HRS-04 implementation (delegated); then HRS-01 connect sweep per
  harness against the new structure.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| HRS-01 | FR-001, FR-002, FR-003 | Per-harness connect/disconnect/skills sweep (5 harnesses) | P1 | Todo | Spec exists; no automated per-harness sweep on the current tree. Re-based on the 3-capability structure. | @raka | HRS-04 | 2026-09-19 |
| HRS-02 | FR-001 | Shared MCP config + skill provisioning machinery | P1 | Deprecated | `capabilities_harness_shared.py` superseded by HRS-04 split into machinery + leaf adapters. | @raka | None | 2026-09-19 |
| HRS-03 | FR-001, FR-002, FR-003 | FRD + BACKLOG pair authoring for harness | P1 | Done | FRD rewritten to 3-capability model; this BACKLOG reflects it. | @raka | None | 2026-09-19 |
| HRS-04 | FR-001, FR-002, FR-003 | Restructure harness module to 3 business capabilities + 5 leaf adapters | P1 | In Progress | Brief written; delegating to Grok Build. Scope: delete `utility_harness_shared.py` + 5 `capabilities_harness_<provider>.py`; add `capabilities_harness_{connector,disconnector,skills}.py`, `utility_{hermes,opencode,grok,qwencode,antigravity}_adapter.py`, adapter registry in taxonomy, rewired `root_harness_container.py` + `agent_harness_orchestrator.py`. | @raka | HRS-03 | 2026-09-19 |
| HRS-05 | FR-001 | Router wiring as connect/disconnect clause | P2 | Todo | Behaviour specified under FR-001/FR-002 (no standalone capability). Implement inside connector/disconnector gated by adapter `supports_custom_api`. | @raka | HRS-04 | 2026-09-19 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa connect hermes` generates an MCP config listing every manifest server and provisions the skill pack. | Manual | — | `aa connect hermes` + diff generated config | `5556fd5` |
| `aa connect --router grok-build` wires 9Router only when the adapter declares custom-API support; otherwise reports the skip. | Gap | — | — | not yet implemented |
| `aa disconnect --dry-run` reports what would be removed (MCP, env, router refs) and changes nothing. | Gap | — | — | `5556fd5` (no automated test yet) |
| `aa connect` for an unknown harness fails with a message naming the supported harnesses. | Gap | — | — | `5556fd5` (no automated test yet) |
| A new harness added as one `utility_<x>_adapter.py` + one registry entry passes all verbs with zero capability edits. | Gap | — | — | not yet verified |

## Blockers

None.

## Dependencies

Skill provisioning depends on `modules/skill` pack integrity (root WS-06 for the
migrated test suite). Router wiring depends on `modules/daemon` exposing the
9Router endpoint resolver.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Todo | No automated coverage on the new structure yet; HRS-01 sweep pending |
| Type gate | Todo | `aa check` must pass after HRS-04 lands |
| Docs | Done | HRS-03 closed (FRD + BACKLOG aligned to 3-capability model) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 3 business capabilities (connector/disconnector/skills); router setup folded into connect/disconnect. BACKLOG rebased: HRS-02 deprecated, HRS-03 closed, HRS-04 opened (restructure), HRS-05 added (router clause). | @raka |