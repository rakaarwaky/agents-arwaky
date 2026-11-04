# AI review layers

The two AI review layers that run on top of the quality gates.

**Goal:** cubic's ultrareview findings and Repowise's advisory health
gate are both active on the repo, with fixture code excluded from
indexing.

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
  ignore_paths:   # mirror .repowiseIgnore
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

## Completion

- The cubic app is installed on the repo and ultrareview runs on PRs.
- `.repowise/bot.yaml` is committed with `ignore_paths` mirroring
  `.repowiseIgnore`; `.repowise/health-rules.json` tunes the scoring
  policy.
