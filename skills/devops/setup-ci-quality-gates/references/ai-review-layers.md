# AI review layers

## CodeRabbit (app.coderabbit.ai)

GitHub App; no repo config file required (config via UI or repo-wide).
Reviews every PR: walkthrough, actionable inline comments, pre-merge
checks (docstring coverage, title/description), "finishing touches".
Re-review runs on every push.

## Codacy Static Code Analysis

- Add repo at app.codacy.com → analysis runs on each PR.
- **Required check**: `Codacy Static Code Analysis` (add to ruleset).
- Exclusions in `.codacy.yaml` (fixture/test code must not skew metrics):

```yaml
exclude_paths:
- "workspaces-bad/**"
- "workspaces-good/**"
- "crates/*/tests/**"
- "scripts/**"
- "tools/**"

```

- Custom AI instructions in `.github/instructions/codacy.instructions.md`
  (org/repo defaults, run `codacy_cli_analyze` after edits, trivy after
  dependency changes).

## cubic AI reviewer (www.cubic.dev)

GitHub App; runs "ultrareview" on each PR with P1/P2/P3 findings.
No repo config file in this project (UI-configured).

## Repowise PR bot (.repowise/bot.yaml)

Health gate on PRs (advisory): code-health of changed files, change risk,
dead-code findings, blast radius. Config:

```yaml
bot:
  enabled: true
  comment_mode: on_signal
  ignore_paths:   # mirror .codacy.yaml + .repowiseIgnore
    - "workspaces-bad/**"
    - "workspaces-good/**"
    - "crates/*/tests/**"
    - "scripts/**"
    - "tools/**"
    - "log/**"
    - "target/**"
    - "*.md"
  health_gate:
    mode: advisory
    min_new_file_score: 7.0
    block_on_introduced: false

```

Also configure `.repowiseIgnore` (committed) + `.repowise/config.yaml`
exclude_patterns so fixture code is never indexed; `.repowise/health-rules.json`
tunes scoring policy (see the `repowise-scan` skill).
