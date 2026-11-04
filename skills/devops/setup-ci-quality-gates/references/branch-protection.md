# Branch protection: GitHub Ruleset

Create the ruleset that makes the gates mandatory on `main`.

**Goal:** no direct push to `main`; every change goes through a PR
that passes all gates.

## Ruleset

Create a ruleset "Protect main - quality gates" (Settings → Rules →
Rulesets), `target: branch`, enforcement `active`:

- **required_status_checks**: Format, Clippy, Build, Tests, Self-Lint —
  with `strict: true` (requires up-to-date).
- **non_fast_forward**: blocked.
- **deletion**: blocked.

(This is why all work here uses worktrees + PRs.)

## Completion

- The ruleset exists on `main` with the five required status checks,
  `strict: true`, and both push blocks.
