---
name: deep-clean
description: "Unified code-quality skill that subsumes cleanup-consolidate, strict-code-quality-review, and simplify-code: remove dead code, merge duplicate files, audit spaghetti growth and giant files, and restructure for maintainability. Use for a full pre-merge audit or post-refactor cleanup across Python, Rust, and TypeScript."
when-to-use: "Use for any of: dead-code cleanup (ruff/vulture/knip/clippy/udeps), consolidation of overlapping files into single cohesive modules, harsh structural maintainability audit (abstraction quality, spaghetti-condition growth, 1k-line file boundaries), or simplification of recent changes over a branch, diff, or module (the 4-agent simplify sweep — reuse/quality/efficiency/altitude reviewers). Use before merge, before release, or after refactoring. --dry-run reports without executing."
argument-hint: "[--dry-run] [diff or module path]"
metadata:
  tags:
    - python
    - rust
    - typescript
    - cleanup
    - consolidation
    - bloat
    - stubs
    - thin-wrappers
    - dead-code
    - orphan
    - unused-files
    - merge
    - deduplication
    - spaghetti
    - maintainability
    - code-judo
    - giant-files
  related_skills:
    - fix-bypass
    - lint-arwaky
    - create-capabilities
    - create-agent
  triggers:
    - deep clean
    - deep clean python
    - deep clean rust
    - deep clean typescript
    - clean bloat
    - clean bloat python
    - clean bloat rust
    - clean bloat typescript
    - remove dead code
    - remove dead code python
    - remove dead code rust
    - remove dead code typescript
    - find unused files
    - find unused files python
    - find unused files rust
    - find unused files typescript
    - remove stubs
    - remove thin wrappers
    - remove unused imports
    - remove unused imports python
    - remove unused imports typescript
    - consolidate files
    - consolidate python
    - consolidate rust
    - consolidate typescript
    - merge files
    - merge files python
    - merge files rust
    - merge files typescript
    - combine modules
    - combine modules python
    - combine modules typescript
    - code quality audit
    - deep code quality audit
    - maintainability review
    - spaghetti code
    - audit spaghetti growth
    - restructure code
    - code judo
    - split giant file
    - harsh maintainability review before merge
---

# deep-clean

One skill that does three jobs over a branch, diff, or module:

- **Cleanup & consolidation** (mechanical). Phase 1 removes dead code — unused files, stubs, thin wrappers, duplicates, commented-out code, unused imports/exports. Phase 2 merges overlapping files that share the same domain into single cohesive modules.
- **Structural maintainability audit** (judgment). A strict review of abstraction quality, spaghetti-condition growth, giant files, boundary leaks, and missed "code-judo" moves — run over the diff or module *after* cleanup, or standalone when the goal is structure rather than deletion.
- **Simplify sweep** (per-diff). The 4-agent parallel reviewer pass over recent changes: reuse / quality / efficiency / altitude reviewers, aggregate, apply the safe and careful tiers — the merged `simplify-code` scenario, one level deep in `references/`.

**CRITICAL: two-phase order** — dead code first, then consolidation. Consolidating files that still contain dead code wastes effort. The structural audit is the judgment layer on top: it does not replace the mechanical phases; it decides *how* the remaining code should be reshaped.

## Language Routing

Read the matching language reference end to end (self-contained: rules, detection patterns, tool commands, report examples, checklists, quick-reference commands, common mistakes, decision flowchart). The structural audit rules below apply to all three languages.

| Language   | Unit      | Primary detection tooling                        | Export surface you MUST update          | Reference                                |
| ---------- | --------- | ------------------------------------------------ | --------------------------------------- | ---------------------------------------- |
| Python     | package   | `ruff`, `vulture`, `black`, `mypy`/`pyright`, `pytest` | `__init__.py`, `__all__`, `pyproject.toml` | [references/python.md](references/python.md) |
| Rust       | crate     | `cargo clippy`, `cargo-udeps`, `cargo check --all-features` | `mod.rs`, trait definitions, `lib.rs`  | [references/rust.md](references/rust.md)     |
| TypeScript | package   | `knip`, `tsc --noEmit`, `eslint`, `prettier`      | barrel `index.ts`, `package.json` `exports`/`main`/`types` | [references/typescript.md](references/typescript.md) |

