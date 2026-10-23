# CLI Surface Backlog

## Current Condition

All 9 per-feature `surface_*_command.py` modules live in `modules/cli/src/`.
The feature folders (`modules/<feat>/src/`) hold only `capabilities_*` and
`agent_*_orchestrator` files. `root_cli_entry.py` wires each surface module
to its feature factory via dependency injection.

## Backlog

| ID | Work Item | Priority | State | Dependencies | Next Action | Updated |
|----|-----------|:---------|-------|--------------|-------------|---------|
| CLI-01 | Move `surface_*_command.py` files from feature `src/` folders into `modules/cli/src/` | P2 | Done | none | none | 2026-09-23 |
| CLI-02 | Update import sites in `root_cli_entry.py`, feature `__init__.py`, and test `patch()` targets | P2 | Done | CLI-01 | none | 2026-09-23 |
| CLI-03 | Add `__init__.py` for `modules/cli` and `modules/cli/src` | P3 | Done | CLI-01 | none | 2026-09-23 |
| CLI-04 | Add DESIGN.md and BACKLOG.md to satisfy the AES703 surface-doc pair | P3 | Done | CLI-03 | none | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `python3 -m pytest modules/ -q` → 594 passed | Automated | `modules/cli/` suite | whole-suite pass | 2026-09-23 |
| `python3 -m ruff check modules/` → clean | Automated | `modules/cli/` suite | ruff clean | 2026-09-23 |
| `lac scan . --format json` → 0 AES702 findings | Automated | `modules/cli/` suite | lint clean | 2026-09-23 |

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
| Tests | Done | 594 passed across `modules/` |
| Lint | Done | `ruff` clean, `lac scan` 0 AES702 findings |

## Deferred

- Consolidating the 9 command modules into a single dispatch table is a
  future refactor; the current 1-module-per-feature layout is the stable
  AES surface pattern.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-23 | CLI-01 through CLI-04 completed | @raka |
| 2026-10-23 | Backlog, Scenario Evidence, Release Readiness, and Change Log converted to the AES606 template tables | @raka |
