# Step 4: Implementation via TDD (Phase 4)

**Fix the root cause, not the symptom. TDD is the verification engine — every fix is born from a failing test.**

The two Iron Laws collapse into one gate here: you may not write the fix until (a) root cause is identified (Steps 1–3) AND (b) a test reproducing the bug exists and is RED.

## 1. RED — Write the Failing Test (reproduction)

- Simplest possible reproduction; automated test if possible.
- The test MUST fail before any fix; watch it fail for the expected reason (feature missing, not a typo). Cycle detail, good/bad test examples, and the "watch it fail" gate: [`step-6-guardrails.md`](step-6-guardrails.md) §TDD Cycle Detail → RED.
- This test encodes the user's exact symptom — it is the regression test.
- Use vertical tracer bullets: one behavior slice at a time (test1→impl1), not all tests then all impl. Rationale: [`step-6-guardrails.md`](step-6-guardrails.md) §TDD Rationale.

## 2. GREEN — Implement Single Fix

- Address the root cause identified in Steps 1–3.
- ONE change at a time. No "while I'm here" improvements. No bundled refactoring.
- Write the simplest code to make the test pass (hardcoding, copy-paste OK now).
- Detail: [`step-6-guardrails.md`](step-6-guardrails.md) §TDD Cycle Detail → GREEN.

## 3. Verify Fix

Run the specific regression test and the full suite with the runner that matches `target_lang` from Step 0:

- **Python**: `pytest tests/test_module.py::test_regression -v` then `pytest tests/ -q`
- **TypeScript/Node**: `vitest run src/app/foo.test.tsx` (or the project's test runner) then full suite
- **Rust**: `cargo test test_name -- --nocapture` then `cargo test`

Confirm: test passes, other tests still pass, output pristine (no warnings).

## 4. REFACTOR — Clean Up (optional, only while green)

- Remove duplication, improve names, extract helpers. Keep tests green.
- Detail: [`step-6-guardrails.md`](step-6-guardrails.md) §TDD Cycle Detail → REFACTOR.

## 5. If Fix Doesn't Work — The Rule of Three

- STOP. Increment `fix_attempts` from Step 0 state.
- If < 3: return to Step 1, re-analyze with new information.
- If ≥ 3: STOP and question the architecture (§6).
- DON'T attempt Fix #4 without architectural discussion.

## 6. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**

- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**

- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

## With Subagents

For complex multi-component debugging, the TDD phase may still be done inline; dispatch subagents only for isolated investigation (Step 1), never for un-supervised "fix it" attempts that bypass the RED gate.
