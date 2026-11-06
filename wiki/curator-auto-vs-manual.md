---
title: Automatic vs Manual Transitions
created: 2026-11-06
updated: 2026-11-06
type: comparison
tags: [automatic, manual, transitions, curator]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Automatic vs Manual Transitions

The curator supports both automatic (background) and manual (user-initiated) skill transitions.

## Automatic transitions

Driven by `apply_automatic_transitions()` on each curator pass. Moves skills `active → stale → archived` based on `stale_after_days` and `archive_after_days`. Skips pinned, cron-referenced, and locked skills. Seeds baseline records on first sight so the inactivity clock starts at first sight, not epoch.

## Manual transitions

User-initiated via CLI:
- `hermes curator archive <skill>` — manual archive (refuses if pinned)
- `hermes curator restore <skill>` — restore from archive (ledger actor = `user`)
- `hermes curator pin <skill>` / `unpin` — opt in/out of auto-transitions
- `hermes curator prune` — bulk manual archive
- `hermes curator adopt <skill>` — bring an unmanaged skill under curator control

## Actor attribution

Automatic transitions record `actor="curator"`; manual transitions record `actor="user"`; agent-driven mutations record `actor="agent"`. Full audit trail in `tools/skill_ledger.py`.

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-lifecycle]] — lifecycle states
- [[curator-cli]] — manual command surface
- [[skill-audit-ledger]] — actor attribution in the ledger
