# Improve — Step 13: Restructuring into Pattern B step-<N>[a|b|c] variants

**Goal:** when a user asks to restructure an existing skill's `references/` from a flat or mode-based layout into numbered step files with per-language/per-runtime sub-variants, do the restructure without losing content, without breaking cross-links, and without leaving the old flat files behind.

This is the concrete application of the Pattern B decision in `step-11-reference-pattern.md`. It fires when the user names the target shape — "use the `step-<n> [a|b|c]` pattern", "make the references like systematic-debugging" — rather than asking for a general audit.

## When it fires

- User names an existing skill as the pattern to copy ("see the references on <other-skill>").
- The target skill currently has a flat `references/<topic>.md` set that is actually a pipeline (Pattern B by shape, flat by current naming).
- The target skill has per-language or per-runtime monolith files that must be split into step variants.

## Procedure

### 1. Read the exemplar first

Open the exemplar skill's `references/` directory (the one the user named) and list its files. Identify which of its files are plain step files and which are `step-<N><variant>` files. The exemplar's own `SKILL.md` Routing table is the authority for how variants are read: each variant row says which runtime/language picks it. Copy that reading model into the target skill's Routing table.

### 2. Identify the split points in any monolith

For each per-language or per-runtime monolith file in the target skill:

- Grep its `## ` headings. The split points are the phase or stage boundaries (`## Phase 1:`, `## Phase 2:`, `## Final Verification`, `## Common Mistakes`, `## Quick Reference`, `## Decision Flowchart`, `## Dry-Run Mode`, `## Tool Reference`).
- The **shared preamble** (title, purpose, rules, when-to-use, fundamental questions, language-specific KEEP/REMOVE tables) goes into the **first** variant's step file.
- The **phase body** (detection patterns, workflow steps for that phase) goes into its own step file.
- The **cross-phase tails** (verification checklists covering all phases, quick-reference commands, common mistakes, decision flowchart, dry-run mode, tool reference) go into the **last** variant's step file — they span phases, and the later step owns them so the earlier step stays focused on detection.

Record the split lines per file before editing. After the split, each original monolith is gone from the tree; its content is fully redistributed.

### 3. Rename the remaining flat files into step numbers

Every other flat reference in the target skill that is actually a pipeline step gets a `step-<N>-<name>.md` name in execution order. The number is the pipeline step, not the order in the file list — the exemplar's Routing table is the authority. Use `git mv` (not a delete + create) so history is preserved. **`mkdir -p` the destination subdirectory first** — `git mv` of multiple files into a subdirectory that does not yet exist fails with `fatal: renaming ... failed: No such file or directory` (one failure aborts the whole chain, no files moved). Update each file's `# Title` to `# Step <N>: <verb>` matching the exemplar's convention (e.g. `# Step 5: Apply Per Tier`, not `# Apply Per Tier`).

### 4. Fix every internal cross-link

After the renames, grep the whole target skill directory for each old filename. Every hit is an incomplete rename. The link sites to fix:

- `SKILL.md` Routing table rows.
- `SKILL.md` Global Rules bullets that mention a reference file by name (language routing, report format, verification gates, etc.).
- Reference-to-reference links (a step file that links to a sibling step file, or to the report-format file).
- The target skill's own `description:` and `when-to-use:` fields only if they name a reference file (rare).

Verify with one final grep: no old filename remains anywhere in the target skill's directory.

### 5. Sync the mode semantics with the restructure

A restructure into `step-<N>[a|b|c]` is often paired with a user instruction about the run's safety model (e.g. "default is headless autonomous; `--dry-run` is the only flag that makes it report-only"). If the user gives that instruction, apply it in the same pass:

- Edit `SKILL.md` `argument-hint:` to the user's exact form (e.g. `<path> [--dry-run]`).
- Edit every step file that carries a blocking approval step, a "wait for explicit approval" line, a Dry-Run Mode section, a verification checklist item, or a decision-flowchart branch. Grep the whole directory for `approv`, `wait for`, `explicit confirmation`, `default mode`, and the flag name (both bare and backtick-wrapped). Each hit is re-worded to the new semantics.
- The new default mode and the flag's gated mode must be stated in exactly two places: a `SKILL.md` Global Rules bullet (the safety-model flip, stated once) and the affected step files (the per-step application of that bullet). No third copy.

### 6. Verify the final shape

Before declaring the restructure done:

- `ls references/` of the target skill: every file starts with `step-` (Pattern B invariant — no flat files left, including no report-format file left unnumbered; report-format becomes `step-<N>-report-format.md` where N is the last pipeline step).
- Each step file's first line: `# Step <N><optional-variant>: <verb> …`.
- `SKILL.md` Routing table: every row names a step-numbered file; variant rows name all variants for that step in one row (a/b/c inline), matching the exemplar's row shape.
- Grep for the old flat filenames: zero hits.
- Grep for `approv` / `wait for` / `explicit confirmation`: every hit is in a step file that was intentionally re-worded in step 5; none describe the old blocking behavior.
- Run the tree's markdown gate on the touched files (repo-embedded skill trees run their own markdown lint over `skills/`) — the restructure often produces doubled blank lines at split points and bare opening fences that the gate catches.
- Commit scoped to the target skill's paths only; check `git diff --cached --name-only` first (repo convention: shared index in a multi-agent tree).

