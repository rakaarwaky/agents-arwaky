---
title: Prune vs Archive
created: 2026-11-06
updated: 2026-11-06
type: comparison
tags: [prune, archive, comparison, curator]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Prune vs Archive

The curator never auto-deletes skills. The two fates for unused skills are **stale** (a state) and **archived** (moved to `.archive/`).

| Aspect | Stale state | Archived |
|---|---|---|
| What it is | A lifecycle label (`state: stale`) | Directory moved to `~/.hermes/skills/.archive/` |
| Reversible | Yes — reactivates on new activity | Yes — `hermes curator restore <skill>` |
| Triggered by | `stale_after_days` (14d) of non-use | `archive_after_days` (30d) of non-use |
| Visible in catalog | Yes (marked stale) | No — excluded from prompt |
| Auto transition to | `archived` after 30d non-use | N/A (terminal auto-state) |

## Manual prune

`hermes curator prune --days N` bulk-archives idle skills ≥ N days old. Exempts pinned and already-archived skills. `--dry-run` previews; `-y` skips confirmation. Refuses `--days < 1`.

## Purge

`hermes curator purge` deletes old archived skills per TTL (`curator.archive_ttl_days`, default 0 = disabled). Explicit-only, never automatic. Computes archive timestamp as the newer of record `archived_at` and directory mtime — never purges before both agree.

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-lifecycle]] — stale → archived transition
- [[curator-cli]] — `prune` and `purge` commands
