# Prune — Step 0: Overview

Consolidation workflow for the skill tree: collapse duplicate and same-purpose skills into one folder. These files hold the step order; classification and phase rules below are the prune-specific design rules (read only by `--prune`, never by `--create` or `--improve`).

**Goal:** read every skill's description and body, merge skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, and archive the dropped duplicates.

Run the steps in order; each links to the next.

| Step | File | What it does |
| ---- | ---- | ------------ |
| 0a | [`step-0-confirm-root.md`](step-0-confirm-root.md) | Resolve the audit root the prune runs on. |
| 1 | [`step-1-inventory.md`](step-1-inventory.md) | List every skill folder and read frontmatter and body. |
| 2 | [`step-2-group.md`](step-2-group.md) | Cluster skills by semantic scope, verified against bodies. |
| 3 | [`step-3-classify.md`](step-3-classify.md) | Label each cluster: duplicate, variant, shared tooling, or separate jobs. |
| 4 | [`step-4-dry-run.md`](step-4-dry-run.md) | Present the planned prune report and gate on approval. |
| 5 | [`step-5-snapshot.md`](step-5-snapshot.md) | Commit the rollback target before touching the tree. |
| 6 | [`step-6-execute.md`](step-6-execute.md) | Merge the clusters and archive dropped duplicates. |
| 7 | [`step-7-verify-report.md`](step-7-verify-report.md) | Verify the merge and emit the final report. |

## Classification rules

- **Prune standard**: two skills covering the same job become one folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario, one level deep. Genuinely different jobs stay separate; note why in the report.
- **Prune phase order**: Phase 1 (remove true duplicates) always precedes Phase 2 (consolidate variants). Merging skills that are already true duplicates is wasted effort.
- **Provisioned copies**: same-folder-name mirrors under `.agents/skills/` or a harness home are provisioned artifacts — keep the repo source, flag the copy for re-provisioning, never edit the copy.
- **Byte-identical or near-identical bodies**: merge into one; keep the more complete body, drop the rest.
- **Same `name:` in two folders**: one is stale; keep the more complete, delete the other.

## Completion

- The root is resolved, the full inventory is read, clusters are classified, the report is approved, and the snapshot is committed before any merge happens.
