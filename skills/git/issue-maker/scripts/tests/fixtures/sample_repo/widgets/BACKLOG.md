# Feature Backlog: widgets

FRD: [FRD.md](FRD.md)
State: In Progress
Health: green
Last Updated: 2026-10-20

## State Definitions

| State | Meaning |
| --- | --- |
| Ready | Specified; not started. |
| In Progress | Active now. |
| In Review | PR open; awaiting merge/verification. |
| Done | Command + commit evidence recorded in `Actual Condition`. |

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Next Action | Updated |
|---|---|---|---|---|---|---|---|
| WID-01 | FR-WID-001 | Widget creation and validation | P0 | In Progress | Widget validator partial; gate `python3 -m pytest widgets/tests -q` outstanding | add `widgets/src/validator.py` exercising `validate_widget`; `python3 -m pytest widgets/tests -q` passes; then set row WID-01 Next Action to "done" in `widgets/BACKLOG.md`. | 2026-10-20 |
| WID-02 | FR-WID-002 | Widget rendering pipeline | P1 | Ready | Not started | none | 2026-10-20 |
| WID-03 | FR-WID-003 | Widget cache backend | P2 | Done | Gate: `python3 -m pytest widgets/tests/test_cache.py -q` → 3 passed at `abc1234`; `widgets/src/cache.py` implements `WidgetCache` | none | 2026-09-01 |
| WID-04 | FR-WID-004 | Widget export | P1 | In Review | PR #42 open; `python3 -m pytest widgets/tests/test_export.py -q` → 2 passed at `def5678` | none | 2026-10-18 |

## Functional Requirements

### FR-WID-001: Widget creation and validation

Widgets validate their configuration on creation.

### FR-WID-002: Widget rendering pipeline

Widgets render through a single pipeline.

### FR-WID-003: Widget cache backend

Widgets read and write through a cache backend.

### FR-WID-005: Widget deletion

Widgets can be deleted; no backlog row cites this requirement yet.

## Feature Roll-up

| Feature | State |
| --- | --- |
| widgets | In Progress |
