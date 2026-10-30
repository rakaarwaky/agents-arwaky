---
name: systematic-debugging
description: Systematic root-cause debugging in 4 phases covering TypeScript/Node, Python, and Rust. Use when fixing bugs, test failures, build or performance problems, or unexpected behavior — read errors, build a tight feedback loop, trace data flow, form hypotheses, then implement one fix verified by TDD (RED-GREEN-REFACTOR). Includes language debuggers (pdb/debugpy, node inspect/CDP, rust-gdb/lldb/dbg!).
when-to-use: Use for any technical issue — test failures, production bugs, build or performance problems, integration issues. Also for Python (pdb, debugpy), TypeScript/Node (node inspect, CDP, heap/CPU profiles), and Rust (dbg!, RUST_BACKTRACE, rust-gdb/lldb) debugging. Invoke directly as /systematic-debugging.
argument-hint: "<issue-or-error> [--phase <1|2|3|4>] [--lang <python|typescript|rust|node>] [--repro <command>]"
metadata:
  tags:
    - debugging
    - troubleshooting
    - problem-solving
    - root-cause
    - investigation
    - tdd
    - python
    - typescript
    - node
    - rust
    - pdb
    - debugpy
    - cdp
  related_skills:
    - github-pr-workflow
    - work-on-issue
    - simplify-code
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure. One fix, proven by a failing test, is the only fix that ships.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law (Unified)

Two phrasings, one gate:

```text
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

The failing test from the second law is the tight feedback loop demanded by
the first: Phase 1 builds a red-capable loop, Phase 4 turns it green with
the smallest possible change. You may not propose or write a fix until
both conditions hold. Violating the letter of either law is violating the
spirit of debugging.

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

- **Phase 1: Root Cause Investigation** → [`references/phase1-root-cause.md`](references/phase1-root-cause.md)
- **Phase 2: Pattern Analysis** → [`references/phase2-pattern.md`](references/phase2-pattern.md)
- **Phase 3: Hypothesis and Testing** → [`references/phase3-hypothesis.md`](references/phase3-hypothesis.md)
- **Phase 4: Implementation** (TDD-woven: RED → GREEN → verify → REFACTOR) → [`references/phase4-implementation.md`](references/phase4-implementation.md)

## Red Flags — STOP and Follow Process

See [`references/red-flags.md`](references/red-flags.md).

## Common Rationalizations

One merged table for debugging and TDD excuses: [`references/common-rationalizations.md`](references/common-rationalizations.md).

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | RED failing test, TDD cycle: fix root cause, verify, refactor | Bug resolved, regression test green, all tests pass |

## Language-Specific Debugging

Pick by file extension / runtime; each reference is self-contained.

- **Python** → [`references/python-debugging.md`](references/python-debugging.md)
- **TypeScript/Node** → [`references/node-typescript-debugging.md`](references/node-typescript-debugging.md)
- **Rust** → [`references/rust-debugging.md`](references/rust-debugging.md)

These three references arrive in PR 2 of this migration; they do not exist yet.

## Agent Integration

See [`references/agent-integration.md`](references/agent-integration.md).

## Related Skills

- `github-pr-workflow` — PR lifecycle; loads this skill for bug-class fixes
- `work-on-issue` — issue triage; loads this skill for bug-class fixes
- `simplify-code` — post-fix cleanup pass

## Real-World Impact

From debugging sessions:

- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**