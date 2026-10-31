# Step 10 Memory Flush

## Step 10: Memory Flush

After cleanup, update the workspace memory file with patterns from this run. The orchestrator performs this directly using its own tools -- no subagent is needed. This step follows the same protocol as the `/implement` skill's Step 6 (see `.grok/skills/implement/SKILL.md` for full helper documentation, exit codes, and file format details).

### Step 10a: Collect & Categorize This Run's Patterns

1. Use the `issue_patterns` list accumulated during Step 5b and Step 5c re-reviews across all PRs and review rounds.
2. **Generalize each pattern.** The memory file exists to help *future* runs on *different* tasks — patterns that reference this task's specific code, variable names, or domain objects are useless noise. Strip implementation-specific details (file names, variable names, type names, function names, domain-specific terms) and rewrite each pattern as a reusable principle that applies across different codebases and tasks:
   - Bad: "Missing error type `RetryableError` in retry handler list" → Good: "Missing entries in error-type or configuration allowlists"
   - Bad: "JWT token not validated for expiration" → Good: "Missing expiration/TTL validation on tokens or credentials"
   - Bad: "`calculateTotal` function exceeds 80 lines" → Good: "Functions exceeding reasonable length without decomposition"
   - Bad: "No test for `handleUserAuth` error path" → Good: "Missing tests for error/edge case paths"
   - Bad: "Missing null check on `userId` parameter" → Good: "Missing null/undefined checks on function inputs"
   If a pattern is *already* general (e.g., "Missing null checks on function inputs"), keep it as-is. If multiple task-specific patterns generalize to the same reusable principle, collapse them into one entry.
3. Categorize each generalized pattern into one of: Error Handling, Testing, Security, Code Quality, Naming, Documentation, Performance, or another short category name. Reuse existing category names from `existing_patterns_snapshot` (captured in Step 0) whenever the pattern fits.
4. For each pattern, write a concise one-line description. Keep descriptions on a single line.

### Step 10b: Harmonize Phrasing Against Existing Entries

Before handing generalized patterns to the helper, dedup at the *phrasing* level using `existing_patterns_snapshot`:

1. For each of this run's patterns, scan `existing_patterns_snapshot` for a semantically equivalent entry. If a match exists, replace this run's description with the **exact existing description string**.
2. If no match exists, keep the concise description as-is.
3. Within this run's own list, also dedup by phrasing -- collapse patterns that mean the same thing to a single entry.

### Step 10c: Build the Update Spec

Construct a JSON object:

```json
{
  "patterns": [
    {"category": "Error Handling", "description": "Missing null/undefined checks on function inputs"},
    {"category": "Testing", "description": "Missing tests for error/edge case paths"}
  ],
  "run": {
    "date": null,
    "description": "Execute plan: <design doc title or short description>",
    "rounds": <sum of review_rounds across all completed PRs>,
    "issues_by_severity": {"bug": <total>, "suggestion": <total>, "nit": <total>},
    "key_patterns": ["<2-3 most significant patterns from this run>"],
    "specializations": ["general", "simplicity"]
  }
}
```

Field notes:
- `run.date`: pass `null` and the helper fills in today's UTC date.
- `run.rounds`: sum of `review_rounds` across all completed PRs.
- `run.issues_by_severity`: derived from `total_issues_by_severity` (accumulated in Step 5b and Step 5c re-reviews across all PRs).
- `run.key_patterns`: pick 2-3 most-significant patterns (severity-ranked: bugs > suggestions > nits). **Apply the same generalization rules as Step 10a** — strip task-specific names and rewrite as reusable principles.
- `run.specializations`: the distinct set of reviewer specializations actually used across **all** PRs this run. Collect every `config.specialization` from every PR's `reviewer_configs`, strip the `-N` suffix so `general-2`/`general-3` collapse to `general`, normalize `plan_alignment` → `plan`, and deduplicate. Always include `simplicity`. For an effort=1 run this is `["general", "simplicity"]`; for higher effort it might be e.g. `["general", "security", "tests", "plan", "simplicity"]`.

### Step 10d: Invoke the Helper

Use the `write` tool to create `${scratch_dir}/grok-exec-mem-${PLAN_ID}.json` with the JSON spec above, then invoke:

```
<PYTHON> <MEMORY_HELPER> update --file <scratch_dir>/grok-exec-mem-<PLAN_ID>.json
```

The helper acquires the lock, merges, compacts, writes atomically, and prints a JSON stats summary on stdout:

```json
{
  "file": "/path/to/implement-memory/<workspace-id>.md",
  "existed_before": true,
  "stats": {
    "new_patterns": 2,
    "merged_patterns": 5,
    "categories_touched": ["Error Handling", "Testing"],
    "categories_capped": {},
    "recent_runs_dropped": 0
  }
}
```

Use these stats to report to the user:
> "Memory updated: 2 new patterns, 5 merged into existing entries."

Or if `existed_before` is `false`:
> "Memory file created with N patterns."

### Graceful Degradation

If the helper exits non-zero, log a warning with stderr and skip the memory update. The implementation is already complete and reviewed -- never fail the run due to memory flush issues. Clean up the temp JSON file regardless:

```
<PYTHON> <HOST_PY> cleanup <scratch_dir>/grok-exec-mem-<PLAN_ID>.json
```

## Rules (memory scope)

- **Memory is best-effort** -- if the `memory.py` helper fails (lock contention, malformed spec, disk full, etc.), proceed without it. Never fail a run due to memory issues.
- **Use the implement skill's `memory.py` helper** -- derive the absolute path from the implement skill's SKILL.md path announced in the system context, not from `$(pwd)`. The execute-plan skill shares the same workspace-scoped memory file as `/implement`.

## In-Progress Reporting

- After memory flush: `"Memory updated with N patterns from this run."` (or `"Memory file created with N patterns."` for first run)
