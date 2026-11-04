# Apply Per Tier

Apply findings in strict risk-tier order (from Phase 4 aggregation):

1. **SAFE first** — auto-apply; run tests after.
2. **CAREFUL next** — apply one file at a time; run targeted tests after each file; revert
   any individual fix that breaks a test.
3. **RISKY last** — flag for human review; **do NOT auto-apply**. Present each with a risk
   description and current test-coverage status. Altitude findings usually land here:
   deepening a fix means touching shared infrastructure, so present the deeper fix and let
   the user decide whether to apply now or defer.
4. If the user opted for `--dry-run`, present all three tiers and apply nothing.

Respect project conventions: if the repo has `AGENTS.md` / `CLAUDE.md` or a linter config,
fold those rules into the apply step so fixes match house style.
