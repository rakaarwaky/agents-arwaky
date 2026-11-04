# Step 0 — Path Audit Capture

The deep-clean run audits a **path only**: a directory, package, crate, or file the user names. It never reads git diff, commits, or branches, and it never bases findings on git history.

## Argument form

```text
/deep-clean <path> [--dry-run]
```

- `<path>` — the target: a file, directory, package, or crate. Validate it exists; if it does not, stop and ask for the correct path.
- `--dry-run` — explicit only. When present: audit produces the report; nothing is executed or applied. When absent: the run is headless and autonomous — every step runs to completion without asking for permission.

## Audit scope

- **File-scoped:** audit the single file's contents (bloat, wrappers, dupes, structure).
- **Directory/package/crate-scoped:** audit everything under the path, unit by unit (Python package, Rust crate, TS package). Entry points and public export surfaces are always in scope: `__init__.py` / `__all__` / `pyproject.toml` (Python), `mod.rs` / trait definitions / `lib.rs` (Rust), barrel `index.ts` / `package.json` `exports`/`main`/`types` (TypeScript).
- The run audits **all aspects step by step**: Phase 1 dead-code cleanup → Phase 2 consolidation → the 4-lens sweep → the structural audit → tiered application → verification → report.

## Mode gate

- **Headless (default, no `--dry-run`):** proceed autonomously through every step; never block on a user question. RISKY-tier items and low-confidence items are recorded in the report's manual-review section instead of stalling the run.
- **`--dry-run`:** run steps 1–6 in report-only mode; apply nothing; the commit step (if any) is skipped.

## Completion

- The path is validated and the target units identified; mode (headless vs `--dry-run`) is fixed for the whole run; no git diff or commit was used as input.
