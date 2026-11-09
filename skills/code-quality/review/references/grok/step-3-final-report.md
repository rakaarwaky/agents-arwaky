# Step 3: Aggregate, cleanup, and final report

## Step 3 details (Aggregation)

1. For every entry in `personas`, read `<review_file_<persona>>` via `read_file`.
2. Count issues by matching heading lines against `^### Issue \d+ -- Severity: (bug|suggestion|nit)$` and bucket by the captured severity. Heading lines that do not match the pattern (typo'd severity, malformed heading) are uncounted; log a one-line warning to the user listing the heading. Do not re-parse the body for a `Severity:` field; the heading is the canonical source.
3. If a per-persona file is missing, empty, or its subagent reported `ERROR`, record that persona's row as `ERROR` with the subagent's error text (or "review file not written") and continue.
4. Compute aggregate totals: `bugs = sum`, `suggestions = sum`, `nits = sum` across all personas; `completed = <number of personas whose row is not ERROR>`, `errored = <number of ERROR rows>`.
5. Write `<summary_file>` with the structure below.

Summary file structure:

```markdown
# Review Summary

- **Mode**: <commit | uncommit | pr | path>
- **Target**: <target>
- **Files reviewed**: <count> (<list, truncated to 10 if longer>)
- **Personas run**: <N> selected, <P> completed, <E> errored

## Per-persona results

| Persona | bugs | suggestions | nits | State |
|---|---|---|---|---|
| <persona> | 1 | 2 | 0 | completed |
| <persona> | 0 | 1 | 3 | completed |
| <persona> | - | - | - | ERROR: <reason> |

## Totals

<completed>/<N> personas completed, <bugs> bugs, <suggestions> suggestions, <nits> nits; <E> errored.

## Top issues

<First 5 issue titles across all personas, one per line, in the form
"[<persona>] [severity] file:line -- description (truncated to ~100 chars)">

Per-persona review files:
- <review_file_<persona1>>
- <review_file_<persona2>>
- ...
```

## Final report

Present a final report to the user. Items 1 and 2 are always included; item 3 is always included after aggregation; item 4 is included only when at least one persona completed.

1. **Mode + target** — one of:
   - `commit`: "Last commit `<short-hash>` (<subject>) reviewed with <N> persona(s)."
   - `uncommit`: "Uncommitted working-tree changes reviewed with <N> persona(s)."
   - `pr`: "PR #<pr-number> reviewed with <N> persona(s)."
   - `path`: "Path `<target>` reviewed with <N> persona(s)."
2. **Files reviewed** — count and (if 10 or fewer) the list from `<files_file>`.
3. **Per-persona table + totals** — exactly the table and totals line from `<summary_file>` (item 5 of Step 3). One row per persona, plus the totals line.
4. **Deliverable paths** — the absolute path to `<summary_file>` and one line per per-persona review file (only completed personas; ERROR rows list the error instead).

Empty-path exits (Step 1 short-circuit): "No files to review." No file paths — nothing was written.

## Cleanup

Cleanup is asymmetric by outcome:

- **Successful run (all personas completed, or some errored):** keep every `<review_file_<persona>>` and `<summary_file>`. Remove only `<files_file>` and, for diff modes (`commit` / `uncommit` / `pr`), `<diff_file>`.
- **Empty-path exit (Step 1 short-circuit):** remove nothing — `<files_file>` was never populated and no review files were written.

For the removals, run the resolved `<PYTHON> <HOST_PY> cleanup <files_file> [diff_file]` with the absolute paths. Missing files are allowed. Do not use a shell deletion command.
