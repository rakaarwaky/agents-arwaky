---
name: deep-clean
description: "Deep structural cleanup and simplification: remove dead code, merge duplicate files, run a 4-lens diff sweep, and audit maintainability. Use for pre-merge or post-refactor work across Python, Rust, and TypeScript. Also triggered by /simplify."
when-to-use: "Use before merge, before release, or after refactoring a branch, diff, or module. Remove dead code (ruff/vulture/knip/clippy/udeps), consolidate overlapping files into single cohesive modules, run a 4-reviewer diff sweep (reuse, quality, efficiency, altitude), and execute a strict maintainability audit. Answers 'is this codebase drifting toward spaghetti?' — run over a diff or module. Do not use for routine lint/type-check runs (those are CI gates) or for style nits without a structural angle. --dry-run reports without executing and is the default for first-time runs on a package/crate."
argument-hint: "[--dry-run] [--focus <reuse|quality|efficiency|altitude>] [--scope <path|commit>] [diff or module path]"
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
    - code-review
    - refactor
    - delegation
    - subagent
    - parallel
    - simplify
    - spaghetti
    - maintainability
    - code-judo
    - giant-files
    - reuse
    - efficiency
    - altitude
  related_skills:
    - lint-arwaky
    - systematic-debugging
---

# deep-clean

Runs a 7-step pipeline (0–6) over a branch, diff, or module: scope capture → dead-code cleanup → file consolidation → 4-lens diff sweep → aggregate, risk-tier, and structural audit → apply per tier → verification gates. A cleanup and simplification pass over code that already works — not a bug hunt.

## Global rules

- **Mechanical order.** Phase 1 (dead code) always precedes Phase 2 (consolidation) — consolidating files that still contain dead code wastes effort. The 4-lens sweep and structural audit (Phases 3–4) are judgment layers on top; they decide *what to reshape and how to apply it safely*, they do not replace the mechanical phases.
- **Cleanup, not bug hunt.** If a reviewer surfaces a genuine correctness bug, report it prominently in a dedicated "Bugs found" section — never fold it into the SAFE/CAREFUL/RISKY cleanup tiers.
- **Language routing.** Read the matching language reference end to end (self-contained: rules, detection patterns, tool commands, report examples, checklists, quick-reference commands, common mistakes, decision flowchart): Python → [`references/python.md`](references/python.md) (unit: package; export surface: `__init__.py`, `__all__`, `pyproject.toml`); Rust → [`references/rust.md`](references/rust.md) (unit: crate; export surface: `mod.rs`, trait definitions, `lib.rs`); TypeScript → [`references/typescript.md`](references/typescript.md) (unit: package; export surface: barrel `index.ts`, `package.json` `exports`/`main`/`types`). The language reference owns that language's invariants and the full Exceptions — NEVER Remove Without Explicit Approval table.
- **Fundamental questions.** Before keeping any function/class/type/file: "Why does it exist?" — "always there / might be useful / handles edge cases we don't have" → REMOVE; "required by FRD or called by an FRD-required method" → KEEP; anything else → consult the language KEEP table, and when unclear flag for manual review, never auto-remove. Consolidation: "Do these files serve the same purpose or share the same domain?" → merge into 1 file. Structural audit: "Is there a code-judo move that makes this dramatically simpler?" → push for it.
- **Shared rules.** Never remove real logic (only code not relevant to FRD scope); always snapshot (git commit or stash) before any deletion; always run the language's checks after changes. A file with 0 inbound imports/references AND not an entry point is likely unused (verify with a multi-pattern check); a file with only re-exports is evaluated for whether the re-export adds value; consolidation follows single responsibility — one clear purpose per file, related classes/functions in the same file.
- **Evidence standard.** Chesterton's Fence: before flagging anything for removal, run `git blame` on the line to understand why it exists; when the original purpose cannot be determined, mark `confidence: low` — do not guess. Reviewers search, they do not guess: every finding requires `file:line` evidence and a mandatory `cost` field (what is duplicated/wasted/harder to maintain) — a finding that cannot articulate its cost is a nit and gets dropped.
- **Fan-out cap.** The 4-lens sweep uses four reviewers — never fan out wider than 4. When subagents are unavailable (leaf agent, delegation disabled, budget exhausted), work all four angles inline, sequentially, in this context with the same search standards and finding format, and state in the final summary that this was a single-pass inline review, not the parallel fan-out.
- **Risk tiers.** SAFE auto-applied (unused imports, commented-out code, pass-through wrappers, redundant type assertions; run tests after); CAREFUL applied one file at a time with targeted tests after each file, reverting any fix that breaks a test (rename locals, flatten ternaries, extract helpers, consolidate dupes); RISKY flagged for human review, never auto-applied (N+1 restructuring, public API changes, concurrency fixes, error-handling changes; present each with a risk description and test-coverage status). Conflict resolution: `correctness > the user's stated focus > readability/reuse > micro-perf`. Altitude findings usually land in RISKY — present the deeper fix and let the user decide whether to apply now or defer.
- **Snapshot before cleanup.** Git commit or stash before any deletion — Phase 1 step 1.1 is non-negotiable; rollback restores a single file from history or resets the cleanup branch.
- **Dry-run semantics.** `--dry-run` (or "just show me what you'd clean/simplify") runs scope capture, detection, overlap detection, the 4-lens sweep (diff-scoped), and the audit over the current state, generates the full report, applies nothing, and waits for explicit approval. This is the default mode for first-time runs on a package/crate.
- **Report format.** Every phase report carries the section shape in [`references/report-format.md`](references/report-format.md); every finding carries a Verdict (KEEP / REMOVE / DELETE / INVESTIGATE / RESTRUCTURE) and a one-line Reason.
- **Completion.** The language's verification gates in [`references/verification-gates.md`](references/verification-gates.md) all pass, the report is complete with its "Bugs found" section (possibly empty), and the commit (if any) itemises counts removed, files merged, and structural changes applied.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0: scope capture | [`references/step-0-scope.md`](references/step-0-scope.md) | Diff source selection order, large-diff warning, module/crate-scoped requests. |
| Step 1: language routing | [`references/python.md`](references/python.md), [`references/rust.md`](references/rust.md), [`references/typescript.md`](references/typescript.md) | Full per-language Phase 1 (dead code) + Phase 2 (consolidation) procedure. |
| Step 3: 4-lens sweep | [`references/lens-sweep.md`](references/lens-sweep.md) | Execution model, the four lenses, evidence standard, finding format, sweep pitfalls. |
| Step 4: reviewer prompts | [`references/reviewer-prompts.md`](references/reviewer-prompts.md) | Full prompt text for each of the four reviewer lenses. |
| Step 4: audit standards | [`references/audit-standards.md`](references/audit-standards.md) | Non-negotiable audit standards, primary audit questions, what to flag aggressively, preferred remedies, approval bar; tone and output prioritization live in [`references/review-tone.md`](references/review-tone.md). |
| Step 5: apply per tier | [`references/apply-per-tier.md`](references/apply-per-tier.md) | Strict tier order, per-file test gates, dry-run presentation, house-style folding. |
| Step 6: verification gates | [`references/verification-gates.md`](references/verification-gates.md) | Gate order, per-language exact commands, verification checklist, common mistakes, bugs-found section rules. |
| Report format | [`references/report-format.md`](references/report-format.md) | Deep-Clean Report section shape and worked example. |
