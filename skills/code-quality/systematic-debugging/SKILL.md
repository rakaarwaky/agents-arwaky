---
name: systematic-debugging
description: "Systematic root-cause debugging in 7 step files (0–6) covering TypeScript/Node, Python, and Rust: read errors and build a red-capable feedback loop, trace data flow, analyze patterns, form ranked falsifiable hypotheses, implement one fix via TDD (RED-GREEN-REFACTOR), verify, and guard against rationalizations. Includes language-variant debugger/verify steps (3a/3b/3c, 5a/5b/5c). Observed phrasing: /systematic-debugging, fix this bug, test is failing, performance regression."
when-to-use: "Use for any technical issue — test failures, production bugs, build or performance problems, integration issues. Also for Python (pdb, debugpy), TypeScript/Node (node inspect, CDP, heap/CPU profiles), and Rust (dbg!, RUST_BACKTRACE, rust-gdb/lldb) debugging. Invoke directly as /systematic-debugging. Do not skip when the issue seems simple, you are in a hurry, or someone wants it fixed NOW — rushing guarantees rework."
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
    - pr-babysit
    - issue-worker
    - deep-clean
---

# Systematic Debugging

For any technical issue — test failures, production bugs, build or performance problems — find the root cause before touching a fix, using a tight red-capable feedback loop and a single TDD-proven fix.

## Global rules

- **The iron law.** Two phrasings, one gate: no fixes without root-cause investigation first; no production code without a failing test first. You may not propose or write a fix until both hold — the failing test from the second law is the tight feedback loop demanded by the first.
- **The feedback loop rule.** Before reading code to build a theory, create or identify a tight command that goes red on the user's exact symptom and green when the bug is fixed: fast, deterministic, agent-runnable, specific enough to catch this bug — not merely "doesn't crash". When a clean repro is hard, spend disproportionate effort building the loop; guessing without a red-capable loop is the failure mode this skill exists to prevent.
- **When to use.** Use for ANY technical issue, ESPECIALLY under time pressure, when "just one quick fix" seems obvious, after multiple failed attempts, or when you do not fully understand the issue. Use for Python, TypeScript/Node, and Rust debugging alike; language-variant steps are picked by `target_lang` from step 0.
- **Language variants.** Debugger variant (`step-3a`/`3b`/`3c`) is picked inside step 3; cleanup variant (`step-5a`/`5b`/`5c`) inside step 5, each by `target_lang` from step 0. Each variant is self-contained: tool selection, quick reference, pitfalls, one-shot recipes.
- **Guardrails.** Red flags force a STOP and return to process — see [`references/step-6-guardrails.md`](references/step-6-guardrails.md) §Red Flags. The common rationalization table (debugging and TDD excuses, merged) is in the same file; check it before declaring any step done.
- **Completion.** Steps 0–6 executed in order; a failing regression test proves the fix; the report carries proof-backed claims only, with no residual unverified assertions.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0. Intake | [`references/step-0-intake.md`](references/step-0-intake.md) | Symptom statement, target lang, repro command, run state; iron-law gate; invocation. |
| 1. Investigate | [`references/step-1-investigate.md`](references/step-1-investigate.md) | Read errors, build a tight red-capable loop, check recent changes, gather multi-component evidence, trace data flow. |
| 2. Pattern | [`references/step-2-pattern.md`](references/step-2-pattern.md) | Minimize the repro, find working examples, compare against references, identify differences, understand dependencies. |
| 3. Hypothesis | [`references/step-3-hypothesis.md`](references/step-3-hypothesis.md) | Form 3–5 ranked falsifiable hypotheses; test minimally, one variable at a time; pick the language debugger variant. |
| 3a/3b/3c. Language debugger | [`step-3a-python-debugger.md`](references/step-3a-python-debugger.md), [`step-3b-node-debugger.md`](references/step-3b-node-debugger.md), [`step-3c-rust-debugger.md`](references/step-3c-rust-debugger.md) | Python (pdb + debugpy), Node/TS (node inspect + CDP, profiles), Rust (dbg!, RUST_BACKTRACE, rust-gdb/lldb). |
| 4. Implement | [`references/step-4-implement.md`](references/step-4-implement.md) | TDD cycle: RED failing test, GREEN single fix, per-language verify, REFACTOR; rule of three; question architecture at 3+ failures. |
| 5. Verify & finish | [`references/step-5-verify.md`](references/step-5-verify.md) | Verification checklist, language cleanup pass (delegates to 5a/5b/5c), guardrails final pass, reporting format. |
| 5a/5b/5c. Language verify | [`step-5a-python-verify.md`](references/step-5a-python-verify.md), [`step-5b-node-verify.md`](references/step-5b-node-verify.md), [`step-5c-rust-verify.md`](references/step-5c-rust-verify.md) | Per-language verification + cleanup grep. |
| 6. Guardrails | [`references/step-6-guardrails.md`](references/step-6-guardrails.md) | Red-flags list, common-rationalizations table, TDD rationale, TDD cycle detail; cross-cutting rules applied before reporting done. |
