---
title: Skill Telemetry
created: 2026-11-06
updated: 2026-11-06
type: concept
tags: [telemetry, skill-usage, usage-tracking]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Skill Telemetry

Skill usage is tracked in `~/.hermes/skills/.usage.json` — a sidecar file deliberately **not** frontmatter in `SKILL.md`, so telemetry stays out of user-authored content and off bundled/hub skills.

## Per-skill record schema

| Field | Type | Meaning |
|---|---|---|
| `state` | `active` \| `stale` \| `archived` | Lifecycle state |
| `pinned` | bool | Opts out of auto-transitions |
| `created_by` | `agent` | Explicit curator-management marker; written by `skill_manage`; never inferred from location |
| `created_at`, `first_seen_at`, `last_activity_at`, `archived_at` | ISO ts | Activity timestamps |
| `views`, `uses` | int | Count of `skill_view` / `skill_manage` executions |
| `activity_window_start` | ISO ts | 14-day recency window anchor |

## Guarantees

- Counter bumps are best-effort — a failure never breaks the tool call
- Writes are atomic under a cross-process lock (`fcntl`/`msvcrt`)
- Lifecycle: `active → stale → archived`

## How the curator reads it

- `curated_report()` — rows for every curator-managed skill, sorted by name; the auto-transition source of truth
- `seed_record_if_missing(name)` — baseline record at first sight so the inactivity clock starts there
- `reanchor_clock(name)` — anchors the clock once; reactivates artifact-stale records

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-lifecycle]] — lifecycle states driven by telemetry
- [[skill-audit-ledger]] — mutation audit trail (companion to telemetry)
