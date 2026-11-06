---
title: Curator Lifecycle Management
created: 2026-11-06
updated: 2026-11-06
type: concept
tags: [lifecycle, curator, skill-state]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Curator Lifecycle Management

The curator moves each managed skill through three lifecycle states based on activity timestamps:

**active → stale → archived**

## State definitions

| State | Meaning | Transition trigger |
|---|---|---|
| `active` | Skill is in regular use | Default state on creation |
| `stale` | No activity for `stale_after_days` (default 14 days) | `apply_automatic_transitions()` |
| `archived` | No activity for `archive_after_days` (default 30 days) | `apply_automatic_transitions()` |

## Automatic transitions logic

`apply_automatic_transitions()` runs on every curator pass. It:

1. Computes `stale_cutoff = now - 14d` and `archive_cutoff = now - 30d`
2. Skips skills that are `pinned`, cron-referenced, or locked
3. Seeds a baseline record on first sight (clock starts at first sight, not epoch)
4. Re-anchors bundled never-used skills once
5. Moves `active → stale` when `anchor ≤ stale_cutoff`
6. Moves `stale → archived` when `anchor ≤ archive_cutoff`
7. Reactivates `stale → active` if activity resumes and `anchor > stale_cutoff`

## Invariant: never archive never-used young skills

If `use_count == 0` (absence of evidence), a skill younger than `stale_after_days` is never archived — the clock must have real activity before staleness accrues.

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-consolidation]] — consolidation can also move skills out of active state
- [[skill-telemetry]] — how activity timestamps are tracked
