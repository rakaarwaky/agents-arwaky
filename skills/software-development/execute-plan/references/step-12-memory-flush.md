# Step 12 Memory Flush

## Step 12: Memory Flush

After cleanup, update the workspace memory file with patterns from this run. The orchestrator performs this directly using its own tools -- no subagent is needed. This step follows the same protocol as the `/implement` skill's Step 6 (see `.grok/skills/implement/SKILL.md` for full helper documentation, exit codes, and file format details).

### Step 12a: Collect & Categorize This Run's Patterns

1. Use the `issue_patterns` list accumulated during Step 7b and Step 7c re-reviews across all PRs and review rounds.
2. **Generalize each pattern.** The memory file exists to help *future* runs on *different* tasks — patterns that reference this task's specific code, variable names, or domain objects are useless noise. Strip implementation-specific details (file names, variable names, type names, function names, domain-specific terms) and rewrite each pattern as a reusable principle that applies across different codebases and tasks:
   - Bad: "Missing error type `RetryableError` in retry handler list" → Good: "Missing entries in error-type or configuration allowlists"
   - Bad: "JWT token not validated for expiration" → Good: "Missing expiration/TTL validation on tokens or credentials"
   - Bad: "`calculateTotal` function exceeds 80 lines" → Good: "Functions exceeding reasonable length without decomposition"
   - Bad: "No test for `handleUserAuth` error path" → Good: "Missing tests for error/edge case paths"
   - Bad: "Missing null check on `userId` parameter" → Good: "Missing null/undefined checks on function inputs"
   If a pattern is *already* general (e.g., "Missing null checks on function inputs"), keep it as-is. If multiple task-specific patterns generalize to the same reusable principle, collapse them into one entry.
3. Categorize each generalized pattern into one of: Error Handling, Testing, Security, Code Quality, Naming, Documentation, Performance, or another short category name. Reuse existing category names from `existing_patterns_snapshot` (captured in Step 0) whenever the pattern fits.
4. For each pattern, write a concise one-line description. Keep descriptions on a single line.

### Step 12b: Harmonize Phrasing Against Existing Entries

Before handing generalized patterns to the helper, dedup at the *phrasing* level using `existing_patterns_snapshot`:

1. For each of this run's patterns, scan `existing_patterns_snapshot` for a semantically equivalent entry. If a match exists, replace this run's description with the **exact existing description string**.
2. If no match exists, keep the concise description as-is.
3. Within this run's own list, also dedup by phrasing -- collapse patterns that mean the same thing to a single entry.

### Step 12c: Build the Update Spec

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
    "specializations": ["general", "tests", "simplicity"]
  }
}
```

Field notes:
- `run.date`: pass `null` and the helper fills in today's UTC date.
- `run.rounds`: sum of `review_rounds` across all completed PRs.
- `run.issues_by_severity`: derived from `total_issues_by_severity` (accumulated in Step 7b and Step 7c re-reviews across all PRs).
- `run.key_patterns`: pick 2-3 most-significant patterns (severity-ranked: bugs > suggestions > nits). **Apply the same generalization rules as Step 12a** — strip task-specific names and rewrite as reusable principles.
- `run.specializations`: collect every `config.specialization` from every PR's `reviewer_configs` and deduplicate — the fixed Step 7 panel makes this always `["general", "tests", "simplicity"]`.

### Step 12d: Invoke the Helper

Resolve `<MEMORY_HELPER>` exactly as in Step 1 (*Resolve the helper path*) — absolute path, inlined. Use the `write` tool to create `${scratch_dir}/grok-exec-mem-${PLAN_ID}.json` with the JSON spec above, then invoke:

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

Map the `stats` output onto the report strings in *In-Progress Reporting* below (`new_patterns` / `merged_patterns`, and `existed_before` for created-vs-updated wording).

### Graceful Degradation

If the helper exits non-zero, log a warning with stderr and skip the memory update. The implementation is already complete and reviewed -- never fail the run due to memory flush issues. Clean up the temp JSON file regardless:

```
<PYTHON> <HOST_PY> cleanup <scratch_dir>/grok-exec-mem-<PLAN_ID>.json
```

## In-Progress Reporting

- After memory flush: `"Memory updated: <new_patterns> new patterns, <merged_patterns> merged into existing entries."`
- After memory flush (first run): `"Memory file created with <N> patterns."`