## When to Use

- After refactoring modules, or a refactor that split code across files.
- Before committing changes, or before release (final bloat + format pass).
- After merging branches (accumulated dead code).
- When cleaning accumulated commented-out code or onboarding new developers (reduce noise).
- For files with scattered responsibilities, or multiple small files that belong together.
- For a deep code-quality audit of a branch, working tree, or PR.
- For an especially harsh maintainability review before merge.
- To answer "Is this codebase drifting toward spaghetti?" — run over a diff or module.
- "Simplify my changes" / "clean up my recent diff" (the 4-agent sweep) →
  [references/simplify-scenario.md](references/simplify-scenario.md), with its
  sub-references `references/reviewer-prompts.md` and
  `references/phase3-aggregate.md`.

Do **not** use for routine lint/type-check runs (those are the gates in `requesting-code-review`/CI), or for style nits without a structural angle.

## The Fundamental Questions

> **"Why does this function/class/type/file need to exist?"**

- "Because it was always there", "because it might be useful someday", or "because it handles edge cases we don't have" → **REMOVE**.
- "Because it's required by the FRD" or "because it's called by an FRD-required method" → **KEEP**.
- Any other answer → consult that language's full KEEP table (decorators, dynamic imports, feature gates, ambient types, contracts, build scripts, `__all__`/barrel consumers…) in the reference. If unclear → flag for manual review; never auto-remove.

For consolidation: **"Do these files serve the same purpose or share the same domain?"** → if yes, merge into 1 file.

For the structural audit: **"Is there a code-judo move that makes this dramatically simpler?"** → if yes, push for it. Do not stop at local cleanup opportunities.

## Shared Rules

- **Never remove real logic** — only remove code not relevant to FRD scope.
- **Always snapshot before cleanup** — git commit or stash before any deletion.
- **Always run the language's checks after changes** — verify no breakage.
- **File with 0 inbound imports/references AND not an entry point** = likely unused (verify with a multi-pattern check).
- **File with only re-exports** = evaluate whether the re-export adds value.
- **Single Responsibility** (consolidation): each file should have ONE clear purpose.
- **Related classes/functions belong in the same file** (consolidation).
- **Be ambitious about structure** (audit): search for restructurings that delete whole branches, helpers, modes, or conditionals; prefer the version that feels inevitable in hindsight.

Language-specific invariants (Rust: *always update the trait when removing impl methods*, *one struct per file*; Python: *respect `# noqa` / `# type: ignore` / `# pragma: no cover` / `if TYPE_CHECKING:`*; TypeScript: *respect `@ts-ignore` / `eslint-disable` / side-effect imports / path aliases*) and the full **Exceptions — NEVER Remove Without Explicit Approval** tables live in each reference.

## Phase 1 — Dead Code Cleanup (identical steps in all three references)

1. **1.1 Safety Snapshot** — commit, then branch; non-negotiable.
2. **1.2 Read Requirements** — understand MVP scope; list entry points, public API surface, framework registrations, optional-dependency features.
3. **1.3 Primary Detection (tooling)** — run the language's linter/dead-code tools FIRST; they understand language semantics. Capture reports to files; do not auto-fix formatting yet.
4. **1.4 Secondary Detection (file-level scan)** — orphan script: 0 inbound imports across every import style, dynamic loading, test and build references.
5. **1.5 Detect Function-Level Bloat** — stubs, thin wrappers, duplicate definitions, commented-out code, suppressed items, decorator/registered code.
6. **1.6 Analyze and Categorize** — KEEP / REMOVE / INVESTIGATE per the Fundamental Question.
7. **1.7 Report Phase 1** — see the Report Format below.
8. **1.8 Get Approval for Phase 1** — no deletions before approval.
9. **1.9 Execute Phase 1 Cleanup** — auto-fixable safe tool fixes first, then approved manual removals, then update the export surface.
10. **1.10 Verify Phase 1** — the language's verification gates below.

## Phase 2 — File Consolidation

