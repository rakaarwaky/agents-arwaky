# Feature Backlog: widgets-ext

FRD: [FRD.md](FRD.md)
State: In Progress
Health: yellow
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
| WEXT-01 | FR-WEXT-001 | Widget extension registry; supports plugin load, plugin unload, and hot-reload of registered widgets without restarting the host process. | P0 | In Progress | Registry skeleton merged at `111aaaa`; plugin load path untested | add plugin unload test in `widgets-ext/tests/test_registry.py`; `python3 -m pytest widgets-ext/tests -q` passes; then set row WEXT-01 Next Action to "done" in `widgets-ext/BACKLOG.md`. | 2026-10-20 |
