# Shared Kernel Backlog

State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-10-26

## Current Condition

`modules/shared` holds the AES kernel: all taxonomy, contract, and utility
modules that every feature folder imports. It contains no feature-specific
logic. Both required doc files (DATA.md + BACKLOG.md) are present and
current as of 2026-10-26.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|----|---------|-----------|----------|-------|--------------|-------------|---------|------------------|
| SHARED-01 | — | Create DATA.md documenting the kernel's prefix taxonomy and dependency rule | P3 | Done | none | none | 2026-10-26 | Prefix taxonomy and dependency rule are documented in `modules/shared/DATA.md`; `modules/shared/src/common/taxonomy_common_vo.py` and `modules/shared/tests/unit_shared_utilities.py` pass in `./.venv/bin/python -m pytest modules/shared -q` → 116 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SHARED-02 | — | Create BACKLOG.md to satisfy the AES701 shared-doc pair requirement | P3 | Done | SHARED-01 | none | 2026-10-26 | This backlog supplies the shared-doc pair; `./.venv/bin/python -m pytest modules/shared -q` → 116 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

No open items. The kernel is stable; changes follow the normal PR process.

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `./.venv/bin/python -m pytest modules -q` → 684 passed | Automated | all module suites | whole-suite pass | `767b186` |
| `./.venv/bin/ruff check modules --ignore E501` → clean | Automated | all module sources | Ruff clean | `767b186` |
| Shared utility unit suite → 116 passed | Automated | `modules/shared/tests/unit_shared_utilities.py` | utility regression tests | `767b186` |

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
| 2026-10-26 | Added per-row command/result/commit evidence for SHARED-01/02; shared suite passes 116 tests at `767b186`. | @raka |
| 2026-10-23 | Backlog, Scenario Evidence, Release Readiness, and Change Log converted to the AES606 template tables | @raka |
