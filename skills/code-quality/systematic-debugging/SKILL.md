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

**All debugging work is delegated to Grok Build.** The 7-step pipeline is the Grok lane — Grok runs it inside one dedicated Orca worktree. Hermes's lane is four steps: plan the brief, drop `/systematic-debugging <issue-or-error>` into Grok, wait, verify + ship. Hermes never reads code to build a theory, runs the debugger, or writes the fix itself.

## Global rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build via Orca worktree)**: You never write code, run the red-capable loop, test hypotheses, or apply the fix yourself. One Orca worktree with `--agent grok`; Grok Build runs the entire debugging pipeline inside it. No `spawn_subagent` for a debugger — your only "subagent" is the Grok Build TUI.
- **One-shot task drop**: You send exactly one message to Grok: `/systematic-debugging <issue-or-error> [--phase <n>] [--lang <lang>] [--repro <command>]` plus the brief's constraints and acceptance criteria. No mid-run course corrections, no "any progress yet?". Red-flag stops and architecture questions are Grok's to surface in its final report — you do not ping it mid-run.
- **Single point of control**: You own the surviving git, Orca worktree, and PR operations. Grok works inside `cwd: <worktree_path>` and makes one local commit (regression test + minimal fix + refactor); it never pushes or opens a PR (you verify and ship in Step 2).
- **Iron law, delegated.** The two iron-law gates (no fix without root cause; no production code without a failing test) bind Grok's run. Your Step 2 verification re-checks the commit contains both before trusting it — a fix without its regression test is reported as an iron-law violation, not silently accepted.
- **Language routing**: `--lang` if given, else detect from the affected files (Python / TypeScript-Node / Rust) and state it in the brief — Grok picks the matching `3x`/`5x` variant. You do not pick it yourself.
- **Verification re-run.** Grok's "gate passed" claim is self-reported. Step 2 re-runs the regression test and the repo's test/lint/build gate against the clean committed tree in Hermes's own tools before trusting it.
- **Diff discipline.** Verify the commit's diff, not its message: `git diff <base>..HEAD` must show exactly the fix + regression test, not a drive-by refactor.
- **Parallel-First for Hermes's own work**: when you need to read multiple report sections or run multiple read-only checks, batch them in one tool call. Serialize only true dependencies.
- **Exit condition for Hermes**: Grok's report is complete, the commit contains the regression test + minimal fix, and your Step 2 verification (gate green on the clean committed tree, iron-law satisfied, no open red-flag stops you can't escalate) passes. Then you ship (if asked) and report.

## Routing

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree, having just received `/systematic-debugging <issue-or-error>`. Run the 7-step pipeline in `references/grok/` (steps 0–6, with language-variant `3x`/`5x` picked by `target_lang` from step 0).

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
