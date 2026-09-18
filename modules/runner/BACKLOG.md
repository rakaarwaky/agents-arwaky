# Feature Backlog: runner

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: runner split per-tool at `5556fd5` — `utility_runner_base.py`
  (`RunnerBase`), 14 `capabilities_<tool>_runner.py`, `agent_runner_orchestrator.py`
  (`RunnerOrchestrator` registry dispatch + `ToolOrchestrator` aggregate),
  `root_runner_container.py`; monolithic `capabilities_runner.py` deleted.
  `python -m modules.root_cli_entry tool run ponytail` → exit 0 at `5556fd5`;
  `aa check` PASSED at `5556fd5`.
- In Progress: RUN-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: RUN-03 — close this pair; then RUN-01 sweep across the 14 tools.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| RUN-01 | FR-001, FR-002 | Per-tool execution capability (14 tools) | P0 | QA | 14 capabilities + `RunnerBase` at `5556fd5`; `tool run ponytail` exit 0; `aa check` PASSED. Cross-tool sweep outstanding. | @raka | None | 2026-09-18 |
| RUN-02 | FR-003 | Zero-I/O aggregate `ToolOrchestrator` composing the 4 lifecycle verbs | P0 | Done | `ToolOrchestrator(IToolAggregate)` present in `agent_runner_orchestrator.py` at `5556fd5`; container wires it via `root_runner_container.py`. | @raka | None | 2026-09-18 |
| RUN-03 | FR-001–FR-003 | FRD + BACKLOG pair authoring for runner | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `run` on an installed tool returns 0 for a valid invocation. | Proxy | manual | `python -m modules.root_cli_entry tool run ponytail` -> 0 | `5556fd5` |
| `run` on a not-installed tool reports "not installed" with a non-zero code, no traceback. | Gap | — | — | `5556fd5` (no automated test yet) |
| `find_executable` finds an XDG-bin launcher ahead of the PATH entry. | Gap | — | — | `5556fd5` (no automated test yet) |
| `resolve_spec` returns `None` for an unknown query and a `ToolSpec` for an alias. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

RUN-01 sweep needs one real tool per runner family (WS-05 env decision for daemon tools).

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `tool run ponytail` exit 0 + `aa check` at `5556fd5`; cross-tool sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | RUN-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | Runner per-tool split + FRD/BACKLOG pair during WS-04 doc sweep at `5556fd5`. | @raka |
