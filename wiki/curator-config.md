---
title: Curator Configuration
created: 2026-11-06
updated: 2026-11-06
type: entity
tags: [config, curator, settings]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Curator Configuration

Curator settings live in the `curator:` section of `~/.hermes/config.yaml`.

## Config keys

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Curator on/off |
| `interval_hours` | 168 (7 days) | Min gap between curator runs |
| `min_idle_hours` | 2 | Agent must be idle this long before curator fires |
| `stale_after_days` | 14 | Days of non-use before skill → `stale` |
| `archive_after_days` | 30 | Days before skill → `archived` |
| `consolidate` | `false` | LLM consolidation pass off by default; opt-in per-run via `--consolidate` |
| `backup.enabled` | `true` | Snapshot on/off |
| `backup.keep` | 2 | Snapshots to retain |
| `archive_ttl_days` | 0 (disabled) | Auto-purge archived skills after N days |

## Live config example

```yaml
curator:
  consolidate: true
  interval_hours: 24
```

## Provider resolution for the consolidation fork

The auxiliary model is resolved in order:
1. `auxiliary.curator.{provider,model}` (current slot)
2. Legacy `curator.auxiliary.{provider,model}` (deprecated)
3. Main `model.{provider,model}` (fallback)

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-consolidation]] — uses `consolidate` key
- [[curator-cli]] — CLI flags that override config
