# Feature Backlog: installer

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-19

## Current Condition

- Done: 14 per-tool `capabilities_*_installer.py` + registry-dispatch
  `agent_installer_orchestrator.py` + `IToolInstaller` contract at `5556fd5`;
  `python -c "import modules.installer.src"` OK at `5556fd5`; `aa check` PASSED
  at `5556fd5`. Excludes: live `.env` handling (root WS-05).
- In Progress: INS-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: INS-03 — close out this pair; then INS-04 restructure to the
  2-capability business-action model (docs only so far, no code touched); then
  INS-01 verification sweep on a clean XDG host.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| INS-01 | FR-001 | Per-tool install capability for every manifest tool | P0 | QA | 14 capability modules present at `5556fd5`; import OK; `aa check` PASSED. Needs a clean-host install sweep to assert `aa tool install <id>` end-to-end. Superseded in shape by INS-04 — sweep runs after the restructure. | @raka | INS-04 | 2026-09-19 |
| INS-02 | FR-002 | Registry-dispatch orchestrator (one capability per tool id) | P0 | Deferred | `agent_installer_orchestrator.py` routes by id; no per-tool `if` branches; verified by import + `aa check` at `5556fd5`. Superseded by INS-04: capabilities are now per business action (provisioner, launcher), and the orchestrator's registry keys on the manifest `id` selecting that tool's leaf adapter. | @raka | None | 2026-09-19 |
| INS-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for installer | P0 | Done | FRD rewritten to the 2-capability business-action model (provisioner + launcher; **per-tool** leaf adapters `utility_<tool>_adapter.py`, one per manifest id; no dependency on `modules/runner/`). This BACKLOG updated to match. Verified at commit `81e3736`: re-run `aa docs check modules/installer` → exit 0 with no `[FAIL]`; re-run `python -m compileall -q modules/installer` → COMPILE_OK. | @raka | None | 2026-09-19 |
| INS-04 | FR-001, FR-002 | Restructure src/ to the 2-capability model | P0 | Ready | Not started — docs-only decision so far, no code touched. Scope: move each tool's install mechanics out of its `capabilities_<tool>_installer.py` into a per-tool leaf adapter `utility_<tool>_adapter.py` (one per manifest id — e.g. `utility_mnemosyne_adapter.py`, `utility_context7_adapter.py`, `utility_lint_adapter.py`), sharing primitives from `modules/shared` rather than duplicating copytree/chmod/atomic-install; then collapse the capability layer to exactly two business-action modules `capabilities_installer_provisioner.py` + `capabilities_installer_launcher.py`; keep `utility_launcher_writer.py` as pure mechanics; add the `IToolAdapter` contract (per-tool, not per-runner family); rewire `root_installer_container.py` and the orchestrator's `_ADAPTERS` registry to key on the manifest `id`; rename `IToolInstaller` surface to `IToolProvisioner` / `IToolLauncherRegistrar` per FRD API Contract. No generic runner-family adapter is created. Verify: exactly 2 `capabilities_*.py` files; one `utility_<tool>_adapter.py` per manifest id; adapters import nothing from capabilities/agent/root/contract layers; no `modules.runner` import anywhere under `modules/installer/`; compileall + `aa check` green. | @raka | INS-03 | 2026-09-19 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Installing a known tool id on a clean host yields a working binary on PATH. | Proxy | manual | `aa tool install <id>` then `which <binary>` | `5556fd5` |
| Installing an unknown tool id fails with a typed error, not a crash. | Gap | — | — | `5556fd5` (no automated test yet) |
| Re-installing a satisfied tool id is idempotent. | Gap | — | — | `5556fd5` (no automated test yet) |
| A manifest tool with no registered per-tool adapter fails with a typed error naming the id. | Gap | — | — | never (model introduced by INS-04) |
| Dry-run provisioning leaves the filesystem untouched. | Gap | — | — | never (model introduced by INS-04) |
| After install, the launcher and each alias exist under XDG bin. | Gap | — | — | never (model introduced by INS-04) |

## Blockers

None.

## Dependencies

Root WS-05 (live `.env` location) gates any install that reads daemon secrets.
INS-01 sweep depends on INS-04 (restructure) landing first, otherwise it tests
the superseded per-tool model.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; clean-host install sweep outstanding, gated on INS-04 |
| Type gate | Done | `aa check` includes compileall + JSON validation at `5556fd5` |
| Docs | Done | INS-03 pair closed; FRD + this BACKLOG consistent on the per-tool-adapter model |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 2-capability business-action model (provisioner + launcher, per-runner leaf adapters); INS-02 deprecated, INS-04 opened for the src/ restructure; scenario rows added for the new failure modes. Docs only — no code touched. | @raka |
| 2026-09-19 | Corrected adapter granularity: leaf adapters are **per-tool** (`utility_<tool>_adapter.py`, keyed on manifest `id`), not per-package-manager family. FRD System Overview, API Contract (`IToolAdapter`, `_ADAPTERS` keyed on id), NFRs (added Adapter-granularity metric), Test Scenarios, Assumptions and Glossary updated; INS-02/INS-03/INS-04 rows, the no-adapter scenario row and Release Readiness aligned. Still docs only — no code touched. | @raka |