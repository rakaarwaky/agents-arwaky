# Feature Backlog: check

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [BACKLOG.md](../../BACKLOG.md) — do not redefine here.
Last Updated: 2026-09-23

## Current Condition

- Done: protocol `execute(scope)` + aggregate `check` / `check_docs` /
  `check_skill` / `summary` wired through orchestrator and surface;
  strict-only gate green for this feature — `check docs modules/check`
  → 0 findings and `check skill` → PASSED (92 skills / 20 categories)
  at `f87a775`; FRD carries 3 FRs (`FR-CHECK-001`–`FR-CHECK-003`)
  with 6 scenarios.
- In Progress: none (redesign slice complete).
- Blocked: none.
- Next Action: keep `aa check` green as docs evolve (CHK-01 closed).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CHK-01 | FR-CHECK-001, FR-CHECK-002, FR-CHECK-003 | Gate aggregation + docs + skills runners | P0 | Done | Gate: `python3 -m modules.root_cli_entry check` dispatches docs `[1/2]` then skill `[2/2]`; strict-only (engine promotes every finding at exit; no `--strict` flag, no advisory tier); skill step PASSED at `f87a775`. | @raka | None | 2026-09-23 |
| CHK-02 | FR-CHECK-001 | Document invariant audit (`aa check docs`) | P0 | Done | Gate: `python3 -m modules.root_cli_entry check docs modules/check` → 0 findings (2 documents) at `f87a775`. | @raka | None | 2026-09-23 |
| CHK-04 | FR-CHECK-002 | Skill-pack loadability runner (`aa check skill`) | P0 | Done | `python3 -m modules.root_cli_entry check skill` → PASSED, 92 skills across 20 categories at `f87a775`. | @raka | None | 2026-09-23 |
| CHK-03 | FR-CHECK-001–FR-CHECK-003 | FRD + BACKLOG pair authoring / template alignment for check | P0 | Done | `python3 -m modules.root_cli_entry check docs modules/check` → 0 errors at `f87a775`; `check_frd_template` clean. | @raka | None | 2026-09-23 |
| CHK-05 | FR-CHECK-001, FR-CHECK-002, FR-CHECK-003 | Standard CLI scopes `aa check docs` / `aa check skill` | P0 | Done | `python3 -m modules.root_cli_entry check skill` + `check docs` smoke scopes at `f87a775`; unknown scope → usage exit 1. | @raka | None | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa check docs` on a tree whose documents satisfy every invariant exits 0 and reports zero findings. | Proxy | manual | `python3 -m modules.root_cli_entry check docs modules/check` → 0 findings | `f87a775` |
| A feature backlog `Done` row without a command and commit hash in its condition cell fails the gate with `done-without-evidence`. | Proxy | `modules/check/src/capabilities_check_docs.py` | doc-pack `done-without-evidence` finding | `30b61c8` |
| `aa check skill` on a loadable pack exits 0 and reports skill and category counts. | Proxy | manual | `python3 -m modules.root_cli_entry check skill` → PASSED, 92 skills / 20 categories | `f87a775` |
| A skill nested deeper than the category/skill depth fails the gate with `nested-layout`. | Proxy | manual | inject nested skill → `check skill` exit 1 with `nested-layout` | `f87a775` |
| `aa check docs` runs only the document audit and never enters the skill audit path. | Proxy | manual | `python3 -m modules.root_cli_entry check docs` → `[1/1]` docs only | `f87a775` |
| An unknown scope such as `aa check bogus` prints usage and exits non-zero without running any audit. | Proxy | `modules/check/src/surface_check_command.py` | unknown-scope path in `cmd_check` → usage exit 1 | `f87a775` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None — strict gate (CHK-01) is closed; research-template README findings cleared.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `check docs modules/check` → 0 findings and `check skill` → PASSED at `f87a775`; full gate dispatches `[1/2]`/`[2/2]` |
| Scenario evidence | Done | 6 of 6 scenarios mapped (6 Proxy) |
| Docs | Done | FRD rewritten to the approved redesign plan; pair matches HOW-TO (CHK-03) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Removed json/python/shell runners; gate now docs + skills only. | @raka |
| 2026-09-23 | Deleted dead `capabilities_doc_pack.py`; rewired `aa docs` to `utility_doc_pack`. | @raka |
| 2026-09-23 | Realigned this pair to HOW-TO-MAKE-{FRD,BACKLOG} golden templates. | @raka |
| 2026-09-23 | Collapsed aggregation into System Overview; FRs = 2 capabilities (docs, skills); IDs renamed per HOW-TO Rule 1 → `FR-CHECK-001`/`FR-CHECK-002`. | @raka |
| 2026-09-23 | Strict FRD template gate (`check_frd_template`); standard CLI scopes `aa check docs` / `aa check skill` (CHK-05). | @raka |
| 2026-09-23 | Realigned all 10 feature FRDs to HOW-TO: `FR-<FEATURE>-NNN` IDs, 6-col API tables, Integration/NFR shapes, tools six-fields; `aa check docs` → 0 errors. | @raka |
| 2026-09-23 | Removed the `aa docs` noun; `aa check docs [path]` now owns path/json/subtree flags (surface `_docs_audit`). | @raka |
| 2026-09-23 | Strict-only mode: `strict` param removed from contracts/runners; engine `as_strict` at exit; dead `_check_docs`/`_check_skill_pack` helpers deleted from `root_cli_entry`; CHK-01 → Done (0 findings). | @raka |
| 2026-09-23 | FRD redesigned per approved plan: 3 FRs (adds FR-CHECK-003 dispatch), Protocol API = single `execute(scope)`, aggregate `check`/`check_docs`/`check_skill`/`summary`, 6 scenarios; code `run` → `execute`; scenario evidence reset to 6 rows. | @raka |
