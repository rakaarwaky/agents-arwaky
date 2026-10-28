# Phase 3 — Aggregate and apply (detail)

Wait for all four to return (batch mode returns them together).

1. **Merge** the findings into one list, deduping where reviewers overlap — when two findings target the same line or the same underlying mechanism, collapse them into one.
2. **Discard false positives** — you have the most context; you don't have to argue with a reviewer, just drop weak or wrong suggestions silently.
3. **Resolve conflicts.** Reviewers can disagree (Reviewer 1: "use existing util X"; Reviewer 3: "X is slow, inline it"). Default resolution order: **correctness > the user's stated focus > readability/reuse > micro-perf.** Don't apply a perf "fix" that hurts clarity unless the path is genuinely hot. When two suggestions are mutually exclusive and both defensible, pick the one that touches less code and note the alternative.
4. **Apply in risk-tier order:**
   - **SAFE first** (auto-apply): unused imports, commented-out code, pass-through wrappers, redundant type assertions. Run tests after.
   - **CAREFUL next** (apply with verification, one file at a time): rename locals, flatten ternaries, extract helpers, consolidate dupes. Run tests after each file. Revert any that break.
   - **RISKY last** (flag for review — do NOT auto-apply): N+1 restructuring, public API changes, concurrency fixes, error-handling changes. Present each with risk description and test coverage status. Altitude findings usually land here — deepening a fix means touching shared infrastructure, so present the deeper fix and let the user decide whether to do it now or as a follow-up.
   If the user opted for a dry run, present all three tiers and apply nothing.
5. **Verify** you didn't break anything: run the project's targeted tests for the touched files (not the full suite), and re-run any linter/type check the repo uses. If a fix breaks a test, revert that one fix and report it.
6. **Summarize** what you changed: a short list of applied fixes grouped by reviewer category and risk tier, plus any findings you deliberately skipped and why. If you ran inline (no delegation), say so here.
