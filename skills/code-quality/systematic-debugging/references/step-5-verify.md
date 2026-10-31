# Step 5: Verify & Finish

The run is complete when the regression test is green and the full suite passes. No shortcuts, no guessing.

## Verification Checklist

- [ ] The regression test (from Step 4 §1) passes
- [ ] Full test suite passes with no regressions
- [ ] Output pristine — no warnings, no stray `breakpoint()` / `dbg!()` / `console.log` in committed code
- [ ] The root cause identified in Steps 1–3 is what the GREEN change actually addresses, not a nearby symptom
- [ ] Red flags from Step 0 did not trigger mid-run (if one did, the run has already returned to Step 1)

## Language Cleanup Pass

Run the language variant's own verification checklist before declaring done:

- **Python** → [`step-5a-python-verify.md`](step-5a-python-verify.md)
- **TypeScript/Node** → [`step-5b-node-verify.md`](step-5b-node-verify.md)
- **Rust** → [`step-5c-rust-verify.md`](step-5c-rust-verify.md)

Each variant owns its cleanup greps; the language-independent checklist above still applies on top of it.

## Guardrails — Final Pass

Before reporting done, scan the work against [`step-6-guardrails.md`](step-6-guardrails.md):

- **Common Rationalizations** table — if any row matches what just happened ("Issue is simple, don't need process", "I'll write test after confirming fix works", "One more fix attempt"), the run is not done — return to the matching step.
- **Red Flags** list — if any red flag is now true, the loop is not complete; return to Step 1.

## Reporting

To the user, report in this order:

1. **Root cause** — one or two sentences, naming the specific file/function/line and the mechanism (what value, in what state, at what point diverged from expected).
2. **Fix** — the single change made, with the diff size (lines added/removed).
3. **Proof** — the regression test name and its before/after status (RED → GREEN), plus the full-suite result.
4. **Residual risk** — anything that is now known but out of scope (e.g., the architecture question from Step 4 §6, a known flake rate, a deferred refactor).

No "I think", "probably", or "might". Each claim is backed by a concrete observation from the run.

## Related Skills

- `github-pr-workflow` — take the fix to a merged PR
- `work-on-issue` — if the fix closes a GitHub issue
- `deep-clean` — post-fix cleanup pass (separate from the REFACTOR in Step 4 §4, which stays green-bound)

**No shortcuts. No guessing. Systematic always wins.**