## Pitfalls

- **Splitting at the wrong heading.** Splitting at the first `## ` inside a monolith is wrong — that is usually the language's purpose or rules section, which is preamble. The split point is the **phase boundary**, not the first heading. Grep for `Phase 2`, `Consolidation`, `Final Verification` (or the target skill's equivalent) and split there.
- **Leaving the shared preamble in the later phase's file.** The preamble (rules, purpose, fundamental questions) belongs to the first phase's file, not the later one. A reader of the later step should not have to re-read the rules. If a section is genuinely needed by both phases (rare — a KEEP table, an EXCEPTIONS table), keep it in the earlier file and have the later file link to it by relative path instead of duplicating it.
- **Renumbering existing step files for "consistency" when the skill is not Pattern B by shape.** The pattern follows the skill's shape, not the current tree. If the target skill is decision-dispatch (two independent tools chosen by question) rather than an ordered pipeline, renumbering is the wrong move — leave per-tool references named by tool/topic. Only renumber when the user's exemplar is itself Pattern B and the target is actually one ordered pipeline.
- **Forgetting the report-format file.** A skill's `report-format.md` (or equivalent) is the last step of the pipeline, not a shared helper. It gets a `step-<N>-` prefix and becomes the final step row in the Routing table. Leaving it flat breaks the Pattern B invariant "every reference file in a Pattern B skill carries a `step-<N>` prefix — no exceptions."
- **Renaming without updating the Routing table's variant-row shape.** If the exemplar shows variant rows as one row per step with a/b/c inlined (a single row listing all three, or a `Step N` row plus a separate `Step Na/Nb/Nc` row), copy that exact row shape. Do not invent a new row layout that the exemplar does not use.
- **Moving step files into per-runtime subdirectories without rewriting cross-links.** When variants land in `references/<runtime>/` subfolders (one lane per runtime — e.g. `hermes/` vs `grok/` instead of inline `step-N[a|b]` variants), relative links in the moved files go stale: a link that was `references/<sibling>.md` from `references/step-N.md` is now `<sibling>.md`-within-same-dir but must be read from a different dir level than the reader expects, and links from the old flat location in files that were NOT moved dangle outright. After the move, grep every `](.*\.md)` link target in the whole target skill directory and re-resolve each one against its new location; do not just re-point `SKILL.md`'s Routing table, which is the link everyone thinks about and the one that misses the reference-to-reference links.
- **Committing a restructure without the safety-model sync.** A `step-<N>[a|b|c]` restructure and a safety-model flip are usually one user request. Committing only the rename and leaving the old blocking approval steps in place means the new step files describe behavior that contradicts the new default. Do the sync in the same pass, same commit.
- **Lane subfolders are whole-lane, not per-step.** A two-lane restructure (one lane per orchestrator — e.g. `hermes/` vs `grok/` instead of inline `step-N[a|b]` variants) moves the entire existing pipeline into one lane directory, unchanged, and writes the new short lane (plan → spawn → wait → verify/ship → report, typically 4 steps) into the other. Both lanes renumber from step 0 independently — the lanes hand off through artifacts (worktree + summary/review/state files on the scratch dir), not a continuing step counter. Per-step `step-<N>[a|b]` variant files only apply when one agent executes both branches; two different agents each running their own full pipeline get whole-lane subfolders instead. The `SKILL.md` Routing table splits into one table per lane, and the lane is picked by who is reading the skill (the agent that owns the run), not by a flag.
- **A whole-lane `git mv` into an unchanged-basename subdirectory is link-safe; any rename alongside it is not.** When the move is `references/step-N-name.md` → `references/<lane>/step-N-name.md` with the basename untouched, every same-directory sibling link inside the moved files (`](step-M-name.md)`) keeps resolving — and the only cross-link breakage comes from `SKILL.md`'s old Routing rows / Global-Rules name mentions plus any same-directory link whose *target* file was also renamed in the same pass. Grep the moved lane for every old basename that got renamed, not just the ones you remember moving; a move that also renumbers files invalidates every sibling `href` in the moved directory, and the step-4 re-grep must cover `](*.md)` targets across the whole moved directory, not just `SKILL.md`.
- **Rewrite the Routing tables as two separate edits — one patch call per table, never one call spanning both.** The two tables (old lane re-pointed, new lane added) are each dense blocks of markdown; a single `patch` call whose `old_string` covers both reliably trips the patch tool's escape-drift check (a literal `\"` anywhere in either table body makes the tool reject the whole call even when the file on disk has no such sequence), and a call that only re-points the old table while the new lane's table is still absent leaves a SKILL.md with one lane pointing at moved files and no rows at all for the new lane. Re-point the old table's rows first (one `patch`, `old_string` = just that table block), verify with a grep for the new lane-prefixed hrefs, then add the new lane's table as a second `patch` (or a targeted append if it sits at the file's end). `git show --stat` on the SKILL.md edit must list exactly one file; a second table that silently never landed means the patch call was rejected and the retry skipped it.
