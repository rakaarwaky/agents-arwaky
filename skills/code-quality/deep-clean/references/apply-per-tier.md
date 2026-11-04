# Apply Per Tier

## Aggregate findings

Before applying, aggregate the 4-lens sweep (and Phase 1/Phase 2) findings into one list:

1. **Merge** the findings into one list, deduping where reviewers overlap — when two findings
   target the same line or the same underlying mechanism, collapse them into one.
2. **Discard false positives** — you have the most context; you don't have to argue with a
   reviewer, just drop weak or wrong suggestions silently.
3. **Resolve conflicts.** Reviewers can disagree (Reviewer 1: "use existing util X";
   Reviewer 3: "X is slow, inline it"). Default resolution order: **correctness > the
   user's stated focus > readability/reuse > micro-perf.** Don't apply a perf "fix" that
   hurts clarity unless the path is genuinely hot. When two suggestions are mutually
   exclusive and both defensible, pick the one that touches less code and note the
   alternative.

## Apply in strict risk-tier order

1. **SAFE first** — auto-apply (unused imports, commented-out code, pass-through wrappers,
   redundant type assertions); run tests after.
2. **CAREFUL next** — apply one file at a time (rename locals, flatten ternaries, extract
   helpers, consolidate dupes); run targeted tests after each file; revert any individual
   fix that breaks a test.
3. **RISKY last** — flag for human review; **do NOT auto-apply** (N+1 restructuring, public
   API changes, concurrency fixes, error-handling changes). Present each with a risk
   description and current test-coverage status. Altitude findings usually land here:
   deepening a fix means touching shared infrastructure, so present the deeper fix and let
   the user decide whether to apply now or defer.
4. If the user opted for `--dry-run`, present all three tiers and apply nothing.

Respect project conventions: if the repo has `AGENTS.md` / `CLAUDE.md` or a linter config,
fold those rules into the apply step so fixes match house style.

## Verify and summarize

- **Verify** you didn't break anything: run the project's targeted tests for the touched
  files (not the full suite), and re-run any linter/type check the repo uses. If a fix
  breaks a test, revert that one fix and report it.
- **Summarize** what you changed: a short list of applied fixes grouped by reviewer
  category and risk tier, plus any findings you deliberately skipped and why. If you ran
  inline (no delegation), say so here.

## Completion

- All SAFE/CAREFUL fixes applied and verified per-file; RISKY items presented (or all tiers presented, nothing applied, under `--dry-run`).
