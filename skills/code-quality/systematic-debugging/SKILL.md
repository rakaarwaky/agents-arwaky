---
name: systematic-debugging
description: "Systematic root-cause debugging in 7 step files (0–6) covering TypeScript/Node, Python, and Rust: read errors and build a red-capable feedback loop, trace data flow, analyze patterns, form ranked falsifiable hypotheses, implement one fix via TDD (RED-GREEN-REFACTOR), verify, and guard against rationalizations. Includes language-variant debugger/verify steps (3a/3b/3c, 5a/5b/5c). Observed phrasing: /systematic-debugging, fix this bug, test is failing, performance regression."
when-to-use: "Use for any technical issue — test failures, production bugs, build or performance problems, integration issues. Also for Python (pdb, debugpy), TypeScript/Node (node inspect, CDP, heap/CPU profiles), and Rust (dbg!, RUST_BACKTRACE, rust-gdb/lldb) debugging. Invoke directly as /systematic-debugging."
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
    - deep-clean
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure. One fix, proven by a failing test, is the only fix that ships.

## The Iron Law (Unified)

Two phrasings, one gate:

```text
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

The failing test from the second law is the tight feedback loop demanded by the first: Step 1 builds a red-capable loop, Step 4 turns it green with the smallest possible change. You may not propose or write a fix until both conditions hold. Violating the letter of either law is violating the spirit of debugging.

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

## The Steps

Every step is self-contained: `references/step-<N>-<name>.md` holds the rules, checklists, and tool commands for that step. Language-variant steps (`step-<N>a|b|c`) are picked by `target_lang` from Step 0 and own the language-specific debugger or cleanup checklist for that step.

| Step | Reference | Purpose |
|------|-----------|---------|
| 0 | [`references/step-0-intake.md`](references/step-0-intake.md) | Intake, iron-law gate, run state, invocation |
| 1 | [`references/step-1-investigate.md`](references/step-1-investigate.md) | Read errors, build a tight red-capable loop, check recent changes, gather multi-component evidence, trace data flow |
| 2 | [`references/step-2-pattern.md`](references/step-2-pattern.md) | Minimize the repro, find working examples, compare against references, identify differences, understand dependencies |
| 3 | [`references/step-3-hypothesis.md`](references/step-3-hypothesis.md) | Form 3–5 ranked falsifiable hypotheses, test minimally one variable at a time, pick the language debugger variant |
| 3a | [`references/step-3a-python-debugger.md`](references/step-3a-python-debugger.md) | Python debugger: pdb + debugpy, REPL quick reference, long-running-process patterns, pitfalls, recipes |
| 3b | [`references/step-3b-node-debugger.md`](references/step-3b-node-debugger.md) | Node/TS debugger: node inspect + CDP, attach-to-running-process, TUI/Ink, vitest-under-debugger, heap/CPU profiles |
| 3c | [`references/step-3c-rust-debugger.md`](references/step-3c-rust-debugger.md) | Rust debugger: dbg!, RUST_BACKTRACE, log crate, rust-gdb/lldb, one-shot recipes |
| 4 | [`references/step-4-implement.md`](references/step-4-implement.md) | TDD cycle: RED failing test, GREEN single fix, verify (per-language runner), REFACTOR; rule of three; question architecture at 3+ failures |
| 5 | [`references/step-5-verify.md`](references/step-5-verify.md) | Verification checklist, language cleanup pass (delegates to 5a/5b/5c), guardrails final pass, reporting format |
| 5a | [`references/step-5a-python-verify.md`](references/step-5a-python-verify.md) | Python verification + cleanup grep |
| 5b | [`references/step-5b-node-verify.md`](references/step-5b-node-verify.md) | Node/TS verification + cleanup grep |
| 5c | [`references/step-5c-rust-verify.md`](references/step-5c-rust-verify.md) | Rust verification + cleanup grep |
| 6 | [`references/step-6-guardrails.md`](references/step-6-guardrails.md) | Merged guardrails: red-flags list, common-rationalizations table, TDD rationale, TDD cycle detail (RED/GREEN/REFACTOR mechanics) |

Language-variant selection happens inside Step 3 (debugger) and Step 5 (cleanup), by `target_lang` from Step 0. Each variant is self-contained: tool selection, quick reference, pitfalls, and one-shot recipes.

## Quick Reference

| Step | Key Activities | Success Criteria |
|------|----------------|------------------|
| **0. Intake** | Symptom statement, target lang, repro command, run state | Red-capable loop is in scope; no guessing |
| **1. Investigate** | Read errors, build tight loop, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Minimize repro, find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form ranked falsifiable hypotheses, test minimally one variable at a time, pick language debugger (3a/3b/3c) | Confirmed or new hypothesis |
| **4. Implement** | RED failing test, GREEN single fix, verify, REFACTOR | Bug resolved, regression test green, all tests pass |
| **5. Verify & Finish** | Verification checklist, language cleanup pass (5a/5b/5c), guardrails pass, report | Proof-backed report; no residual unverified claims |
| **6. Guardrails** | Red flags, rationalization table, TDD rationale, TDD cycle detail | Applied as cross-cutting rules; final pass before reporting done |

## Red Flags — STOP and Follow Process

See [`references/step-6-guardrails.md`](references/step-6-guardrails.md) §Red Flags.

## Common Rationalizations

One merged table for debugging and TDD excuses: [`references/step-6-guardrails.md`](references/step-6-guardrails.md) §Common Rationalizations.

## Related Skills

- `github-pr-workflow` — PR lifecycle; loads this skill for bug-class fixes
- `work-on-issue` — issue triage; loads this skill for bug-class fixes
- `deep-clean` — post-fix cleanup pass

## Real-World Impact

From debugging sessions:

- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
