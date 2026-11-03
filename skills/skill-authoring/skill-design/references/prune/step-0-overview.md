# Prune — Step 0: Overview

Consolidation workflow for the skill tree: collapse duplicate and same-purpose skills into one folder. Design rules and the Phase order are Global Rules in `SKILL.md`; these files hold only the step order.

**Goal:** read every skill's description and body, merge skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, and archive the dropped duplicates.

Run the steps in order; each links to the next.

| Step | File | What it does |
| ---- | ---- | ------------ |
| 0 | [`step-0-confirm-root.md`](step-0-confirm-root.md) | Resolve the audit root the prune runs on. |
| 1 | [`step-1-inventory.md`](step-1-inventory.md) | List every skill folder and read frontmatter and body. |
| 2 | [`step-2-group.md`](step-2-group.md) | Cluster skills by semantic scope, verified against bodies. |
| 3 | [`step-3-classify.md`](step-3-classify.md) | Label each cluster: duplicate, variant, shared tooling, or separate jobs. |
| 4 | [`step-4-dry-run.md`](step-4-dry-run.md) | Present the planned prune report and gate on approval. |
| 5 | [`step-5-snapshot.md`](step-5-snapshot.md) | Commit the rollback target before touching the tree. |
| 6 | [`step-6-execute.md`](step-6-execute.md) | Merge the clusters and archive dropped duplicates. |
| 7 | [`step-7-verify-report.md`](step-7-verify-report.md) | Verify the merge and emit the final report. |
