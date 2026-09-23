# Feature Backlog: tools

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-23

> Supersedes the BACKLOGs of the four former modules: `modules/installer/BACKLOG.md`,
> `modules/updater/BACKLOG.md`, `modules/uninstaller/BACKLOG.md`,
> `modules/runner/BACKLOG.md` — all four module directories were merged into
> this one and deleted.

## Current Condition

- Done: the tools feature spec and design were rewritten against the
  approved plan — `FRD.md` now carries 6 behavioural FRs, a single-method
  protocol table (`execute` / `op, spec?, query?, args?`), the 7-row
  aggregate table (`list`, `resolve`, `install`, `update`, `uninstall`,
  `run`, `executable_path`), and 8 test scenarios. The code follows the
  same shape: the 11 leaf protocols plus `IToolAdapterFacade` collapsed
  into one `IToolsProtocol.execute(op, spec?, query?, args?)`; the
  aggregate methods renamed (`list_tools`→`list`, `resolve_spec`→
  `resolve`, `run_tool`→`run`); the four action capabilities and the
  adapter facade implement the single protocol and dispatch internally;
  the orchestrator, CLI surface, root container, and `root_cli_entry.py`
  all call the new names through `execute`.
- Blocked: none.
- Next Action: re-run the verification gate (`python3 -m compileall -q
  modules/tools modules/shared` + `python3 -m modules.root_cli_entry
  check docs modules/tools`) and a clean-host lifecycle sweep
  (install → update → run → uninstall) to move the four Gap scenarios
  out of unverified.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| TOL-01 | FR-TOOLS-001..004 | Unified tools feature (4 modules → 1) | P0 | Done | 4 action capability files, 13 plain-class adapters (mechanics via `utility_tool_mechanics`), orchestrator + surface + root container all present; old modules deleted; `root_cli_entry.py` repointed. Evidence: `python3 -m compileall -q modules/tools/` → COMPILE_OK; `python3 -c "import modules.tools"` → import OK; verified at commit `b44f139` (2026-09-19). | @raka | None | 2026-09-19 |
| TOL-02 | FR-TOOLS-004 | Exit-code fidelity + sentinel 126 on clean host | P1 | QA | Needs a clean-host `aa tool run <id>` sweep to assert real child exit codes pass through unmodified (0 / 1 / 127) and sentinel 126 on a vanished executable. | @raka | TOL-01 | 2026-09-23 |
| TOL-03 | FR-TOOLS-003 | Residual reporting sweep | P1 | QA | Needs a clean-host uninstall sweep to assert named residuals for active daemon units (never force-killed). | @raka | TOL-01 | 2026-09-19 |
| TOL-04 | FR-TOOLS-001..004 | Fold 8 capability files → 4 action classes | P2 | Done | `capabilities_tools_{provisioner,launcher,bumper,recorder,remover,verifier,discoverer,executor}.py` merged into `capabilities_tools_{installer,updater,uninstaller,runner}.py`; orchestrator + root container rewired through `IToolAdapterFacade`. Adapter consolidation: 13 `utility_<tool>_adapter.py` + `utility_tool_mechanics.py` deleted, mechanics inlined into `capabilities_tools_adapter.py` (AES301 exception registered in `lint_arwaky.config.yaml`). Gate: `python3 -m compileall -q modules/` + `python3 -m modules.root_cli_entry check`. Evidence: both re-run at commit `63921af` → COMPILE_OK + All verifications PASSED (2026-09-20). | @raka | TOL-01 | 2026-09-20 |
| TOL-05 | FR-TOOLS-001..006 | Collapse protocol surface + rename aggregate methods to match FRD | P1 | Done | 11 leaf protocols + `IToolAdapterFacade` deleted from `contract_tools_protocol.py`; single `IToolsProtocol.execute(op, spec?, query?, args?)` remains. `IToolsAggregate` renamed `list_tools`→`list`, `resolve_spec`→`resolve`, `run_tool`→`run`; callers fixed (surface, root container, `root_cli_entry.py`, shared barrel). Capabilities dispatch through `execute` to their internal actions. Evidence: `python3 -m compileall -q modules/tools modules/shared` → COMPILE_OK + `python3 -m modules.root_cli_entry check docs modules/tools` → 0 findings; verified at commit `f87a775` (2026-09-23). | @raka | TOL-04 | 2026-09-23 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| FR-TOOLS-001: Installing a registered tool twice makes the second run a no-op success with the launcher already in place. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-001: A dry-run install reports the planned invocation and leaves the filesystem untouched. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-002: Updating a tool whose pin is already satisfied skips the bump and writes no version record. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-002: Updating a tool with an unsatisfied pin bumps it and records the transition; recording it again is a no-op. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-003: Uninstalling a tool removes only its owned paths; an active daemon unit that refuses to stop is reported as a named residual and never force-killed. | Manual | — | TOL-03 clean-host uninstall residual sweep | unverified |
| FR-TOOLS-004: Running a registered tool returns the child's real exit code for 0, 1, and 127; an executable that vanishes after discovery returns sentinel 126. | Manual | — | TOL-02 clean-host `aa tool run` exit-code sweep | unverified |
| FR-TOOLS-005: Resolving a query by id, binary, or alias yields the matching tool specification; an unknown query yields no match without raising. | Proxy | — | `python3 -m modules.root_cli_entry tool run definitely-not-a-tool-xyz` → exit 1, no exception; `create_tools_feature().resolve(...)` smoke | 2026-09-23 |
| FR-TOOLS-006: Discovering readiness returns the executable path without touching install state, and no path when the tool is not installed. | Proxy | — | `create_tools_feature().executable_path(spec)` smoke → `$HOME/.local/bin/lint-arwaky-mcp` | 2026-09-23 |

