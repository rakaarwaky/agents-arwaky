# Step 1: Root Cause Investigation (Phase 1)

**BEFORE attempting ANY fix.** Read errors, build a tight feedback loop, gather evidence, and trace data flow.

## 1. Read Error Messages Carefully

- Don't skip past errors or warnings — they often contain the exact solution.
- Read stack traces completely; note line numbers, file paths, error codes.

**Action:** Use `read_file` on the relevant source files. Use `grep` / `codegraph_explore` to find the error string in the codebase.

## 2. Build a Tight Feedback Loop

The feedback loop is the debugging work. Before reading code to build a theory, create or identify a command that goes red on the user's exact symptom and green when the bug is fixed. A tight loop is fast, deterministic, agent-runnable, and specific enough to catch this bug — not merely "doesn't crash".

When a clean repro is hard, spend disproportionate effort building the loop. Guessing without a red-capable loop is the failure mode this skill exists to prevent.

**Ways to construct a loop — try in roughly this order:**

1. **Failing test** at the seam that reaches the bug: unit, integration, or end-to-end.
2. **HTTP script / curl** against a running dev server.
3. **CLI invocation** with fixture input, diffing stdout/stderr against expected output.
4. **Headless browser script** (Playwright/Puppeteer) asserting on DOM, console, or network.
5. **Replay a captured trace**: HAR, request payload, event log, queue message, or webhook body.
6. **Throwaway harness** that boots the smallest useful slice of the system and calls the failing path.
7. **Property / fuzz loop** when the bug is intermittent wrong output over a broad input space.
8. **Bisection harness** suitable for `git bisect run` when the bug appeared between two known states.
9. **Differential loop** comparing old vs new version, two configs, two providers, or two datasets.
10. **Human-in-the-loop script** only as a last resort: script the human steps and capture their result so the loop stays structured.

**Tighten the loop once it exists:**

- Make it faster: cache setup, narrow scope, skip unrelated initialization.
- Make the signal sharper: assert the exact symptom, not generic success.
- Make it more deterministic: pin time, seed randomness, isolate filesystem, freeze network.

For non-deterministic bugs, the immediate goal is a higher reproduction rate, not perfection. Run the trigger 100x, parallelize, add stress, narrow timing windows, or inject sleeps. A 50% flake is debuggable; a 1% flake usually is not.

**Action:** Run the loop with `run_terminal_command`:

```bash
# Run a specific failing test
pytest tests/test_module.py::test_name -v

# Or run a scripted repro
python scripts/repro_bug.py

# Or run a high-repetition flaky repro
for i in {1..100}; do pytest tests/test_flake.py::test_name -q || break; done
```

## 3. Check Recent Changes

- What changed that could cause this? Git diff, recent commits.
- New dependencies, config changes.

**Action:**

```bash
git log --oneline -10
git diff
git log -p --follow src/problematic_file.py | head -100
```

## 4. Gather Evidence in Multi-Component Systems

**WHEN the system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation** at each component boundary:

- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks. THEN analyze evidence to identify the failing component. THEN investigate that specific component.

## 5. Trace Data Flow

**WHEN the error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source.
- Fix at the source, not at the symptom.

**Action:** Use `grep` / `codegraph_explore` to trace references:

```bash
grep -rn "function_name(" src/
grep -rn "variable_name\s*=" src/
```

## Investigation Tools

- **`grep` / `codegraph_explore`** — find error strings, trace function calls, locate patterns
- **`read_file`** — read source with line numbers for precise analysis
- **`run_terminal_command`** — run tests, check git history, reproduce bugs
- **`web_search` / `web_fetch`** — research error messages, library docs

For complex multi-component debugging, dispatch investigation subagents in parallel (Orca worktrees when isolation is needed):

- Goal: "Investigate why [specific test/behavior] fails"
- Context: error, file, test command; instruct: read error, reproduce, trace data flow, report findings — do NOT fix yet.

## Step 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] A tight loop command exists and has been run at least once
- [ ] Loop is red-capable: it asserts the user's exact symptom, not a nearby failure
- [ ] Loop is deterministic, or a flaky bug has a high enough reproduction rate to debug
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypotheses can be stated and tested

**STOP:** Do not proceed to Step 2 until you understand WHY it's happening.
