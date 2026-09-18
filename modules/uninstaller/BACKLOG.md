# Feature Backlog: uninstaller

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-19

## Current Condition

- Done: 13 per-tool `capabilities_<tool>_uninstaller.py` +
  `agent_uninstaller_orchestrator.py` + `IToolUninstaller` contract at `5556fd5`;
  import OK; `aa check` PASSED at `5556fd5`.
- In Progress: UNL-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: UNL-03 — close this pair; then UNL-04 restructure to the
  2-capability business-action model (docs only so far, no code touched); then
  UNL-01 sweep (uninstall a real tool).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| UNL-01 | FR-001 | Per-tool uninstall capability (binary, XDG, daemon units) | P0 | QA | 13 capabilities present at `5556fd5`; import OK; `aa check` PASSED. End-to-end removal sweep outstanding. Superseded in shape by UNL-04 — sweep runs after the restructure. | @raka | UNL-04 | 2026-09-19 |
| UNL-02 | FR-002 | Registry-dispatch uninstall orchestrator (daemon/mcp split) | P0 | Deferred | `agent_uninstaller_orchestrator.py` routes by id at `5556fd5`. The per-tool-id dispatch model is superseded: capabilities are now per business action (remover, verifier), and the owned-path computation lives in the orchestrator as agent-layer glue — no per-runner adapters needed because removal is generic filesystem teardown. | @raka | None | 2026-09-19 |
| UNL-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for uninstaller | P0 | In Progress | FRD rewritten to the 2-capability business-action model (remover + verifier; no adapters; owned-set computation as orchestrator glue; no dependency on `modules/installer/`, `modules/updater/`, or `modules/runner/`). This BACKLOG updated to match. | @raka | None | 2026-09-19 |
| UNL-04 | FR-001, FR-002 | Restructure src/ to the 2-capability model | P0 | Ready | Not started — docs-only decision so far, no code touched. Scope: delete 13 `capabilities_<tool>_uninstaller.py`; create `capabilities_uninstaller_remover.py` + `capabilities_uninstaller_verifier.py`; move owned-path computation into `agent_uninstaller_orchestrator.py` as `_owned_paths(spec)` helper; add `IToolRemover` / `IToolVerifier` contracts replacing `IToolUninstaller`; rewire `root_uninstaller_container.py`. No adapter files — uninstaller has none. Verify: exactly 2 `capabilities_*.py` files, zero `utility_*_adapter.py` under `modules/uninstaller/src/`, no `modules.installer` / `modules.updater` / `modules.runner` import anywhere under `modules/uninstaller/`, compileall + `aa check` green. | @raka | UNL-03 | 2026-09-19 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Uninstalling an installed tool removes its launcher and XDG data; the binary is gone from PATH. | Proxy | manual | `aa tool uninstall <id>` then `which <binary>` | `5556fd5` |
| Uninstalling an absent tool is an idempotent success. | Gap | — | — | `5556fd5` (no automated test yet) |
| Uninstalling a running daemon reports the active unit as residual without force-killing. | Gap | — | — | `5556fd5` (no automated test yet) |
| Dry-run uninstall reports the planned deletions and leaves the filesystem untouched. | Gap | — | — | never (model introduced by UNL-04) |
| A partially-installed tool yields a partial removal with a residual list naming each survivor. | Gap | — | — | never (model introduced by UNL-04) |

## Blockers

None.

## Dependencies

Daemon teardown assumes the container-isolation invariant (root PRD § Scope).
UNL-01 sweep depends on UNL-04 (restructure) landing first, otherwise it tests
the superseded per-tool model.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; removal sweep outstanding, gated on UNL-04 |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | UNL-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 2-capability business-action model (remover + verifier; no adapters; owned-set as orchestrator glue); UNL-02 deprecated, UNL-04 opened for the src/ restructure; scenario rows added for dry-run and partial-removal cases. Docs only — no code touched. | @raka |