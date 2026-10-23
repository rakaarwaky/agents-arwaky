# Feature Backlog: harness

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-26

## Current Condition

- Done: `IHarnessProtocol` / `IHarnessOperationsProtocol` replaced by four
  per-seam ABCs — `IHarnessConnectProtocol` (`connect`),
  `IHarnessDisconnectProtocol` (`disconnect`), `IHarnessSkillsProtocol`
  (`provision_skills`), and `IHarnessProviderProtocol` (`execute` for the
  per-harness leaves). Each capability implements exactly one seam in full,
  so the fourteen `raise NotImplementedError` stubs are gone (AES304 /
  Rule 4). `HarnessConnector` keeps skill provisioning as an internal
  delegation to the injected `IHarnessSkillsProtocol` rather than a second
  owned method, and the three dead `execute(op, targets, flags)` dispatch
  wrappers on the business capabilities were removed. Gate:
  `lint-arwaky-cli scan modules/harness` → 0 violations;
  `python3 -m pytest modules/harness -q` → 36 passed at `6df9f21`.
- In Progress: none.
- Blocked: none.
- Next Action: HRS-01 — per-harness connect/disconnect/skills sweep
  (5 harnesses) against the per-seam structure.

## Backlog

| ID | Priority | State | Dependencies | Next Action | Updated |
|---|---|---|---|---|---|
| HRS-01 | P1 | Ready | HRS-06 | none | 2026-09-23 |
| HRS-02 | P1 | Deferred | None | none | 2026-09-19 |
| HRS-03 | P1 | Done | None | none | 2026-09-23 |
| HRS-04 | P1 | Done | HRS-03 | none | 2026-09-23 |
| HRS-05 | P2 | Ready | HRS-04 | none | 2026-09-19 |
| HRS-06 | P1 | Done | HRS-04 | none | 2026-09-26 |
| HRS-07 | P1 | Done | HRS-04 | none | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa connect hermes` writes an MCP config listing every manifest server and provisions the skill pack. | Manual | — | `aa connect hermes` + diff generated config | `5556fd5` |
| `aa connect --router grok-build` wires the local router only when the adapter declares custom-API support; otherwise reports the skip. | Gap | — | — | not yet verified |
| `aa disconnect --dry-run` reports what would be removed (MCP servers, env keys, router refs) and changes nothing. | Manual | — | `python3 -m modules.root_cli_entry disconnect --opencode --dry-run` → exit 0, all steps DRY-RUN | `f87a775` |
| Disconnecting a harness that was never connected is an idempotent no-op that exits 0. | Gap | — | — | not yet verified |
| `aa connect --skills-only hermes` provisions the skill pack without touching MCP config. | Gap | — | — | not yet verified |
| Provisioning into a harness with no skill dir skips it with a report while remaining targets continue. | Gap | — | — | not yet verified |
| `aa connect --all` targets every supported harness id in a single run. | Gap | — | — | not yet verified |
| An unknown harness token fails with a message naming the supported harness set. | Manual | — | `python3 -m modules.root_cli_entry connect --notaharness` → exit 1, supported set named | `f87a775` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

Skill provisioning depends on the `skills/` pack being readable by
`modules/skills` (list/show discovery). Router wiring depends on `modules/daemon` exposing the
OmniRoute endpoint resolver.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Ready for QA | 36 unit + contract + integration + e2e tests passing at `6df9f21`; HRS-01 per-harness connect/disconnect/skills sweep still outstanding |
| Scenario evidence | Done | 8 of 8 scenarios mapped (3 Manual, 5 Gap) |
| Docs | Done | FRD realigned to 1-row Protocol + 5-row Aggregate; `check docs modules/harness` → 0 findings at `f87a775` |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | `IHarnessOperationsProtocol` split into four per-seam ABCs (`IHarnessConnectProtocol` / `IHarnessDisconnectProtocol` / `IHarnessSkillsProtocol` / `IHarnessProviderProtocol`); dispatch wrappers removed; zero AES304 stubs, 36 tests, 0 violations at `6df9f21`. | @raka |
| 2026-09-23 | Protocol collapsed to a single `execute` row; FRD rewritten to 4 FRs / 8 scenarios with `all_targets` on the aggregate; scenario evidence synced 8 of 8; HRS-04 + HRS-06 closed at `f87a775`. | @raka |
