---
title: Curator Consolidation
created: 2026-11-06
updated: 2026-11-06
type: concept
tags: [consolidation, curator, llm-review, skill-merge]
sources: [raw/articles/curator-source.md]
confidence: medium
---

# Curator Consolidation

Consolidation is the opt-in LLM review pass that identifies near-duplicate skills and merges them into umbrella skills. It is **off by default** (`curator.consolidate: false`) and can be enabled per-run with `hermes curator run --consolidate` or globally via config.

## How the fork works

1. A whole-tree snapshot is taken via `snapshot_skills()` (see [[curator-snapshot-rollback]])
2. `apply_automatic_transitions()` runs first (deterministic prune)
3. An auxiliary-model `AIAgent` is forked with `enabled_toolsets=["skills"]`, `max_iterations=9999`, `quiet_mode=True`, `platform="curator"`
4. The agent runs `CURATOR_REVIEW_PROMPT` + candidate list and returns a structured YAML block with `consolidations:` and `prunings:`
5. Classification is reconciled against tool-call audit evidence
6. Cron job skill references are rewritten to point at umbrella skills

## Consolidation vs pruning

- **Consolidation:** skill X is absorbed into umbrella Y (Y is patched/extended with X's content); X goes under `consolidations` with `into: Y`
- **Pruning:** skill X is truly stale/obsolete with no merge target; X goes under `prunings` and is archived

## Hard constraints (from the review prompt)

1. DO NOT touch bundled, hub-installed, or external-dir skills
2. DO NOT delete — archive only
3. DO NOT touch pinned skills
3b. DO NOT touch protected built-ins (currently `plan`)
3c. DO NOT archive cron-referenced skills (may consolidate only)

## Reports

Each consolidation run writes `logs/curator/{YYYYMMDD-HHMMSS}/run.json` + `REPORT.md` with sections for consolidated, pruned, state transitions, and cron rewrites.

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-lifecycle]] — lifecycle states that consolidation operates on
- [[curator-snapshot-rollback]] — safety snapshot before consolidation
