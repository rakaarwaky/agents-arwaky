# Step 0: Resume or price

Run `aa skills traces state get`. Exit code 3 means a run is pending — resume it instead of starting over.

When the user abandons a pending run and wants to discard it, clear the status:

```
aa skills traces state clear --run-dir <RUN>
```

Then run `aa skills traces collect` into a run dir. The collector's window filters are real CLI flags with these defaults:

- `--since-last` — sessions since the last completed trace run (on by default via the constant `TRACE_COLLECT_SINCE_LAST`)
- `--min-turns N` — drop sessions with fewer than N human turns (default `3`, constant `TRACE_COLLECT_MIN_TURNS`)
- `--limit N` — max sessions to keep (default `0` = unlimited, constant `TRACE_COLLECT_LIMIT_UNLIMITED`)
- `--out DIR` — run dir for the output records (default: a scratch `skills-trace-*` temp dir)

Keep enough sessions and span for the window to be wide — a narrow run lists but does not retire (`--unlearn` mode, Global Rules: the narrow-window rule). This is step 0 because every subsequent step depends on the run dir and manifest it produces.
