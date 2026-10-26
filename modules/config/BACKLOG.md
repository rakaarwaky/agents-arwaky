# Feature Backlog: config

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Current Condition

- Done: `IConfigProtocol` split into two seam ABCs — `IConfigReaderProtocol`
  (`load` / `save` / `inspect` / `help`) and `IConfigModifierProtocol`
  (`merge_servers` / `set_env` / `remove_entries` / `help`). `ConfigWriter`
  implements the reader seam and `ConfigModifier` the modifier seam, each
  completely, so the six `raise NotImplementedError` stubs are gone
  (AES304 / Rule 4). `ConfigOrchestrator` no longer imports the concrete
  capabilities — both are injected by `root_config_container.py`, which also
  owns the usage text (clears AES201). Gate: `./.venv/bin/ruff check
  modules/config --ignore E501` → clean; `./.venv/bin/python -m pytest
  modules/config -q` → 77 passed at `767b18672a0c0abd92f7225f267478db8271c334`.
- In Progress: none.
- Blocked: none.
- Next Action: none.
- Verification: `./.venv/bin/python -m pytest modules/config -q` → 77 passed
  at `767b18672a0c0abd92f7225f267478db8271c334`; the targeted aggregate,
  byte-round-trip, dry-run-purity, and CLI tests pass.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| CFG-01 | FR-CONFIG-001, FR-CONFIG-002 | P1 | Done | CFG-04 | none | 2026-10-26 | `modules/config/tests/integration_config.py::test_config_roundtrip_jsonc_byte_identical`, `test_config_roundtrip_toml_byte_identical`, and `test_config_dry_run_remove_purity`; `./.venv/bin/python -m pytest modules/config/tests/integration_config.py -q` → 12 passed; `./.venv/bin/python -m pytest modules/config -q` → 77 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| CFG-02 | FR-CONFIG-002 | P1 | Done | None | none | 2026-10-26 | `modules/config/src/capabilities_config_modifier.py` and `modules/config/tests/integration_config.py`; `./.venv/bin/python -m pytest modules/config -q` → 77 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| CFG-03 | FR-CONFIG-002 | P1 | Done | None | none | 2026-10-26 | Dry-run removal preserves original bytes in `test_config_dry_run_remove_purity`; `./.venv/bin/python -m pytest modules/config -q` → 77 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| CFG-04 | FR-CONFIG-001, FR-CONFIG-002 | P1 | Done | None | none | 2026-10-26 | `modules/cli/src/surface_config_command.py` executes inspect/load in `test_config_cli_live_execute`; targeted integration suite → 12 passed; `./.venv/bin/python -m pytest modules/config -q` → 77 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Loading a JSONC config reports the parsed mapping and format jsonc. | Automated | `modules/config/tests/integration_config.py` | `test_config_roundtrip_jsonc_byte_identical` | `767b186` |
| Loading a TOML config returns nested tables with format toml. | Automated | `modules/config/tests/integration_config.py` | `test_config_roundtrip_toml_byte_identical` | `767b186` |
| Re-saving an unchanged JSONC file is byte-identical with comments and key order preserved. | Automated | `modules/config/tests/integration_config.py` | `test_config_roundtrip_jsonc_byte_identical` | `767b186` |
| Saving to an unwritable path fails without truncating the original file. | Gap | — | — | not yet |
| Merging a new MCP server entry leaves sibling servers and comments untouched. | Gap | — | — | not yet |
| Merging an already-present server without force is a no-op that changes nothing on disk. | Gap | — | — | not yet |
| Setting an env pair on a missing file creates the file containing that pair. | Gap | — | — | not yet |
| Setting an existing env key rewrites only that line, leaving the rest byte-identical. | Gap | — | — | not yet |
| Removing MCP servers with dry-run lists the would-be-removed names and writes nothing. | Automated | `modules/config/tests/integration_config.py` | `test_config_dry_run_remove_purity` | `767b186` |
| Removing an absent entry is a clean no-op returning an empty list. | Gap | — | — | not yet |
| Inspecting a config returns path, format, data, and server names without writing. | Gap | — | — | not yet |
| Two inspects of an unchanged file return equal snapshots and leave the file bytes unchanged. | Gap | — | — | not yet |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `./.venv/bin/python -m pytest modules/config -q` → 77 passed at `767b186`; aggregate round-trip, dry-run purity, and CLI execution covered |
| Scenario evidence | QA | JSONC/TOML round-trip, dry-run purity, and CLI inspect/load are automated; remaining host/path scenarios stay explicitly identified |
| Docs | Done | FRD and backlog rows are synchronized in this PR; per-row code/test evidence is recorded above |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | `IConfigProtocol` split into `IConfigReaderProtocol` + `IConfigModifierProtocol`; `ConfigWriter` owns reader seam only, `ConfigModifier` owns modifier seam only; both fully implemented — zero AES304 stubs, 73 tests, 0 lint violations at `6df9f21`. | @raka |
| 2026-09-23 | Redesign: FRD rebuilt around a single-execute protocol + config agent (6 FRs, 12 scenarios); protocol collapsed to `execute` with new aggregate, orchestrator, and `aa config` surface; scenario evidence synced 12 of 12. | @raka |
| 2026-10-26 | Added per-row FRD references and command/result/commit evidence for CFG-01 through CFG-04; 77 feature tests and 12 targeted integration tests pass at `767b186`. | @raka |
