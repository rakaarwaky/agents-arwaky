---
title: Hermes Agent Curator Source
created: 2026-11-06
updated: 2026-11-06
type: raw
tags: [source, curator]
sources: []
confidence: high
---

# Hermes Agent Curator Source

This raw file documents the source material for all curator wiki pages. It is **immutable** — corrections go in wiki pages, not here.

## Source files analyzed

| File | Lines | Role |
|---|---|---|
| `agent/curator.py` | 1214 | Main orchestrator — state persistence, config, idle/interval gating, automatic transitions, consolidation fork, run claim, public entrypoint |
| `agent/curator_backup.py` | 492 | Snapshot + rollback — tar.gz snapshots, exclusion rules, cron restoration, undoable rollback |
| `hermes_cli/curator.py` | 766 | CLI commands — 18 subcommands, status display, pin/unpin/archive/restore |
| `hermes_cli/subcommands/curator.py` | 22 | CLI subcommand parser wiring |
| `tools/skill_usage.py` | 773 | Per-skill telemetry — `.usage.json`, lifecycle states, curation eligibility |
| `tools/skill_ledger.py` | 633 | Per-mutation audit trail — `.curator_ledger.jsonl`, content-addressed blobs |

## Key invariants from source

1. Only curator-managed skills are touched
2. Never delete, only archive (recoverable)
3. Pinned skills bypass all auto-transitions
4. Consolidation fork uses auxiliary client, never touches main session prompt cache
5. Bundled, hub-installed, and external-dir skills are off-limits
6. Protected built-ins (currently `plan`) are never touched
