# Phase4 Implementation

## Phase 4: Implementation

**Fix the root cause, not the symptom. TDD is the verification engine —
every fix is born from a failing test.**

The two Iron Laws collapse into one gate here: you may not write the fix
until (a) root cause is identified (Phase 1–3) AND (b) a test reproducing
the bug exists and is RED.

### 1. RED — Write the Failing Test (reproduction)

- Simplest possible reproduction; automated test if possible.
- The test MUST fail before any fix; watch it fail for the expected reason
  (feature missing, not a typo). See `references/tdd-red-green-refactor.md` §RED.
- This test encodes the user's exact symptom — it is the regression test.
- Use vertical tracer bullets: one behavior slice at a time (test1→impl1),
  not all tests then all impl. See `references/tdd-why-order-matters.md`.

### 2. GREEN — Implement Single Fix

- Address the root cause identified in Phases 1–3.
- ONE change at a time. No "while I'm here" improvements. No bundled refactoring.
- Write the simplest code to make the test pass (hardcoding, copy-paste OK now).
- See `references/tdd-red-green-refactor.md` §GREEN.

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v   # or cargo test / vitest

# Run full suite — no regressions
pytest tests/ -q
```

Confirm: test passes, other tests still pass, output pristine (no warnings).

### 4. REFACTOR — Clean Up (optional, only while green)

- Remove duplication, improve names, extract helpers. Keep tests green.
- See `references/tdd-red-green-refactor.md` §REFACTOR.

### 5. If Fix Doesn't Work — The Rule of Three

- STOP. Count fixes tried.
- If < 3: return to Phase 1, re-analyze with new information.
- If ≥ 3: STOP and question the architecture (step 6).
- DON'T attempt Fix #4 without architectural discussion.

### 6. If 3+ Fixes Failed: Question Architecture

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

---
