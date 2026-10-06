# Shared Kernel Backlog

## Current Condition

`modules/shared` holds the AES kernel: all taxonomy, contract, and utility
modules that every feature folder imports. It contains no feature-specific
logic. Both required doc files (DATA.md + BACKLOG.md) are present and
current as of 2026-09-23.

## Backlog

| ID | Work Item | State |
|----|-----------|-------|
| SHARED-01 | Create DATA.md documenting the kernel's prefix taxonomy and dependency rule | Done |
| SHARED-02 | Create BACKLOG.md to satisfy the AES701 shared-doc pair requirement | Done |

No open items. The kernel is stable; changes follow the normal PR process.

## Scenario Evidence

- `python3 -m pytest modules/ -q` → 594 passed
- `python3 -m ruff check modules/` → clean
- `lac scan . --format json` → 0 AES701 findings

## Blockers

None.

## Dependencies

- Feature folders (`modules/<feat>/src/`) import from `modules/shared/src/`
  only; the shared folder never imports a feature module.
- `modules/root_cli_entry.py` is the sole composition point that bridges
  feature factories and the CLI surface layer.

## Release Readiness

Kernel is frozen for the current release cycle. No breaking changes are in
progress.

## Deferred

- Consolidating the 54 `src/` files into sub-folders by layer prefix is a
  future layout refactor; the current flat prefix scheme is the stable
  convention.

## Change Log

- 2026-09-23: SHARED-01 and SHARED-02 completed.
