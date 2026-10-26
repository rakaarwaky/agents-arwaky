# CLI Surface Backlog

State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-10-26

## Current Condition

All 9 per-feature `surface_*_command.py` modules live in `modules/cli/src/`.
The feature folders (`modules/<feat>/src/`) hold only `capabilities_*` and
`agent_*_orchestrator` files. `root_cli_entry.py` wires each surface module
to its feature factory via dependency injection.

## Backlog

| ID | Work Item | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|----|-----------|:---------|-------|--------------|-------------|---------|------------------|
| CLI-01 | Move `surface_*_command.py` files from feature `src/` folders into `modules/cli/src/` | P2 | Done | none | none | 2026-10-26 | All per-feature surfaces are under `modules/cli/src/`; `./.venv/bin/python -m pytest modules/cli -q` → 2 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| CLI-02 | Update import sites in `root_cli_entry.py`, feature `__init__.py`, and test `patch()` targets | P2 | Done | CLI-01 | none | 2026-10-26 | Root entry and feature imports use the shared CLI package; `./.venv/bin/python -m pytest modules/cli -q` → 2 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| CLI-03 | Add `__init__.py` for `modules/cli` and `modules/cli/src` | P3 | Done | CLI-01 | none | 2026-10-26 | Both package files exist and import in `modules/cli/tests/integration_cli.py::test_cli_packages_import_and_config_surface_executes`; `./.venv/bin/python -m pytest modules/cli -q` → 2 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| CLI-04 | Add DESIGN.md and BACKLOG.md to satisfy the AES703 surface-doc pair | P3 | Done | CLI-03 | none | 2026-10-26 | `modules/cli/DESIGN.md` and this backlog are present; `./.venv/bin/python -m pytest modules/cli -q` → 2 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `./.venv/bin/python -m pytest modules -q` → 684 passed | Automated | all module suites | whole-suite pass | `767b186` |
| `./.venv/bin/ruff check modules --ignore E501` → clean | Automated | all module sources | Ruff clean | `767b186` |
| Root CLI help advertises local-only backup output | Automated | `modules/cli/tests/integration_cli.py` | `test_root_help_advertises_local_backup_only` | `767b186` |

## Blockers

None.

## Dependencies

- `modules/shared` kernel (taxonomy, contracts, utilities) — imported by all
  surface modules through the feature aggregate; never imported directly by
  surface code for I/O.
- `modules/root_cli_entry.py` — the only call-site that imports surface
  modules by path; it receives feature factories from the root container.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Behaviour | Done | Surface module names and exit-code contracts match the pre-migration `tools/` runner actions 1:1; no operator-visible behaviour changed |
| Tests | Done | `./.venv/bin/python -m pytest modules/cli -q` → 2 passed at `767b186`; full suite → 684 passed |
| Lint | Done | `./.venv/bin/ruff check modules --ignore E501` → clean at `767b186` |

## Deferred

- Consolidating the 9 command modules into a single dispatch table is a
  future refactor; the current 1-module-per-feature layout is the stable
  AES surface pattern.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-23 | CLI-01 through CLI-04 completed | @raka |
| 2026-10-26 | Added CLI package and help regression tests; recorded per-row command/result/commit evidence for CLI-01 through CLI-04 at `767b186`. | @raka |
| 2026-10-23 | Backlog, Scenario Evidence, Release Readiness, and Change Log converted to the AES606 template tables | @raka |
