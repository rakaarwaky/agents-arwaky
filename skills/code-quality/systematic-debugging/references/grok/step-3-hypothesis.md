# Step 3: Hypothesis & Testing (Phase 3)

**Scientific method.**

## 1. Form Ranked Falsifiable Hypotheses

- Generate 3–5 plausible hypotheses before testing any single one.
- Rank them by likelihood and cheapness to falsify.
- State the prediction each hypothesis makes: "If X is the cause, then changing or observing Y should make Z happen."
- Discard or sharpen any hypothesis that does not make a testable prediction.

If the user is present, show the ranked list before testing. They may have domain knowledge that instantly re-ranks it. If the user is AFK, proceed with your ranking.

## 2. Test Minimally

- Test the highest-ranked hypothesis with the smallest possible probe.
- Change one variable at a time.
- Don't fix multiple things at once.
- Prefer debugger/REPL inspection when available; one breakpoint beats ten logs.
- If you add logs, tag every temporary line with a unique prefix such as `[DEBUG-a4f2]` so cleanup is a single search.

Language-specific debugger selection happens here, by `target_lang` from Step 0. Each variant is self-contained: tool selection, REPL quick reference, attach-to-running-process patterns, pitfalls, and one-shot recipes:

- **Python** → [`step-3a-python-debugger.md`](step-3a-python-debugger.md) (pdb + debugpy)
- **TypeScript/Node** → [`step-3b-node-debugger.md`](step-3b-node-debugger.md) (node inspect + CDP)
- **Rust** → [`step-3c-rust-debugger.md`](step-3c-rust-debugger.md) (dbg!, RUST_BACKTRACE, rust-gdb/lldb)

Pick the tool that is cheapest for the situation: `breakpoint()` / `node inspect` / `dbg!` first; attach-to-running-process tools (debugpy, CDP attach, `SIGUSR1`) only when the process is long-lived and can't be restarted clean.

## 3. Verify Before Continuing

- Did it work? → Step 4
- Didn't work? → Form NEW hypothesis, return to §1
- DON'T add more fixes on top

## 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

## Next

When a hypothesis is confirmed and the root cause is identified, proceed to Step 4 (implementation via TDD).
