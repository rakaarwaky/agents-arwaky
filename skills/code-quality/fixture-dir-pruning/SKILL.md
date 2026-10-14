---
name: fixture-dir-pruning
description: Prunes test/lint fixture dirs by code-coverage redundancy.
---

# Fixture-Dir Pruning

Deterministic test/lint fixtures (a linter's `workspaces-bad/` or equivalent intentionally-violating fixture dirs) are **deliberate test data**, not dead code. Prune them by *coverage redundancy*, never by "unused" heuristics. The whole point of a fixture is to emit the codes a linter must detect. This is a distinct task class from generic dead-code cleanup: the gate is "which codes are still covered", not "which files are imported".

## When to Use

- A fixture dir has grown too large (hundreds of files) and the user asks to shrink it.
- Before converting fixture dirs to submodules or vendoring (verify in-tree redundancy first).
- When a per-language CI floor is set on scan-visible code counts.

## Procedure

1. **Reproduce the baseline first.** Build the linter's own binary (`cargo build --bin <cli>` or the equivalent) and run its scan over the fixture dir. Record the set of unique violation codes and the per-language code sets. This is the source of truth; do not guess from file names.
2. **Map codes to providers per language.** Parse the scan report into `{language: {dir: {codes}}}`. A fixture dir is *redundant* only if every code it emits is also emitted by another fixture dir **in the same language**. Cross-language coverage does not count: a code covered by the Rust fixture does NOT cover it for the JS/TS fixture.
3. **Compute a minimal set cover per language**, not "drop everything except two." Greedy set-cover gives the true floor. Deleting a redundant dir that is the *only* holder of a code in its own language drops that language's count below the CI floor.
4. **Honor the per-language gate, not just the aggregate.** CI typically has BOTH an aggregate `scan workspaces-bad` code-count gate AND a per-language floor (e.g. `>= N codes per language`). Check both in `ci.yml` and the test doc before deleting. A prune that keeps the aggregate count but breaks a per-language floor still fails CI.
5. **Respect test-hardcoded fixture paths.** Grep the test tree for string literals like `"workspaces-bad/packages/<name>/..."` before deleting any fixture dir. Tests that reference a concrete fixture file by path break on any shard you did not run. Keep any dir a test hardcodes, even if its codes look redundant.
6. **Verify after every delete batch.** Re-run the linter scan (aggregate + each per-language root) and confirm: total codes unchanged, every per-language set unchanged (or intentionally reduced per step 4), the clean/"good" fixture still yields 0 violations, and the fixture-dir's own build manifests (`Cargo.toml` members, `package.json` `workspaces`) still resolve. Fixtures are standalone — deleting one does not break the main build — but a dangling manifest entry does.
7. **Update the doc count tables.** A fixture prune changes file counts recorded in the test/CI doc (e.g. `| JS/TS | 150 |` cells and any `workspaces-bad/packages` file-count assertions). Bump them to the post-prune actuals in the same PR, or the doc-consistency gate fails.
8. **Commit in logical chunks:** the deletion, then the doc-count update. A restore (putting a dir back for the step-4 floor) is its own commit with a message naming the code it restores.

## Pitfalls

- **Probe a deleted dir's codes from the original commit without polluting the branch.** `git checkout <base-commit> -- <fixture-dir>` stages the deleted files back into the index; carelessly `git reset` / `checkout -- .`-ing afterward either resurrects the whole dir or loses the prune. Clean up with `git reset -q` + `rm -rf <dir>` + `git checkout HEAD -- <dir-parent>` and re-verify `git status` is clean before committing.
- **A stale rule-catalog count is not a bug you may fix on a guess.** Rule-count drift between docs (e.g. `35 rules` vs `34`) usually means one rule is *defined but has no scan fixture*, not that a doc number is wrong. Count the catalog table's distinct codes yourself before changing any doc number — patching `35` to `34` on a guess can desync the doc from the per-rule matrix and the CI threshold that are locked in lockstep. When in doubt, open a separate issue rather than "correcting" the count in a prune PR.
- **Per-language vs aggregate are independent gates.** A scan can emit 30 codes aggregate while a per-language floor demands 27 in each of 3 languages; the aggregate passing says nothing about the per-language pass. Always check both.

## Verification Gates (after every delete batch, in order)

1. linter scan aggregate code count unchanged (or intentionally reduced per the doc).
2. linter scan per-language code counts meet the documented floor.
3. clean/"good" fixture still yields 0 violations.
4. fixture-dir build manifests resolve (no dangling `Cargo.toml` member / `package.json` workspace entry).
5. test suite for the linter crate passes (the regression tests that hardcode fixture paths).
6. doc count tables updated to post-prune actuals.

## Rollback

Rollback via the pre-delete snapshot: `git checkout HEAD -- workspaces-bad/packages/<dir>` to restore a single dir, or `git reset` the prune branch to undo the whole batch. A restore-for-floor (step 4) is a forward commit, not a rollback — message it as "keep <dir> for <code> coverage".

## Dry-Run Mode

When the user says "just show me what you'd remove": run steps 1–5 (baseline, provider map, set-cover, gate check, hardcoded-path grep), produce the report of which dirs are redundant and which codes each still covers, **do NOT execute any deletions**, present the report, and wait for explicit approval. This is the default for first-time fixture prunes.
