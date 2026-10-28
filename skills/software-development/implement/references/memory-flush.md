# Step 6: Memory Flush — full procedure (factored from implement/SKILL.md)

The implement SKILL.md carries a short "Step 6" summary; the complete procedure below (sub-steps 6a–6d, the memory file format, and helper exit codes) is loaded from this reference when the loop exits with 0 open issues.

## Step 6: Memory Flush

After the loop terminates with 0 open issues, update the workspace memory file with patterns from this run. The orchestrator performs this directly using its own tools — no subagent is needed for this step.

The write goes through `"${PYTHON}" "${MEMORY_HELPER}" update --file <spec>` so that:
- The path resolves to the **shared workspace-scoped file** (`$HOME/.grok/implement-memory/<workspace-id>.md`), not a per-worktree file.
- An exclusive lock (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows; no `flock(1)` shell binary required) is held during the read-merge-write, so a /implement run in another worktree of the same repo can't clobber this update.
- Dedup against existing entries is enforced **deterministically** (case- and whitespace-insensitive match within each category).
- Compaction is enforced: each category is capped at 25 entries (lowest-count entries dropped first); Recent Runs is capped at 20 entries (oldest dropped).
- Strict input validation: malformed types (e.g., a non-list `key_patterns`, a string where a dict is required, a calendar-invalid `date`) fail fast with exit code 4 and a clear error message rather than silently corrupting the file.

### Step 6a: Collect & Categorize This Run's Patterns

1. Use the `issue_patterns` list accumulated during Step 3 across all rounds. This list contains a one-line description of every distinct issue that was open at any review checkpoint during the run.
2. **Generalize each pattern.** The memory file exists to help *future* runs on *different* tasks — patterns that reference this task's specific code, variable names, or domain objects are useless noise. Strip implementation-specific details (file names, variable names, type names, function names, domain-specific terms) and rewrite each pattern as a reusable principle that applies across different codebases and tasks:
   - Bad: "Missing error type `RetryableError` in retry handler list" → Good: "Missing entries in error-type or configuration allowlists"
   - Bad: "JWT token not validated for expiration" → Good: "Missing expiration/TTL validation on tokens or credentials"
   - Bad: "`calculateTotal` function exceeds 80 lines" → Good: "Functions exceeding reasonable length without decomposition"
   - Bad: "No test for `handleUserAuth` error path" → Good: "Missing tests for error/edge case paths"
   - Bad: "Missing null check on `userId` parameter" → Good: "Missing null/undefined checks on function inputs"
   If a pattern is *already* general (e.g., "Missing null checks on function inputs"), keep it as-is. If multiple task-specific patterns generalize to the same reusable principle, collapse them into one entry.
3. Categorize each generalized pattern into one of: Error Handling, Testing, Security, Code Quality, Naming, Documentation, Performance, or another short category name as appropriate. Reuse existing category names from `existing_patterns_snapshot` (captured in Step 0) whenever the pattern fits — do not invent a near-duplicate category like "Error-Handling" or "Tests" when one already exists.
4. For each pattern, write a concise one-line description. Keep descriptions on a single line; the helper collapses any embedded newlines but it's cleaner to write them without.

### Step 6b: Harmonize Phrasing Against Existing Entries

Before handing generalized patterns to the helper, dedup at the *phrasing* level using `existing_patterns_snapshot`:

1. For each of this run's patterns, scan `existing_patterns_snapshot` for an entry in the same (or semantically equivalent) category whose description means the same thing — even if worded differently. Examples of matches:
   - "missing null check on input" ≈ "No null validation for function parameters"
   - "functions over 50 lines" ≈ "Long functions without decomposition"
   - "no tests for error path" ≈ "Missing tests for failure cases"
2. **If a semantic match exists:** replace this run's description with the **exact existing description string** (so the helper's normalised match will collapse them onto the same entry).
3. **If no match exists:** keep your concise description as-is. It will be added as a new entry.
4. **Within this run's own list:** also dedup by phrasing — if you have two patterns that mean the same thing, collapse them to a single entry (the helper would otherwise count them as two distinct hits, which is fine but slightly inflates new-pattern stats).

The helper will also do a final case/whitespace/punctuation normalisation, but it cannot infer semantic equivalence — that's the orchestrator's job here. Skipping this step leads to the file accumulating near-duplicates over time.

### Step 6c: Build the Update Spec

Construct a JSON object with this shape (omit `run` only if you want to record patterns without logging a run; in normal flow, always include both):

