# Feature Backlog: runner

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-19

## Current Condition

- Done: runner split per-tool at `5556fd5` — `utility_runner_base.py`
  (`RunnerBase`), 14 `capabilities_<tool>_runner.py`, `agent_runner_orchestrator.py`
  (`RunnerOrchestrator` registry dispatch + `ToolOrchestrator` aggregate),
  `root_runner_container.py`; monolithic `capabilities_runner.py` deleted.
  `python -m modules.root_cli_entry tool run ponytail` → exit 0 at `5556fd5`;
  `aa check` PASSED at `5556fd5`.
- In Progress: RUN-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: RUN-03 — close this pair; then RUN-04 restructure to the
  2-capability business-action model (docs only so far, no code touched); then
  RUN-01 sweep across the 14 tools.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| RUN-01 | FR-001, FR-002 | Per-tool execution capability (14 tools) | P0 | QA | 14 capabilities + `RunnerBase` at `5556fd5`; `tool run ponytail` exit 0; `aa check` PASSED. Cross-tool sweep outstanding. Superseded in shape by RUN-04 — sweep runs after the restructure. | @raka | RUN-04 | 2026-09-19 |
| RUN-02 | FR-003 | Zero-I/O aggregate `ToolOrchestrator` composing the 4 lifecycle verbs | P0 | Done | `ToolOrchestrator(IToolAggregate)` present in `agent_runner_orchestrator.py` at `5556fd5`; container wires it via `root_runner_container.py`. The aggregate survives the restructure unchanged — only the executor side splits into discoverer + executor capabilities. | @raka | None | 2026-09-19 |
| RUN-03 | FR-001–FR-003 | FRD + BACKLOG pair authoring for runner | P0 | In Progress | FRD rewritten to the 2-capability business-action model (discoverer + executor; no adapters; universal discovery order as capability logic; `ToolOrchestrator` aggregate preserved; no dependency on `modules/installer/`, `modules/updater/`, or `modules/uninstaller/`). This BACKLOG updated to match. | @raka | None | 2026-09-19 |
| RUN-04 | FR-001, FR-002 | Restructure src/ to the 2-capability model | P0 | Todo | Not started — docs-only decision so far, no code touched. Scope: delete 14 `capabilities_<tool>_runner.py` and `utility_runner_base.py`; create `capabilities_runner_discoverer.py` (universal XDG-bin → PATH → install-dir resolution incl. MCP `mcp_binary` branch) + `capabilities_runner_executor.py` (subprocess launch, stdio inheritance vs MCP management, sentinel exit code); add `IToolDiscoverer` / `IToolExecutor` contracts replacing `IToolExecutor.find_executable`+`run`; simplify `agent_runner_orchestrator.py` `RunnerOrchestrator` to drive the two capabilities (drop `_REGISTRY` per-tool dispatch); keep `ToolOrchestrator` aggregate intact; rewire `root_runner_container.py`. No adapter files — runner has none. Verify: exactly 2 `capabilities_*.py` files, zero `utility_*_adapter.py` under `modules/runner/src/`, no `modules.installer` / `modules.updater` / `modules.uninstaller` import anywhere under `modules/runner/`, `python -m modules.root_cli_entry tool run ponytail` still exits 0, compileall + `aa check` green. | @raka | RUN-03 | 2026-09-19 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `run` on an installed tool returns 0 for a valid invocation. | Proxy | manual | `python -m modules.root_cli_entry tool run ponytail` -> 0 | `5556fd5` |
| `run` on a not-installed tool reports "not installed" with a non-zero code, no traceback. | Gap | — | — | `5556fd5` (no automated test yet) |
| `find_executable` finds an XDG-bin launcher ahead of the PATH entry. | Gap | — | — | `5556fd5` (no automated test yet) |
| `resolve_spec` returns `None` for an unknown query and a `ToolSpec` for an alias. | Gap | — | — | `5556fd5` (no automated test yet) |
| `discover` resolves an MCP tool through `mcp_binary` when set. | Gap | — | — | never (model introduced by RUN-04) |
| `execute` forwards args verbatim and inherits stdio for non-MCP tools. | Gap | — | — | never (model introduced by RUN-04) |

## Blockers

None.

## Dependencies

RUN-01 sweep needs one real tool per runner family (WS-05 env decision for daemon tools).
RUN-01 sweep depends on RUN-04 (restructure) landing first, otherwise it tests
the superseded per-tool model.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `tool run ponytail` exit 0 + `aa check` at `5556fd5`; cross-tool sweep outstanding, gated on RUN-04 |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | RUN-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | Runner per-tool split + FRD/BACKLOG pair during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 2-capability business-action model (discoverer + executor; no adapters; universal discovery order; `ToolOrchestrator` aggregate preserved); RUN-02 marked Done-as-survivor, RUN-04 opened for the src/ restructure; scenario rows added for MCP routing and arg forwarding. Docs only — no code touched. | @raka |