Detect same-purpose / same-domain / split-functionality file groups → pick the target file (the one holding the most logic) → move the source files' unique members into it → update **all** references (imports, exports, tests, wiring) → delete the source file(s) → verify compilation and behavior. Rust merges follow *one struct per file* (merge fields, keep each trait impl, prefix shared method names); Python/TypeScript merge re-export surfaces too (`__init__.py`/`__all__`, barrel `index.ts`/`package.json`).

## Phase 3 — Structural Maintainability Audit (judgment layer)

After cleanup and consolidation are stable, run the strict structural audit over the diff or module. This is where the "code-judo" ambition lives. Read [references/review-tone.md](references/review-tone.md) for tone and output prioritization.

### Non-Negotiable Audit Standards

0. **Be ambitious about structural simplification.** Do not stop at "this could be a bit cleaner." Look for opportunities to reframe the change so whole branches, helpers, modes, conditionals, or layers disappear. If a path deletes complexity rather than rearraging it, push hard for that path.
1. **Do not let a change push a file from under 1k lines to over 1k lines** without a very strong reason. Prefer extracting helpers, subcomponents, or modules; only waive with a compelling structural reason and a still-organized file.
2. **Do not allow random spaghetti growth.** Be highly suspicious of new ad-hoc conditionals, scattered special cases, or one-off branches in unrelated flows. Treat "weird if statements in random places" as a design problem; prefer a dedicated abstraction, helper, state machine, policy object, or separate module.
3. **Bias toward cleaning the design, not just accepting working code.** If behavior stays the same while structure becomes meaningfully cleaner, push for the cleaner version. Prefer simplifications that remove moving pieces altogether over refactors that spread the same complexity around.
4. **Prefer direct, boring, maintainable code over hacky or magical code.** Treat brittle, ad-hoc, or "magic" behavior as a code-quality problem. Flag thin abstractions, identity wrappers, or pass-through helpers that add indirection without clarity.
5. **Push hard on type and boundary cleanliness** where they affect maintainability. Question unnecessary optionality, `unknown`/`any`, or cast-heavy code when a clearer type boundary exists; prefer explicit typed models or shared contracts.
6. **Keep logic in the canonical layer and reuse existing helpers.** Call out feature logic leaking into shared paths or implementation details leaking through APIs; prefer canonical utilities over bespoke one-offs.
7. **Treat unnecessary sequential orchestration and non-atomic updates as design smells** when the cleaner structure is obvious. Flag independent work serialized for no reason, and related updates that leave state half-applied.

### Primary Audit Questions

For every meaningful change, ask:

- Is there a code-judo move that makes this dramatically simpler?
- Can this be reframed so fewer concepts, branches, or helper layers are needed?
- Does this improve or worsen the local architecture?
- Did the diff add branching complexity where a better abstraction should exist?
- Did a previously cohesive module become more coupled, more stateful, or harder to scan?
- Is this logic in the right file and layer?
- Did this change push a file or component past a healthy size boundary?
- Are there repeated conditionals that signal a missing model or missing helper?
- Is the implementation direct and legible, or does it lean on special cases and incidental control flow?
- Is this abstraction earning its keep, or just a wrapper?
- Did the diff introduce casts, optionality, or ad-hoc object shapes that obscure the real invariant?
- Is this logic in the canonical layer, or did the diff leak details across a boundary?
- Is this orchestration more sequential or less atomic than it needs to be?

### What to Flag Aggressively

- A complicated implementation where a cleaner reframing could delete whole categories of complexity.
- Refactors that move code around but fail to reduce the number of concepts a reader must hold.
- A file crossing 1000 lines due to the change, especially if the new code could be split out.
- New conditionals bolted onto unrelated code paths.
- One-off booleans, nullable modes, or flags that complicate existing control flow.
- Feature-specific logic leaking into general-purpose modules.
- Generic "magic" handling that hides simple structure.
- Thin wrappers or identity abstractions that add indirection without simplifying anything.
- Unnecessary casts, `any`, `unknown`, or optional params that muddy the real contract.
- Copy-pasted logic instead of extracted helpers.
- Narrow edge-case handling in the middle of an already busy function.
- Refactors that pass tests but make the code less modular or less readable.
- "Temporary" branching that will become permanent debt.
- Bespoke helpers where the codebase already has a canonical utility.
- Logic added in the wrong layer/package when it has a clear canonical home.
- Sequential async flow where obviously independent work could stay simpler with parallel execution.
- Partial-update logic that leaves state less atomic than necessary.

