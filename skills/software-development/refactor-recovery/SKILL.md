---
name: refactor-recovery
description: Resume a mid-flight code refactor left inconsistent.
category: software-development
---

## When to use

Use when resuming a code refactor that was interrupted mid-flight and left the tree inconsistent: some files moved but not all, imports half-fixed, `__init__.py` re-exports pointing at moved-or-deleted sources, dead duplicates left behind. Also covers mass import rewrites across many consumer files.

## Procedure

### 1. Establish ground truth

Before changing anything, measure three layers:

- **Staged**: `git diff --cached --name-only` — what a prior session prepared but may not have landed.
- **On disk**: `find <pkg> -name '*.py'` per package — what actually exists.
- **Consumers**: `grep -rln "from ...common.<moved_module> import" <root>` — what still points at the old location.

If `git reset` was run mid-session, staged-new files may never have landed on disk. Treat on-disk state as truth; don't trust the index.

### 2. Map the target architecture

Decide where each moved module lives in the final structure. For a flat-package-to-domain split, each `common/XX` → `<domain>/XX` with a self-contained `__init__.py`. For a domain-to-flat collapse, `shared/<domain>/XX.py` → `shared/XX.py`. Write the map down before moving files. Derive the map from `git show <commit> --name-status`, not from the user's description — the commit is the authoritative source of where each file actually went (or was deleted).

### 3. Finish moving files

Move remaining files from old to new location, one package at a time. Verify each move landed with `ls <new_pkg>/`. Large chained shell commands may hit shell-safety limits — move in small batches.

### 4. Rewrite `__init__.py` re-exports

Each domain package gets a self-contained `__init__.py` re-exporting its public symbols. Read the source file's actual `def`/`class`/CONSTANT names — do not guess. A re-export of a non-existent symbol breaks every consumer that imports from the package.

Rewrite the emptied package's `__init__.py` (e.g. `common/`) to expose only what stays (taxonomy backbone: constants, errors, value objects).

### 5. Sweep consumer imports

Rewrite every `from ...common.<moved_module> import` → `from ...<domain>.<moved_module> import`. For many files, use a Python script with `Path.rglob` + string replace — grouped shell commands can hit shell-safety filters.

After the sweep, re-grep to confirm zero remaining references to moved `common.*` modules.

### 6. Delete dead duplicates

After moving a file out of a package, delete the old copy. A stale duplicate that a rewritten `__init__.py` or consumer still references causes confusing import errors.

### 7. Verify

Run the project's quality gate. Fix remaining import errors one at a time, re-reading the source file each time rather than guessing symbols.

## Pitfalls

- **Read source before re-exporting.** Write `__init__.py` symbols from the source file's actual `def`/`class`/CONSTANT names — guessing produces import errors that surface only when consumers load the package.
- **Delete the old copy after moving.** A stale duplicate left in the old location may still be referenced by a rewritten `__init__.py` or consumer.
- **Use Python for mass import rewrites.** Large chained `mv`/`grep`/`sed` shell commands can hit shell-safety filters; `execute_code` with `Path.rglob` + string replace is reliable for sweeping many files.
- **Don't trust a reset index.** If `git reset` ran mid-session, staged-new files may never have materialized on disk. Check on-disk state, not the index.
- **Keep domain `__init__.py` self-contained.** A domain package's `__init__.py` must not import from `common.*` for modules moved out of `common/` — re-exports must stay within the domain.
- **Stale config paths survive the refactor.** When SSOT config files (manifest.json, version.txt, env examples) move from `modules/shared/config/` to a new location (e.g. repo-root `config/`), fixing `repo_root()` alone is not enough. Every utility that constructs a config path with a hardcoded `root / "modules" / "shared" / "config" / ...` also breaks — scan the moved utilities (`utility_version.py`, `utility_version_cli.py`, `utility_manifest_reader.py`, and any `capabilities_*.py` that builds paths from `repo_root()`) for the old prefix and rewrite each one. Run the quality gate with `repo_root()` resolving correctly, then fix each path error the gate reports.
- **`repo_root()` depth must match the file's actual location.** A `parents[N]` index that was correct before the move may be wrong after. The file's depth relative to repo root is `len(Path(__file__).resolve().parts) - len(repo_root().parts)`. If the file moves deeper (e.g. `common/utility_paths.py` → `paths/utility_paths.py`, one level deeper), bump the index and update any docstring that states the depth so the two cannot drift apart.
- **Environment-variable root overrides must be soft-fallback, not hard-fail.** When an env var like `AGENTS_ARWAKY_ROOT` points at the wrong tree (e.g. the main checkout while running from a git worktree), hard-failing on `repo_root()` makes the tool unusable. Instead: honor the env var only when it actually contains the anchor file; otherwise fall through to discovery from the running code's own location, which always works for the tree the code is loaded out of.
- **Facade modules preserve backward-compat import paths.** When many consumers import from a module that is being removed or relocated (e.g. `modules.doctor.src.capabilities_manifest_reader`), create a thin facade at the old import path that re-exports from the new location. This avoids a second import-swap pass across the consumer tree. Delete the facade once all consumers have been migrated.

## References

- `references/flat-to-domain-migration.md` — recipe for splitting a flat utility package into domain packages.
- `references/domain-flattening.md` — recipe for collapsing domain packages into a flat root (reverse direction): enumerate three-way, recover deleted files from git history, rewrite imports via Python regex, split package-level imports by symbol, verify with compileall + import smoke-test + quality gate.