```json
{
  "patterns": [
    {"category": "Error Handling", "description": "Missing null/undefined checks on function inputs"},
    {"category": "Testing", "description": "Missing tests for error/edge case paths"}
  ],
  "run": {
    "date": "2026-04-23",
    "description": "Add retry logic to blackbox client",
    "rounds": 2,
    "issues_by_severity": {"bug": 1, "suggestion": 1, "nit": 5},
    "key_patterns": ["Missing entries in error-type allowlists", "Incomplete configuration validation"],
    "specializations": ["general", "simplicity"]
  }
}
```

Field notes (the helper rejects wrong-typed input with exit code 4 and a clear error message identifying the offending field; empty-or-null input falls back to defaults or is silently skipped per the per-field rules below):
- `patterns[]`: each entry must be an object. `category` must be a string (defaults to `"Other"` if empty/null). `description` must be a string; **null and omitted are treated identically** (both result in a silent skip with no error).
- `patterns[].description`: one-line, harmonised in Step 6b. Newlines/tabs are collapsed to single spaces; internal multi-space runs are preserved.
- `run` must be an object (not a list, not a string). Send `null` or omit it entirely to skip the Recent Runs entry.
- `run.date`: a string in `YYYY-MM-DD` format. Calendar-invalid dates like `2026-13-99` are rejected. Pass `null`, empty string, or whitespace-only string and the helper fills in today's UTC date.
- `run.description`: the user's implementation request, trimmed to a short label. Must be a string (or `null`/omitted to fall back to `"(no description)"`). The helper strips ALL double-quote characters from the description and then wraps it in exactly one outer pair, so internal quotes never produce broken nested-quote markup. (`Add retry "logic" to client` becomes `"Add retry logic to client"`.) If you need to preserve quotes verbatim, escape them yourself before submission — the helper assumes the description is a free-form label, not a structured string.
- `run.rounds`: `round_count` as an integer. Booleans, floats, strings, and lists are rejected. Zero is accepted as-is (structurally unreachable in the actual /implement loop, but not enforced).
- `run.issues_by_severity`: derived from `total_issues_by_severity`. Must be an object with string keys and integer values (or `null`/omitted to skip the `**Issues**` body line entirely). Zero-count severities are silently dropped from the rendered summary; if all severities are zero (or the object is empty) the helper omits the `**Issues**` body line entirely.
- `run.key_patterns`: must be a list of strings (or `null`/omitted to skip the `**Key patterns**` body line). Pick the 2-3 most-significant patterns from this run. **Apply the same generalization rules as Step 6a** — strip task-specific names and rewrite as reusable principles. Two implementable options, pick consistently across runs:
  - **Option A (recommended): severity-ranked.** Re-read the latest merged review_file (still on disk at this point in the loop). Each issue has a `Severity:` tag. Take 1-2 of the highest-severity issues first (bugs > suggestions > nits), then top up with the next-highest severity until you have 3 entries. This sees only **final-round survivors** (issues that the implementer actually had to address) which is the natural "most-significant" reading.
  - **Option B (lower-effort): recency-ranked.** Take the **last 2-3 entries** of `issue_patterns` (the list grows by appending per round in Step 3, so the tail is the most-recent round's issues). This sees **cross-round accumulation** including issues that were introduced and fixed mid-loop. Use this only if re-reading the review_file is impractical — the resulting `key_patterns` will sometimes include issues that ended up wontfix or were ephemeral.
  - **Pick one option and stick with it for the run.** The two options return semantically different sets, so mixing them across runs makes the Recent Runs log inconsistent.
- `run.specializations`: must be a list of strings (or `null`/omitted to skip the `**Specializations used**` body line). Strip the `-N` suffix from `general-2`/`general-3` first so the list is the set of distinct specialization classes (e.g., `["general", "security", "simplicity"]`, not `["general", "general-2", "security"]`); deduplicate. Include `simplicity` when that specialist ran (always).

### Step 6d: Invoke the Helper

Use the `write` tool to create `${scratch_dir}/grok-mem-${IMPL_ID}.json` with the JSON spec above (using a temp file avoids quoting issues that heredocs introduce), then invoke the helper via `run_terminal_command`:

```
<PYTHON> <MEMORY_HELPER> update --file <scratch_dir>/grok-mem-<IMPL_ID>.json
```

The helper acquires the lock, parses the existing file, merges, compacts, writes atomically, and prints a JSON stats summary on stdout (pretty-printed with `indent=2`):

```json
{
  "file": "/Users/.../implement-memory/proj-d5016f47e5cb.md",
  "existed_before": false,
  "stats": {
    "new_patterns": 2,
    "merged_patterns": 5,
    "categories_touched": ["Error Handling", "Testing"],
    "categories_capped": {},
    "recent_runs_dropped": 0
  },
  "total_categories": 4,
  "total_patterns": 17,
  "total_recent_runs": 12
}
```

Key fields:
- `existed_before`: `true` if the file existed before this update, `false` if the helper just created it. Use this for the report wording.
- `stats.categories_capped`: dict of `{category: dropped_count}` for any category that exceeded `MAX_PATTERNS_PER_CATEGORY` and had its lowest-count entries dropped. Empty dict in the typical case.

Use these stats to report to the user:
> "Memory updated: 2 new patterns, 5 merged into existing entries (file at <file>)."

Or if `existed_before` is `false`:
> "Memory file created at <file> with N patterns."

### Memory File Format

The helper writes a markdown file with this structure:

<!-- mirror-of: scripts/memory.py DEFAULT_HEADER -->
<!-- The 5-line block immediately following this comment must match -->
<!-- '\n'.join(memory.DEFAULT_HEADER) verbatim. The drift-check unit -->
<!-- test TestDocsConsistency.test_skill_md_default_header_matches -->
<!-- asserts this on every test run. -->
```markdown
# Implementation Review Patterns

> This file is maintained by the /implement skill.
> It records common issues found during implementation reviews to help avoid them in future runs.
> Shared across all working directories that resolve to the same workspace id.

## Common Issues

### Error Handling
- Missing null/undefined checks on function inputs (seen 5 times)
- Not handling async errors in promise chains (seen 3 times)
- Missing error logging before re-throwing (seen 2 times)

### Testing
- Missing tests for error/edge case paths (seen 8 times)
- Tests that don't assert on error messages, only error types (seen 3 times)
- No integration tests for new API endpoints (seen 2 times)

### Security
- User input not validated before database queries (seen 2 times)
- Missing rate limiting on new endpoints (seen 1 time)

### Code Quality
- Functions exceeding 50 lines without decomposition (seen 4 times)
- Magic numbers without named constants (seen 6 times)
- Inconsistent naming conventions within new code (seen 3 times)

## Recent Runs

### 2026-04-23 — "Add retry logic to blackbox client"
- **Rounds**: 2
- **Issues**: 7 total (1 bug, 1 suggestion, 5 nits)
- **Key patterns**: Missing entries in error-type allowlists, incomplete configuration validation
- **Specializations used**: general

### 2026-04-22 — "Implement user auth endpoints"
- **Rounds**: 3
- **Issues**: 12 total (3 bugs, 4 suggestions, 5 nits)
- **Key patterns**: Missing expiration/TTL validation on tokens, missing rate limiting on new endpoints, missing tests for error/edge case paths
- **Specializations used**: general, security
```

Notes on the format:
- Within each category, entries are sorted by count desc then description asc (case-insensitive).
- `seen 1 time` (singular) and `seen N times` (plural) are both produced and parsed.
- `—` (em-dash), `–` (en-dash), and `-` (ASCII hyphen) are all accepted as separators in run headers.
- The helper preserves any custom lines you add to the header (anything before `## Common Issues`) on round-trip. Custom freeform paragraphs **inside** a category in `## Common Issues` are not preserved — only `### Category` headers and well-formed `- desc (seen N time(s))` bullets survive. **Caveat:** anything written to the file before the first `## Common Issues` heading becomes part of the preserved header indefinitely, including unintentional garbage from a hand-edit. To reset a corrupted file, delete it and the helper will recreate it with the default header on the next `update`. If you delete the header itself (leaving the file starting at `## Common Issues`), the helper re-injects the default header on the next render — not byte-stable, but the data survives.
- Both the memory file and its sibling `.lock` file are written and then chmodded to mode `0o600` (owner read/write only, best-effort — if a cross-user race makes the chmod fail, the file's umask-default mode is preserved). The memory file may contain security-review patterns and `key_patterns` drawn from non-public source review, so we deliberately keep it owner-only on shared hosts (the workspace id is a deterministic SHA-256 of the canonical remote URL, so an unprivileged account that knows or guesses the public-repo URL could otherwise read the file directly). In the typical single-user case both files end up at `0o600` regardless of the process umask. The lock file's content is irrelevant; it exists purely as an `flock` target.

### Graceful Degradation

If the helper exits non-zero (lock contention timeout, malformed spec, disk full, etc.), log a warning with the helper's stderr and skip the memory update. The implementation is already complete and reviewed at this point — never fail the run due to memory flush issues. Also remove the temp JSON spec file in the cleanup step regardless.

Exit codes:
- `0`: success.
- `1`: unexpected I/O error (disk full mid-write, permission flips during execution, FS races). The stderr message says `memory.py: I/O error: ...`.
- `2`: workspace id could not be determined (cwd unreadable and `$HOME` unset — very rare).
- `3`: lock could not be acquired within 30 seconds (another concurrent /implement run is monopolising the file; usually retrying once works).
- `4`: stdin JSON is missing, malformed, or fails type validation. The stderr message identifies the offending field. Surface it verbatim in the report so the user can see what was wrong with the spec.
