---
title: Hermes Agent Curator
created: 2026-11-06
updated: 2026-11-06
type: entity
tags: [curator, hermes-agent, skill-maintenance]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Hermes Agent Curator

The **Hermes Agent Curator** is a background maintenance pass for agent-created skills. It exists so that skills created via the self-improvement loop (`skill_manage`) don't pile up forever. Every time the agent solves a novel problem and saves a skill, it lands in `~/.hermes/skills/`. Without maintenance, the catalog accumulates dozens of narrow near-duplicates that pollute skill listings and waste tokens.

## Core invariant

Only curator-managed skills are touched; never delete, only archive (recoverable); pinned skills bypass all auto-transitions; the LLM consolidation fork uses an auxiliary client and never touches the main session's prompt cache.

## Scope

- **Managed:** agent-created skills (those with `created_by: agent` in `.usage.json`)
- **Never touched:** bundled built-ins, hub-installed skills, external-dir skills, pinned skills, protected built-ins (currently `plan`)
- **Maximum destructive action:** archive into `~/.hermes/skills/.archive/` — deletion never happens automatically

## How it runs

The curator is not a cron job. It is triggered by an inactivity check at CLI session start, gateway housekeeping, and `hermes serve` maintenance timer. It fires only when:

1. Curator is `enabled` and not `paused`
2. Enough time has passed since the last run (`interval_hours`, default 7 days)
3. The agent has been idle long enough (`min_idle_hours`, default 2 hours)

Each pass runs `apply_automatic_transitions()` (deterministic stale/archive moves) and, if consolidation is enabled, forks an auxiliary-model review that proposes consolidating near-duplicate skills into umbrella skills.

## Key pages

- [[curator-lifecycle]] — how skills move through active → stale → archived
- [[curator-consolidation]] — the LLM umbrella-merge review fork
- [[curator-snapshot-rollback]] — pre-mutation snapshots and undo
- [[curator-cli]] — all 18 `hermes curator` subcommands
- [[curator-config]] — config keys and defaults
- [[skill-telemetry]] — `.usage.json` usage tracking
- [[skill-audit-ledger]] — `.curator_ledger.jsonl` mutation audit trail
