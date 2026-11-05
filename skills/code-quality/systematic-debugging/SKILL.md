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

For any technical issue — test failures, production bugs, build or performance problems — find the root cause before touching a fix. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

## Global Rules

The lane is determined from a physical signal, not by self-identification. Each agent's launcher stamps a fixed attribution env var into every command it runs; the model cannot set these.

```bash
if [[ -n "${HERMES_AGENT:-}" ]]; then echo HERMES
elif [[ -n "${GROK_AGENT:-}" ]]; then echo GROK
else echo UNSET; fi
```

- `HERMES` → **Hermes lane.** Read `references/hermes/`. Stop.
- `GROK` → **Grok lane.** Read `references/grok/`. Stop.
- `UNSET` → stop and report. Do not guess the lane.

Marker provenance:

- **Hermes** re-exports `AI_AGENT=hermes-agent` and `HERMES_AGENT=true` on every command.
- **Grok Build** runs with `GROK_AGENT=1`.

Read only the winning lane's references. Do not read the other lane's.

## Routing

### Hermes lane (Steps 0–3)

| Step | Reference                                                                              | Purpose                                                                                                  |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Detect lang; plan the brief (symptom, repro, phase, constraints, acceptance criteria); create the Orca worktree with `--agent grok`; drop `/systematic-debugging <issue-or-error>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)         | Wait for Grok to finish the pipeline; read its debug summary and commit                                 |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify the iron law (regression test present), re-run the gate on the clean tree; commit/push/PR as appropriate |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (root cause, fix, verification, open decisions, commit/PR, worktree teardown) |

### Grok lane (Steps 0–6, run by Grok Build)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0. Intake | [`references/grok/step-0-intake.md`](references/grok/step-0-intake.md) | Symptom statement, target lang, repro command, run state; iron-law gate; invocation. |
| 1. Investigate | [`references/grok/step-1-investigate.md`](references/grok/step-1-investigate.md) | Read errors, build a tight red-capable loop, check recent changes, gather multi-component evidence, trace data flow. |
| 2. Pattern | [`references/grok/step-2-pattern.md`](references/grok/step-2-pattern.md) | Minimize the repro, find working examples, compare against references, identify differences, understand dependencies. |
| 3. Hypothesis | [`references/grok/step-3-hypothesis.md`](references/grok/step-3-hypothesis.md) | Form 3–5 ranked falsifiable hypotheses; test minimally, one variable at a time; pick the language debugger variant. |
| 3a/3b/3c. Language debugger | [`step-3a-python-debugger.md`](references/grok/step-3a-python-debugger.md), [`step-3b-node-debugger.md`](references/grok/step-3b-node-debugger.md), [`step-3c-rust-debugger.md`](references/grok/step-3c-rust-debugger.md) | Python (pdb + debugpy), Node/TS (node inspect + CDP, profiles), Rust (dbg!, RUST_BACKTRACE, rust-gdb/lldb). |
| 4. Implement | [`references/grok/step-4-implement.md`](references/grok/step-4-implement.md) | TDD cycle: RED failing test, GREEN single fix, per-language verify, REFACTOR; rule of three; question architecture at 3+ failures. |
| 5. Verify & finish | [`references/grok/step-5-verify.md`](references/grok/step-5-verify.md) | Verification checklist, language cleanup pass (delegates to 5a/5b/5c), guardrails final pass, reporting format. |
| 5a/5b/5c. Language verify | [`step-5a-python-verify.md`](references/grok/step-5a-python-verify.md), [`step-5b-node-verify.md`](references/grok/step-5b-node-verify.md), [`step-5c-rust-verify.md`](references/grok/step-5c-rust-verify.md) | Per-language verification + cleanup grep. |
| 6. Guardrails | [`references/grok/step-6-guardrails.md`](references/grok/step-6-guardrails.md) | Red-flags list, common-rationalizations table, TDD rationale, TDD cycle detail; cross-cutting rules applied before reporting done. |
