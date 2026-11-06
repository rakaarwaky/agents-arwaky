---
title: Curator CLI Commands
created: 2026-11-06
updated: 2026-11-06
type: entity
tags: [cli, curator, commands]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Curator CLI Commands

The curator exposes 18 subcommands under `hermes curator`:

| Command | Purpose |
|---|---|
| `status` | Show config, paused state, last run, grouped counts by state, pinned/unmanaged summaries |
| `usage` | Telemetry for all skills with provenance; `--json`, `--provenance`, sort options |
| `run` | Trigger a curator pass now; `--consolidate` forces LLM merge; `--dry-run`, `--background` |
| `pause` / `resume` | Pause or resume the curator |
| `pin <skill>` / `unpin <skill>` | Protect or unprotect a skill from auto-transitions |
| `lock <skill>` / `unlock <skill>` | User-declared content lock stored in `.usage.json` |
| `list-unmanaged` | List skills without a provenance marker (curation blind spot) |
| `adopt <skill>` | Hand an unmanaged skill to curator (`created_by: agent`) |
| `archive <skill>` / `restore <skill>` | Manually archive or restore an archived skill |
| `list-archived` | List archived skills |
| `prune` | Bulk-archive idle skills ≥ N days; `--dry-run`, `-y` |
| `backup` | Manual tar.gz snapshot |
| `rollback [id]` | Restore from snapshot or single ledger entry |
| `ledger` | Show per-mutation audit ledger; `--compact` GCs blobs |
| `purge` | Delete old archived skills per TTL |

## Actor ledger

User-initiated mutations record `actor="user"`; curator/agent paths record their own — full auditability via `tools/skill_ledger.py`.

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-config]] — config keys driving CLI behavior
- [[curator-snapshot-rollback]] — backup/rollback command details