### Preferred Remedies

- Delete a whole layer of indirection rather than polishing it.
- Reframe the state model so conditionals disappear instead of getting centralized.
- Change the ownership boundary so the feature becomes a natural extension of an existing abstraction.
- Turn special-case logic into a simpler default flow with fewer exceptions.
- Extract a helper or pure function.
- Split a large file into smaller focused modules.
- Move feature-specific logic behind a dedicated abstraction.
- Replace condition chains with a typed model or explicit dispatcher.
- Separate orchestration from business logic.
- Collapse duplicate branches into a single clearer flow.
- Delete wrappers that do not meaningfully clarify the API.
- Reuse the existing canonical helper instead of a near-duplicate.
- Make type boundaries more explicit so control flow gets simpler.
- Move the logic to the package/module/layer that already owns the concept.
- Parallelize independent work when that also simplifies orchestration.
- Restructure related updates into a more atomic flow when partial state would be harder to reason about.

Do not settle for "maybe rename this" when the real issue is structural, or for a merely cleaner version of the same messy idea when a much simpler one is plausible.

### Approval Bar

Do not approve merely because behavior seems correct. The bar is:

- no clear structural regression
- no obvious missed opportunity to make the implementation dramatically simpler when such a path is visible
- no unjustified file-size explosion
- no obvious spaghetti growth from special-case branching
- no obviously hacky or magical abstraction that makes the code harder to reason about
- no unnecessary wrapper/cast/optionality churn obscuring the real design
- no clear architecture-boundary leak or avoidable canonical-helper duplication
- no missed opportunity for an obvious decomposition that would materially improve maintainability

Presumptive blockers (the author must justify clearly):

- the change preserves a lot of incidental complexity when a plausible code-judo move would delete it
- the change pushes a file from below 1000 lines to above 1000 lines
- the change adds ad-hoc branching that tangles an existing flow
- the change solves a local problem by scattering feature checks across shared code
- the change adds an unnecessary abstraction, wrapper, or cast-heavy contract that makes the design more indirect
- the change duplicates an existing helper or puts logic in the wrong layer when there is a clear canonical home

If those conditions are not met, leave explicit, actionable feedback and push for a cleaner decomposition.

## Report Format (all phases)

```text
## Deep-Clean Report: <unit>
### Summary            # files scanned, items analyzed, counts per category found
### Per-File Findings  # per file: | Item | Type | Lines | Verdict | Reason |
### Structural Audit Findings  # from Phase 3: | Finding | File:Line | Severity | Judo move |
### Items Requiring Manual Review   # ambiguous / INVESTIGATE / audit disagreements
### Formatting Fixes (auto-applied) # format-only changes needing no approval
```

Every finding carries a Verdict (KEEP / REMOVE / DELETE / INVESTIGATE / RESTRUCTURE) and a one-line Reason. Each language reference contains a fully worked example table.

## Verification Gates

After any removal, merge, or restructuring, in this order: static/lint check clean → format check clean → type/compile check clean → full test suite passes → the package/crate still imports or resolves at its entry point → downstream consumers still build → no stale references to deleted or renamed names (grep the old names). Exact commands per language are in the references, as are the **Verification Checklist** (Phase 1 / Phase 2 / Final) and **Common Mistakes** tables.

For audit findings: tie every finding to specific files/lines in the diff; for each blocker name the concrete code-judo move that resolves it (or why none exists); a reviewer re-reading the diff cold must be able to reproduce every finding from the code alone.

## Rollback & Commit

Rollback via the snapshot: restore a single file from history, or reset the cleanup branch. Commit only after all gates pass, with a descriptive message itemising counts removed (stubs, thin wrappers, duplicates, unused files, unused imports, commented-out code), files merged, and structural changes applied — per-language commit-message templates are in the references.

## Dry-Run Mode

When the user requests `--dry-run` or says "just show me what you'd remove": run Phase 1 steps 1.1–1.6, Phase 2 overlap detection, and the Phase 3 audit over the current state; generate the full report; **do NOT execute any deletions, edits, format changes, or restructurings**; present the report and wait for explicit approval. This is the **default mode** for first-time runs on a package/crate.
