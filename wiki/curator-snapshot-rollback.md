---
title: Curator Snapshot and Rollback
created: 2026-11-06
updated: 2026-11-06
type: concept
tags: [snapshot, rollback, backup, curator]
sources: [raw/articles/curator-source.md]
confidence: high
---

# Curator Snapshot and Rollback

Before any mutating curator pass, `~/.hermes/skills/` is tar.gz'd under `~/.hermes/skills/.curator_backups/<utc-iso>/` with a `manifest.json`. Rollback first snapshots the current tree (so rollback is itself undoable), then extracts the chosen snapshot into place.

## Snapshot contents

**Included:** all skill dirs, `.usage.json`, `.curator_state`, `.bundled_manifest`, `.curator_suppressed`, plus a copy of `~/.hermes/cron/jobs.json` as `cron-jobs.json`.

**Excluded:**
| Path | Reason |
|---|---|
| `.curator_backups/` | The backup dir itself |
| `.hub/` | Hub-managed; rolling back breaks lockfile invariants |
| `.locks/` | skill_manage per-skill lock files |
| `.git/` | Repo metadata; once inflated backups to 24GB |
| `.archive/` | Recoverable store; rolling back loses entries |
| `.curator_ledger.jsonl` | Append-only audit log |
| `venv/`, `node_modules/`, caches (any depth) | Transient build artifacts |

## Rollback mechanism

1. Resolves target snapshot (newest restorable if no id given)
2. Takes a safety snapshot of the current tree first — rollback is undoable
3. Stages current top-level entries into `.rollback-staging-<id>/`
4. Extracts `skills.tar.gz` into the now-empty tree (path-traversal defense; `filter="data"` on Python 3.12+)
5. On extract failure: removes new entries, unstages; retains staging as `.rollback-unrestored-*` if unstage fails
6. Carries excluded subtrees back from the staged live tree
7. Reconciles cron `skills`/`skill` fields via `_restore_cron_skill_links()` — failures here don't fail rollback

## Default retention

`DEFAULT_KEEP = 2` snapshots are retained; `prune_old_snapshots()` trims excess.

## CLI

- `hermes curator backup` — manual snapshot
- `hermes curator rollback [id]` — restore from snapshot
- `hermes curator list-backups` — list available snapshots
- `hermes curator summarize-backups` — human-readable table

## Related

- [[hermes-agent-curator]] — curator overview
- [[curator-consolidation]] — consolidation triggers a pre-run snapshot