## Blockers

- None recorded.
- Daemon tools (9Router, Anytype daemon) are gated on a Podman container for
  their service units; a stopped-from-stopping unit becomes a named residual,
  never a forced kill (container-isolation invariant).

## Dependencies

- `config/manifest.json` (repo-root SSOT, resolved via `repo_root()`) — tool
  ids, runner family, binary, alias, mcp_binary.
- `modules/shared/src` — `taxonomy_common_vo`, `taxonomy_common_error`,
  `taxonomy_tools_vo`, `taxonomy_tools_constant`, `taxonomy_common_constant`,
  `contract_tools_protocol`, `contract_tools_aggregate`, `utility_git_update`,
  `utility_manifest_reader`, `utility_paths_resolver`.
- `modules/daemon` — aggregate only, lazy-imported for service install/stop.
- `modules/root_cli_entry.py` — the only external surface (single `aa` entry point); imports `modules.tools` only.

## Release Readiness

- 8 of 8 scenario evidence rows recorded against the 8 FRD test scenarios
  (4 Gap, 2 Manual, 2 Proxy) — one row per scenario, in spec order.
- Gated on TOL-02 / TOL-03 (clean-host QA sweeps): full verification gate
  green and a clean-host lifecycle sweep (install → update → run →
  uninstall) with exit-code fidelity asserted.
- No release-blocking defects open; residual sweep (TOL-03) is P1 and does not
  gate the release of the merged feature.

## Deferred

- Intentionally out of scope for the merged `modules/tools` release.
- No new per-tool capability files (would violate the 4-action-class invariant).
- Cross-feature capability sharing beyond the lazy daemon aggregate.

## Change Log

- 2026-09-19: `modules/{installer,updater,uninstaller,runner}` merged into
  `modules/tools`; the four old BACKLOG/FRD files are superseded by this
  document and `modules/tools/FRD.md` and deleted with their directories.
- TOL-01 moved to QA on 2026-09-19 after the module tree landed and
  `modules/root_cli_entry.py` was repointed to `modules.tools`.
- 2026-09-19: `utility_adapter_base.py` deleted (AES404 violation: class with
  `self` in utility layer). Method bodies moved to `utility_tool_mechanics.py`
  (free functions, taxonomy-only imports). 13 leaf adapters now plain classes
  calling `tool_mechanics.<fn>(...)` directly. `IToolAdapter` ABC removed from
  `contract_tools_protocol.py`; adapter param typed as `object` with docstring.
- 2026-09-19: TOL-04 added — fold 8 capability files into 4 action classes
  (tracker only; not yet implemented).
- 2026-09-20: TOL-04 completed — 8 capability files folded into 4 action
  classes; 13 `utility_<tool>_adapter.py` + `utility_tool_mechanics.py`
  deleted with mechanics inlined into `capabilities_tools_adapter.py`
  (registered AES301 exception). `IToolAdapterFacade` + `ToolAdapterFacade`
  added; root container exposes `TOOLS_REGISTRY`.
- 2026-09-19: `skill` removed from the tools lifecycle. The skill manager is
  part of `agents-arwaky` itself (`modules/skill`), not an internal or vendor
  tool: its manifest entry, `utility_skill_adapter.py`, and the `skill`
  registry/constant keys were deleted. `aa skill …` remains the sole entry
  point; the 13-tool registry no longer includes skill.
- 2026-09-23: TOL-05 completed — FRD rewritten (6 FRs, 1-row protocol table,
  7-row aggregate table, 8 scenarios); 11 leaf protocols + `IToolAdapterFacade`
  collapsed into `IToolsProtocol.execute`; aggregate methods renamed to
  `list` / `resolve` / `run`; capabilities, orchestrator, surface, root
  container, `root_cli_entry.py`, and the shared barrel updated; Scenario
  Evidence expanded to 8 rows (4 Gap, 2 Manual, 2 Proxy).
