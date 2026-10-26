# Argument parsing (mode flags, modifiers, auto-detect)

### Argument parsing

Parse the raw argument tokens in **two phases**: first extract the `--approve` / `--submit` modifiers, then resolve the mode from the remaining tokens.

**Phase 1 -- modifier extraction.** Scan the raw argument tokens for standalone `--approve` and `--submit` tokens anywhere in the list. If `--approve` is present, set `APPROVE=true` and remove all its occurrences; otherwise `APPROVE=false`. If `--submit` is present, set `SUBMIT=true` and remove all its occurrences; otherwise `SUBMIT=false`. If BOTH are present, reject with `--approve and --submit are mutually exclusive.` and stop. All of Phase 2 operates on the REMAINING tokens.

**Phase 2 -- mode resolution.** First, reject input that contains more than one of the mode-selecting flags `--main` / `--local` / `--branch` / `--pr` / `--stack` (e.g. `--pr 1 --stack 2`) with `Only one of --main, --local, --branch, --pr, --stack may be given.` and stop. This cross-cutting check runs BEFORE the ordered rules below, because those rules stop at the first matching flag and would otherwise never see the second one. Then parse the remaining tokens with these deterministic rules, applied in order. The first rule that matches wins; do not fall through.

1. **Empty / whitespace-only**: run `git status --porcelain`. Non-empty (uncommitted changes) resolves `MODE=local`; empty (clean tree) resolves `MODE=main`. No target either way.
2. **Starts with `--main`**: `MODE=main`. Reject any extra positional argument with an error.
3. **Starts with `--local`**: `MODE=local`. Reject any extra positional argument with an error.
4. **Starts with `--branch <name>`**: `MODE=branch`, `TARGET=<name>`. The branch name is required -- if the flag appears with no following token (or only with another `--`-prefixed token), reject with `Flag --branch requires an argument: <branch-name>` and stop.
5. **Starts with `--pr <id-or-url>`**: `MODE=pr`, `TARGET=<id-or-url>`. The id or URL is required -- if the flag appears with no following token (or only with another `--`-prefixed token), reject with `Flag --pr requires an argument: <number-or-url>` and stop.
6. **Starts with `--stack <id-or-url>`**: `MODE=stack`, `TARGET=<id-or-url>`. The id or URL is required -- if the flag appears with no following token (or only with another `--`-prefixed token), reject with `Flag --stack requires an argument: <number-or-url>` and stop.
7. **Starts with `--` but does not match any of the above**: reject with `Unknown flag: <flag>. Valid flags: --main, --local, --branch <name>, --pr <number-or-url>, --stack <number-or-url>, --approve, --submit.` and stop. Do NOT fall through to auto-detect.
8. **Plain argument given (no flag prefix)**: auto-detect against the rules below, also applied in order:
   1. Matches the regex `^https?://github\.com/[^/]+/[^/]+/pull/\d+(?:[/?#].*)?$` -- treat as PR URL. `MODE=pr`, `TARGET=<url>`.
   2. Matches `^#?\d+$` (optional leading `#`, then pure digits) -- treat as PR number. `MODE=pr`, `TARGET=<digits without leading #>`. A bare number always stays single-PR mode -- stack review requires the explicit `--stack` flag.
   3. Resolves to a local or remote branch via `git rev-parse --verify --quiet <arg>` or `git rev-parse --verify --quiet origin/<arg>` -- treat as branch. `MODE=branch`, `TARGET=<arg>` (use the bare name, not `origin/<arg>`).
   4. None of the above -- ask the user whether the argument is a PR identifier or a branch name (use the appropriate ask/question tool if available). Provide three options: "PR (treat as PR identifier)", "Branch (treat as branch name)", and "Cancel". On Cancel, stop.

As enforced by the pre-check at the top of Phase 2, the mode-selecting flags `--main` / `--local` / `--branch` / `--pr` / `--stack` are mutually exclusive -- input containing more than one is rejected before the ordered rules run.

**Modifier validation.** After resolving `MODE`, if `APPROVE` or `SUBMIT` is true and `MODE` is `main`, `local`, or `branch` (including an auto-detected branch), reject with `--approve/--submit are only valid with --pr or --stack (PR-based modes).` and stop.

If the user passes both a mode flag and a positional argument (e.g., `/review --local somebranch`), reject with a clear error message and stop -- the mode flags are mutually exclusive and take no free positional. This rejection does NOT apply to `--approve`/`--submit`, which are co-flags rather than modes: `/review 1234 --approve`, `/review --pr 1234 --approve`, `/review --pr 1234 --submit`, and `/review --stack 1234 --submit` are all valid.

