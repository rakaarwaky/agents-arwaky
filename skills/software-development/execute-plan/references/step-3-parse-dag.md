# Step 3 Parse DAG

## Step 3: Parse PR Plan DAG

Read the design document at `<design_doc_path>` using `read_file`.

### Prefer the bundled validator

Run the bundled validator first — it encodes the exact parsing, validation, and level-assignment rules, so a malformed plan fails with a precise error before any subagent is spawned:

```bash
<python> <HOST_PY_DIR>/validate-plan.py <design_doc_path>
```

- `<HOST_PY_DIR>` is the same directory as `host.py` (resolved in Setup). On this host that is `scripts/validate-plan.py` relative to this `SKILL.md`.
- Exit `0`: parse the JSON report. `linearized_order`, `level_assignments`, `pr_count`, and `max_parallelism` are authoritative — store `linearized_order` in the state file and skip to Step 4 (it only computes branch names from the parsed nodes; it must not re-derive the order).
- Exit `1`: the report's `errors` list names the offending PRs (duplicate id, unresolved dependency, cycle, malformed entry). Report the first error to the user and stop — do not proceed to Step 4 or spawn any subagent.
- Exit `2`: usage or IO error (path not found, unreadable). Report and stop.

Only parse by hand if `validate-plan.py` is missing from `scripts/`. The manual procedure below is the reference implementation the validator mirrors; both must agree on `id`, `slug`, `dependencies`, `level`, and `linearized_order`.

Extract the `## PR Plan` section. Parse each PR entry from `### PR N:` headings into a structured representation:

```
PRNode {
    id: string           // e.g., "pr-1", "pr-2" -- derived from the PR number
    title: string        // PR title (text after "### PR N: ")
    slug: string         // URL-safe slug: lowercase, spaces to hyphens, non-alphanumeric removed, truncated to 50 chars
    description: string  // From the "Description:" or "**Description:**" bullet
    files: string[]      // From the "Files/components affected:" bullet
    dependencies: string[] // From the "Dependencies:" bullet, parsed as PR ids
    level: int           // Computed in Step 4
    status: string       // "pending"
    branch: string       // Computed after level assignment
    subagent_id: string  // null initially
    worktree_path: string // null initially
    base_sha: string     // null initially -- branch point before implementation
    commit_sha: string   // null initially -- HEAD after all commits (implementation + fixes)
    error: string        // null initially
    reviewer_configs: object[] // [] initially -- per-PR reviewer config objects, populated in Step 7.0.
                               // Each entry: {subagent_id, persona_to_inject, specialization, review_file}.
                               // Effort 1 holds general + simplicity, each with its own
                               // individual review_file. Always merge. See Step 7.
    review_rounds: int   // 0 initially
    started_at: string   // null initially
    completed_at: string // null initially
    worktree_cleaned: bool // false initially; set true by Step 10a (per-PR prologue) or Step 11 (safety net) after `orca worktree rm` succeeds. Step 11 uses this to stay idempotent across resumes.
    orca_worktree_id: string // null initially; the Orca worktree address <repoId>::<worktreePath> from `orca worktree create --json`
}
```

**Parsing strategy:**

1. Find the `## PR Plan` section by scanning for the heading.
2. Split into individual PR entries at each `### PR` heading.
3. For each entry:
   - Extract the PR number and title from the heading (e.g., `### PR 1: Add retry configuration types`).
   - Extract `Files/components affected:` from the bullet list (split by comma).
   - Extract `Dependencies:` from the bullet list. Parse references like "PR 1", "PR 2" into ids like "pr-1", "pr-2". "None" means empty dependencies.
   - Extract `Description:` from the bullet list.
   - Generate the slug from the title:
     1. Lowercase the title.
     2. Replace spaces and underscores with hyphens.
     3. Remove any character that is not `[a-z0-9-]`.
     4. Collapse consecutive hyphens into a single hyphen.
     5. Strip leading and trailing hyphens.
     6. Remove the suffix `.lock` if present (defensive -- dots are already removed in step 3, but this guards against future validation changes; git rejects refs ending in `.lock`).
     7. Truncate to 50 characters. If truncation lands mid-hyphen-sequence, trim trailing hyphens after truncation.
     8. If the result is empty after all transformations, use `"unnamed"`.

     The resulting slug is safe for use in git branch names: no spaces, no `..`, no control characters, no `~^:?*[\`, no trailing `.lock`, no leading/trailing dots, no consecutive dots.
   - Set `id` to `"pr-N"` where N is the PR number.

4. Validate the DAG:
   - All dependency references must resolve to valid PR ids.
   - There must be no cycles. Detect cycles by attempting topological sort -- if it fails, report the cycle and stop.
   - Every PR must have a unique id.

If parsing fails (missing PR Plan section, malformed entries, unresolved dependencies, cycles), report the error with details and stop.

Store the parsed nodes in `dag.nodes`.

Report to the user: `"Parsed PR Plan: <N> PRs found."`

