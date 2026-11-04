---
name: deep-clean
description: "Deep structural cleanup and simplification: remove dead code, merge duplicate files, run a 4-lens sweep, and audit maintainability over a named path. Use for pre-merge or post-refactor work across Python, Rust, and TypeScript. Also triggered by /simplify."
when-to-use: "Use before merge, before release, or after refactoring a path, package, crate, or file. Remove dead code (ruff/vulture/knip/clippy/udeps), consolidate overlapping files into single cohesive modules, run a 4-reviewer sweep (reuse, quality, efficiency, altitude), and execute a strict maintainability audit. Answers 'is this codebase drifting toward spaghetti?' — run over a path, step by step, all aspects. Do not use for routine lint/type-check runs (those are CI gates) or for style nits without a structural angle. `--dry-run` (explicit) reports without executing; without it the run is headless and autonomous — no permission prompts."
argument-hint: "<path> [--dry-run]"
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

Runs a 7-step pipeline (0–7) over a named path: path audit capture → per-language dead-code cleanup (step 1) → per-language file consolidation (step 2) → 4-lens sweep (step 3) → reviewer prompts + structural audit (step 4) → apply per tier (step 5) → verification gates (step 6) → report (step 7). Language variants are picked per step (`1a`/`1b`/`1c`, `2a`/`2b`/`2c`) by the target language. A cleanup and simplification pass over code that already works — not a bug hunt.

## Global rules

