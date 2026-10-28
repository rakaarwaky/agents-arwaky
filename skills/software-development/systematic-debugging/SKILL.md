---
name: systematic-debugging
description: Debugs root causes in 4 phases. Use when fixing bugs via read_file, search, delegate_task.
when-to-use: Use for any technical issue — test failures, production bugs, build/performance problems. Users also invoke it directly as /systematic-debugging; this slash trigger is carried here so trigger matching resolves bundled-vs-user collisions.
argument-hint: "<issue-or-error> [--phase <1|2|3|4>] [--repro <command>]"
metadata:
  tags:
    - debugging
    - troubleshooting
    - problem-solving
    - root-cause
    - investigation
  related_skills:
    - test-driven-development
    - hermes-plan
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```text
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST

```text

If you haven't completed Phase 1, you cannot propose fixes.

## The Feedback Loop Rule

The feedback loop is the debugging work. Before reading code to build a theory, create or identify a **tight** command that can go red on the user's exact symptom and green when the bug is fixed. A tight loop is fast, deterministic, agent-runnable, and specific enough to catch this bug — not merely "doesn't crash".

When a clean repro is hard, spend disproportionate effort building the loop. Guessing without a red-capable loop is the failure mode this skill exists to prevent.

## When to Use

Use for ANY technical issue:

- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**

- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**

- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

See [`references/phase1-root-cause.md`](references/phase1-root-cause.md).
## Phase 2: Pattern Analysis

See [`references/phase2-pattern.md`](references/phase2-pattern.md).
## Phase 3: Hypothesis and Testing

See [`references/phase3-hypothesis.md`](references/phase3-hypothesis.md).
## Phase 4: Implementation

See [`references/phase4-implementation.md`](references/phase4-implementation.md).
## Red Flags — STOP and Follow Process

See [`references/red-flags.md`](references/red-flags.md).
## Common Rationalizations

See [`references/common-rationalizations.md`](references/common-rationalizations.md).
## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

See [`references/hermes-integration.md`](references/hermes-integration.md).
## Real-World Impact

From debugging sessions:

- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
