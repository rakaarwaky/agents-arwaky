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

**All work is delegated to Grok Build.** The pipeline above is the Grok lane — Grok runs it inside one dedicated Orca worktree. Hermes's lane is four steps: plan the brief, drop `/deep-clean <path>` into Grok, wait, verify + ship. Hermes never writes code, runs the sweep, or applies tiers itself.

## Global rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build via Orca worktree)**: You never write code, run the 4-lens sweep, or apply cleanup tiers yourself. One Orca worktree with `--agent grok`; Grok Build runs the entire pipeline inside it. No `spawn_subagent` for reviewers — your only "subagent" is the Grok Build TUI.
- **One-shot task drop**: You send exactly one message to Grok: `/deep-clean <path>` plus the brief's language, mode (headless vs `--dry-run`), and acceptance criteria. No mid-run course corrections, no status pings.
- **Single point of control**: You own all surviving git, Orca worktree, and PR operations. Grok works inside `cwd: <worktree_path>` and makes one local commit; it never pushes or opens a PR (you verify and ship in Step 2).
- **Language routing**: detect the target language from `<path>` (Python / Rust / TypeScript) and state it in the brief — Grok picks the matching `1x`/`2x` variant. You do not pick it yourself.
- **`--dry-run` passthrough**: if the user passed `--dry-run`, forward it verbatim in the task drop. In dry-run there is no commit — verify that in Step 2.
- **Headless autonomous**: without `--dry-run`, every step executes to completion without asking the user for permission. RISKY-tier and low-confidence items are recorded in the report's manual-review section, not blocking.
- **Cleanup, not bug hunt.** If Grok's report surfaces a genuine correctness bug in its "Bugs found" section, surface it prominently to the user — never fold it into the cleanup tiers.
- **Verification re-run.** Grok's "gates passed" claim is self-reported. Step 2 re-runs the language's verification gates against the clean committed tree in Hermes's own tools before trusting it.
- **Parallel-First for Hermes's own work**: when you need to read multiple report sections or run multiple read-only checks, batch them in one tool call. Serialize only true dependencies.
- **Exit condition for Hermes**: Grok's report is complete with its "Bugs found" section, your Step 2 verification (gates green on the clean committed tree, commit hygiene) passes. Then you ship (if asked) and report.

## Routing

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree, having just received `/deep-clean <path>`. Run the 7-step pipeline in `references/grok/` (steps 0–7, with per-language `1x`/`2x` variants).

### Hermes lane (Steps 0–3)

| Step | Reference                                                                     | Purpose                                                                                                  |
| ----: | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Detect language from `<path>`; plan the brief (mode, acceptance criteria); create the Orca worktree with `--agent grok`; drop `/deep-clean <path>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md) | Wait for Grok to finish the pipeline; read its step 7 report and commit                                |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Re-run the language's verification gates on the clean committed tree; surface bugs + RISKY items; push/PR if asked |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (cleanup counts, bugs, RISKY items, commit/PR, worktree teardown)             |

### Grok lane (Steps 0–7, run by Grok Build)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0: path audit capture | [`references/grok/step-0-scope.md`](references/grok/step-0-scope.md) | Path validation, audit scope, headless vs `--dry-run` mode gate. |
| Step 1: dead code (language variants) | [`step-1a-dead-code-python.md`](references/grok/step-1a-dead-code-python.md), [`step-1b-dead-code-rust.md`](references/grok/step-1b-dead-code-rust.md), [`step-1c-dead-code-typescript.md`](references/grok/step-1c-dead-code-typescript.md) | Phase 1 per-language dead-code detection, workflow, exceptions. |
| Step 2: consolidation (language variants) | [`step-2a-consolidate-python.md`](references/grok/step-2a-consolidate-python.md), [`step-2b-consolidate-rust.md`](references/grok/step-2b-consolidate-rust.md), [`step-2c-consolidate-typescript.md`](references/grok/step-2c-consolidate-typescript.md) | Phase 2 per-language consolidation workflow, verification, commit, checklists. |
| Step 3: 4-lens sweep | [`references/grok/step-3-lens-sweep.md`](references/grok/step-3-lens-sweep.md) | Execution model, the four lenses, evidence standard, finding format, sweep pitfalls. |
| Step 4: reviewer prompts | [`references/grok/step-4-reviewer-prompts.md`](references/grok/step-4-reviewer-prompts.md) | Full prompt text for each of the four reviewer lenses. |
| Step 4: audit standards | [`references/grok/step-4-audit-standards.md`](references/grok/step-4-audit-standards.md) | Non-negotiable audit standards, primary audit questions, what to flag aggressively, preferred remedies, approval bar; tone and output prioritization live in [`references/grok/step-4-review-tone.md`](references/grok/step-4-review-tone.md). |
| Step 5: apply per tier | [`references/grok/step-5-apply-per-tier.md`](references/grok/step-5-apply-per-tier.md) | Strict tier order, per-file test gates, dry-run presentation, house-style folding. |
| Step 6: verification gates | [`references/grok/step-6-verification-gates.md`](references/grok/step-6-verification-gates.md) | Gate order, per-language exact commands, verification checklist, common mistakes, bugs-found section rules. |
| Step 7: report | [`references/grok/step-7-report-format.md`](references/grok/step-7-report-format.md) | Final report section shape and worked example. |
