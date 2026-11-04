# Verification Gates

After any removal, merge, or restructuring, in this order: static/lint check clean →
format check clean → type/compile check clean → full test suite passes → the package/crate
still imports or resolves at its entry point → downstream consumers still build → no stale
references to deleted or renamed names (grep the old names). Exact commands per language:

- Python: [`python.md`](python.md) § Verification
- Rust: [`rust.md`](rust.md) § Verification
- TypeScript: [`typescript.md`](typescript.md) § Verification

Each language reference also carries the **Verification Checklist** (Phase 1 / Phase 2 /
Final) and **Common Mistakes** tables.

For audit findings: tie every finding to specific files/lines in the diff; for each blocker
name the concrete code-judo move that resolves it (or why none exists); a reviewer
re-reading the diff cold must be able to reproduce every finding from the code alone.

**Bugs found.** If a reviewer surfaced a genuine correctness bug, list it in a dedicated
`## Bugs found` section of the report — separate from the cleanup fixes, with its own
verification standard. Do not fold bugs into the SAFE/CAREFUL/RISKY cleanup tiers.

## Rollback & Commit

Rollback via the snapshot: restore a single file from history, or reset the cleanup
branch. Commit only after all gates pass, with a descriptive message itemising counts
removed (stubs, thin wrappers, duplicates, unused files, unused imports, commented-out
code), files merged, and structural changes applied — per-language commit-message
templates are in the references.

## Completion

- All gates in the order above pass; stale-reference grep is clean; any genuine bug is reported in the dedicated "Bugs found" section, not the cleanup tiers.
