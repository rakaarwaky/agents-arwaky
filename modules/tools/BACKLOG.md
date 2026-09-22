# Feature Backlog: tools

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-19

> Supersedes the BACKLOGs of the four former modules: `modules/installer/BACKLOG.md`,
> `modules/updater/BACKLOG.md`, `modules/uninstaller/BACKLOG.md`,
> `modules/runner/BACKLOG.md` — all four module directories were merged into
> this one and deleted.

## Current Condition

- Done: the four lifecycle features (installer, updater, uninstaller, runner)
  are merged into a single `modules/tools` feature: 4 protocol classes
  (`IToolInstaller`, `IToolUpdater`, `IToolUninstaller`, `IToolRunner` — one
  public method each; sub-steps internal), 4 verb capability files
  (`capabilities_tools_{installer,updater,uninstaller,runner}.py`), 13
  unified per-tool adapter units (one `capabilities_tools_adapter.py` — a
  registered AES301 god-object exception; all `utility_*` adapter modules
  deleted), `IToolAdapterFacade` protocol + `ToolAdapterFacade`, one
  `ToolsOrchestrator` aggregate, and the CLI surface
  `surface_tools_command.py`.
- Blocked: none.
- Next Action: run the full verification gate (`python3 -m compileall`, import
  smoke, `python3 -m modules.root_cli_entry check`, `python3 -m pytest tests/ -q`) and a
  clean-host lifecycle sweep.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| TOL-01 | FR-001..004 | Unified tools feature (4 modules → 1) | P0 | Done | 4 protocol classes, 8 verb capability files, 13 plain-class adapters (mechanics via `utility_tool_mechanics`), orchestrator + surface + root container all present; old modules deleted; `root_cli_entry.py` repointed. Evidence: `python3 -m compileall -q modules/tools/` → COMPILE_OK; `python3 -c "import modules.tools"` → import OK; verified at commit `b44f139` (2026-09-19). | @raka | None | 2026-09-19 |
| TOL-02 | FR-004 | Exit-code fidelity + sentinel 126 on clean host | P1 | QA | Needs a clean-host `aa tool run <id>` sweep to assert real child exit codes pass through unmodified. | @raka | TOL-01 | 2026-09-19 |
| TOL-03 | FR-003 | Residual reporting sweep | P1 | QA | Needs a clean-host uninstall sweep to assert named residuals for active daemon units. | @raka | TOL-01 | 2026-09-19 |
| TOL-04 | FR-001..004 | Fold 8 capability files → 4 verb classes | P2 | Done | `capabilities_tools_{provisioner,launcher,bumper,recorder,remover,verifier,discoverer,executor}.py` merged into `capabilities_tools_{installer,updater,uninstaller,runner}.py`; orchestrator + root container rewired through `IToolAdapterFacade`. Adapter consolidation: 13 `utility_<tool>_adapter.py` + `utility_tool_mechanics.py` deleted, mechanics inlined into `capabilities_tools_adapter.py` (AES301 exception registered in `lint_arwaky.config.yaml`). Gate: `python3 -m compileall -q modules/` + `python3 -m modules.root_cli_entry check`. Evidence: both re-run at commit `63921af` → COMPILE_OK + All verifications PASSED (2026-09-20). | @raka | TOL-01 | 2026-09-20 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| FR-001 Install: run twice → second is a no-op; dry-run leaves the filesystem untouched. | Gap | — | not yet asserted on a clean host | unverified |
| FR-002 Update: pin satisfied → skip; unsatisfied → bump + record; re-record is a no-op. | Gap | — | not yet asserted on a clean host | unverified |
| FR-003 Uninstall: clean removal; active daemon unit → named residual, never force-killed. | Gap | — | TOL-03 residual sweep pending | unverified |
| FR-004 Run: exit-code fidelity across 0/1/127; vanished executable → sentinel 126; unknown id → typed error before any capability; alias → resolved spec. | Manual | — | TOL-02 clean-host `aa tool run` sweep | unverified |

## Blockers

- None recorded.
- Daemon tools (9Router, Anytype daemon) are gated on a Podman container for
  their service units; a stopped-from-stopping unit becomes a named residual,
  never a forced kill (container-isolation invariant).

## Dependencies

- `config/manifest.json` (repo-root SSOT, resolved via `repo_root()`) — tool
  ids, runner family, binary, alias, mcp_binary.
- `modules/shared/src` — `taxonomy_common_vo`, `taxonomy_common_error`,
  `taxonomy_common_vo`, `taxonomy_common_vo`, `utility_git_update`,
  `utility_manifest_reader`, `utility_paths_resolver`.
- `modules/daemon` — aggregate only, lazy-imported for service install/stop.
- `modules/root_cli_entry.py` — the only external surface (single `aa` entry point); imports `modules.tools` only.

## Release Readiness

- Gated on TOL-01 (feature QA): full verification gate green and a clean-host
  lifecycle sweep (install → update → run → uninstall) with exit-code fidelity
  asserted.
- No release-blocking defects open; residual sweep (TOL-03) is P1 and does not
  gate the release of the merged feature.

## Deferred

- Intentionally out of scope for the merged `modules/tools` release.
- No new per-tool capability files (would violate the 4-verb-class invariant).
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
- 2026-09-19: TOL-04 added — fold 8 capability files into 4 verb classes
  (tracker only; not yet implemented).
- 2026-09-20: TOL-04 completed — 8 capability files folded into 4 verb
  classes; 13 `utility_<tool>_adapter.py` + `utility_tool_mechanics.py`
  deleted with mechanics inlined into `capabilities_tools_adapter.py`
  (registered AES301 exception). `IToolAdapterFacade` + `ToolAdapterFacade`
  added; root container exposes `TOOLS_REGISTRY`.
- 2026-09-19: `skill` removed from the tools lifecycle. The skill manager is
  part of `agents-arwaky` itself (`modules/skill`), not an internal or vendor
  tool: its manifest entry, `utility_skill_adapter.py`, and the `skill`
  registry/constant keys were deleted. `aa skill …` remains the sole entry
  point; the 13-tool registry no longer includes skill.