- **Path-only audit.** The run takes a path (file, directory, package, or crate) and audits all of it step by step, all aspects in order. It never reads git diff, commits, or branches, and never bases findings on git history.
- **Headless autonomous by default.** Without `--dry-run`, every step executes to completion without asking the user for permission. RISKY-tier and low-confidence items are recorded in the report's manual-review section instead of blocking the run.
- **`--dry-run` is explicit-only.** Only when the user explicitly passes it: run the full audit (steps 0–6) in report-only mode, apply nothing, and skip the commit.
- **Mechanical order.** Phase 1 (dead code, step 1) always precedes Phase 2 (consolidation, step 2) — consolidating files that still contain dead code wastes effort. The 4-lens sweep and structural audit (steps 3–4) are judgment layers on top; they decide *what to reshape and how to apply it safely*, they do not replace the mechanical phases.
- **Cleanup, not bug hunt.** If a reviewer surfaces a genuine correctness bug, report it prominently in a dedicated "Bugs found" section — never fold it into the SAFE/CAREFUL/RISKY cleanup tiers.
- **Language routing.** Per step, pick the language variant from the target language: step 1 → [`step-1a-dead-code-python.md`](references/step-1a-dead-code-python.md) / [`step-1b-dead-code-rust.md`](references/step-1b-dead-code-rust.md) / [`step-1c-dead-code-typescript.md`](references/step-1c-dead-code-typescript.md); step 2 → [`step-2a-consolidate-python.md`](references/step-2a-consolidate-python.md) / [`step-2b-consolidate-rust.md`](references/step-2b-consolidate-rust.md) / [`step-2c-consolidate-typescript.md`](references/step-2c-consolidate-typescript.md). Each variant is self-contained (rules, detection patterns, tool commands, report examples, checklists, quick-reference commands, common mistakes, decision flowchart). Export surfaces: Python `__init__.py` / `__all__` / `pyproject.toml`; Rust `mod.rs` / trait definitions / `lib.rs`; TypeScript barrel `index.ts` / `package.json` `exports`/`main`/`types`. Each variant owns its language's invariants and the full Exceptions — NEVER Remove Without Explicit Approval table.
- **Fundamental questions.** Before keeping any function/class/type/file: "Why does it exist?" — "always there / might be useful / handles edge cases we don't have" → REMOVE; "required by FRD or called by an FRD-required method" → KEEP; anything else → consult the language KEEP table, and when unclear flag for manual review, never auto-remove. Consolidation: "Do these files serve the same purpose or share the same domain?" → merge into 1 file. Structural audit: "Is there a code-judo move that makes this dramatically simpler?" → push for it.
- **Shared rules.** Never remove real logic (only code not relevant to FRD scope); always snapshot (git commit or stash) before any deletion; always run the language's checks after changes. A file with 0 inbound imports/references AND not an entry point is likely unused (verify with a multi-pattern check); a file with only re-exports is evaluated for whether the re-export adds value; consolidation follows single responsibility — one clear purpose per file, related classes/functions in the same file.
- **Evidence standard.** Chesterton's Fence: before flagging anything for removal, run `git blame` on the line to understand why it exists; when the original purpose cannot be determined, mark `confidence: low` — do not guess. Reviewers search, they do not guess: every finding requires `file:line` evidence and a mandatory `cost` field (what is duplicated/wasted/harder to maintain) — a finding that cannot articulate its cost is a nit and gets dropped.
- **Fan-out cap.** The 4-lens sweep uses four reviewers — never fan out wider than 4. When subagents are unavailable (leaf agent, delegation disabled, budget exhausted), work all four angles inline, sequentially, in this context with the same search standards and finding format, and state in the final summary that this was a single-pass inline review, not the parallel fan-out.
- **Risk tiers.** SAFE auto-applied (unused imports, commented-out code, pass-through wrappers, redundant type assertions; run tests after); CAREFUL applied one file at a time with targeted tests after each file, reverting any fix that breaks a test (rename locals, flatten ternaries, extract helpers, consolidate dupes); RISKY flagged in the report's manual-review section, never auto-applied (N+1 restructuring, public API changes, concurrency fixes, error-handling changes; present each with a risk description and test-coverage status). Conflict resolution: `correctness > the user's stated focus > readability/reuse > micro-perf`. Altitude findings usually land in RISKY — present the deeper fix in the report; in headless mode it is recorded, not applied.
- **Snapshot before cleanup.** Git commit or stash before any deletion — step 1 step 1.1 is non-negotiable; rollback restores a single file from history or resets the cleanup branch.
- **Report format.** The final report follows [`references/step-7-report-format.md`](references/step-7-report-format.md); every finding carries a Verdict (KEEP / REMOVE / DELETE / INVESTIGATE / RESTRUCTURE) and a one-line Reason.
- **Completion.** The language's verification gates in [`references/step-6-verification-gates.md`](references/step-6-verification-gates.md) all pass, the step 7 report is complete with its "Bugs found" section (possibly empty), and the commit (if any) itemises counts removed, files merged, and structural changes applied.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0: path audit capture | [`references/step-0-scope.md`](references/step-0-scope.md) | Path validation, audit scope, headless vs `--dry-run` mode gate. |
| Step 1: dead code (language variants) | [`step-1a-dead-code-python.md`](references/step-1a-dead-code-python.md), [`step-1b-dead-code-rust.md`](references/step-1b-dead-code-rust.md), [`step-1c-dead-code-typescript.md`](references/step-1c-dead-code-typescript.md) | Phase 1 per-language dead-code detection, workflow, exceptions. |
| Step 2: consolidation (language variants) | [`step-2a-consolidate-python.md`](references/step-2a-consolidate-python.md), [`step-2b-consolidate-rust.md`](references/step-2b-consolidate-rust.md), [`step-2c-consolidate-typescript.md`](references/step-2c-consolidate-typescript.md) | Phase 2 per-language consolidation workflow, verification, commit, checklists. |
| Step 3: 4-lens sweep | [`references/step-3-lens-sweep.md`](references/step-3-lens-sweep.md) | Execution model, the four lenses, evidence standard, finding format, sweep pitfalls. |
| Step 4: reviewer prompts | [`references/step-4-reviewer-prompts.md`](references/step-4-reviewer-prompts.md) | Full prompt text for each of the four reviewer lenses. |
| Step 4: audit standards | [`references/step-4-audit-standards.md`](references/step-4-audit-standards.md) | Non-negotiable audit standards, primary audit questions, what to flag aggressively, preferred remedies, approval bar; tone and output prioritization live in [`references/step-4-review-tone.md`](references/step-4-review-tone.md). |
| Step 5: apply per tier | [`references/step-5-apply-per-tier.md`](references/step-5-apply-per-tier.md) | Strict tier order, per-file test gates, dry-run presentation, house-style folding. |
| Step 6: verification gates | [`references/step-6-verification-gates.md`](references/step-6-verification-gates.md) | Gate order, per-language exact commands, verification checklist, common mistakes, bugs-found section rules. |
| Step 7: report | [`references/step-7-report-format.md`](references/step-7-report-format.md) | Final report section shape and worked example. |
