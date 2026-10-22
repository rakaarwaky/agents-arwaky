# Shared Kernel Backlog

## Current Condition

`modules/shared` holds the AES kernel: all taxonomy, contract, and utility
modules that every feature folder imports. It contains no feature-specific
logic. Both required doc files (DATA.md + BACKLOG.md) are present and
current as of 2026-09-23.

## Backlog

| ID | Work Item | Priority | State | Dependencies | Next Action | Updated |
|----|-----------|:---------|-------|--------------|-------------|---------|
| SHARED-01 | Create DATA.md documenting the kernel's prefix taxonomy and dependency rule | P3 | Done | none | none | 2026-09-23 |
| SHARED-02 | Create BACKLOG.md to satisfy the AES701 shared-doc pair requirement | P3 | Done | SHARED-01 | none | 2026-09-23 |

No open items. The kernel is stable; changes follow the normal PR process.

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `python3 -m pytest modules/ -q` → 594 passed | Automated | `modules/shared/` suite | whole-suite pass | 2026-09-23 |
| `python3 -m ruff check modules/` → clean | Automated | `modules/shared/` suite | ruff clean | 2026-09-23 |
| `lac scan . --format json` → 0 AES701 findings | Automated | `modules/shared/` suite | lint clean | 2026-09-23 |

## Blockers

None.

## Dependencies

- Feature folders (`modules/<feat>/src/`) import from `modules/shared/src/`
  only; the shared folder never imports a feature module.
- `modules/root_cli_entry.py` is the sole composition point that bridges
  feature factories and the CLI surface layer.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Kernel | Done | Kernel is frozen for the current release cycle; no breaking changes in progress |

## Deferred

- Consolidating the 54 `src/` files into sub-folders by layer prefix is a
  future layout refactor; the current flat prefix scheme is the stable
  convention.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-23 | SHARED-01 and SHARED-02 completed | @raka |
| 2026-10-23 | Backlog, Scenario Evidence, Release Readiness, and Change Log converted to the AES606 template tables | @raka |
