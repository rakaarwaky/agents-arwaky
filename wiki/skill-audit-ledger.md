---
title: Skill Audit Ledger
created: 2026-11-06
updated: 2026-11-06
type: concept
tags: [ledger, audit, skill-ledger, rollback]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Skill Audit Ledger

The curator maintains an append-only JSONL audit trail at `~/.hermes/skills/.curator_ledger.jsonl`, plus content-addressed before/after blobs at `~/.hermes/.curator_backups/blobs/`.

## Per-entry schema

| Field | Type | Meaning |
|---|---|---|
| `id` | uuid | Entry id |
| `ts` | ISO ts | When |
| `actor` | `curator` \| `agent` \| `user` | Who made the mutation |
| `action` | `patch` \| `create` \| `delete` \| `archive` \| `purge` \| `consolidate` \| `rollback` \| `pre-rollback` | Mutation type |
| `skill` | str | Skill affected |
| `before` / `after` | `[{path, sha256}]` | File manifests; contents stored in blobs |
| `evidence` | dict | Freeform: `absorbed_into`, `rollback_target`, etc. |

## Design philosophy

The ledger is **telemetry, not a gate** — every public write swallows and logs errors, except `rollback_entry`, which fails closed when its safety capture fails.

## Size management

- **Trim:** oldest-first lines dropped until under `skills.ledger_max_bytes` (default 5 MB)
- **Compact:** rewrites entries dropping unchanged paths via `_delta`; ids/order/rollback semantics preserved
- **Blob GC:** removes unreferenced, non-fresh blobs (older than 1-hour grace window)

## Rollback semantics

Every entry's paths must be under `HERMES_HOME` — a hand-edited ledger must not become a write-anywhere primitive. Pre-check every blob before changing anything; append a `pre-rollback` safety entry of current state first (so rollback is itself undoable); then write before-files and remove created files.

## Related

- [[hermes-agent-curator]] — curator overview
- [[skill-telemetry]] — usage tracking (companion to ledger)
- [[curator-snapshot-rollback]] — snapshot/rollback infrastructure
