---
title: Step 5 — Snapshot
role: step
---

# Step 5: Snapshot

Stage the skill-tree paths you touch and commit (`git commit -m "snapshot: before skill-library prune"`). If the tree is dirty for other reasons, `git stash` instead; record the `HEAD` SHA as the rollback target (Global Rules: Rollback).

When the tree holds unrelated in-progress changes, stage only the skill-tree paths you touch — never `git add -A` into the same commit as unrelated work. Use explicit paths (`git add skills/<category>/ skills/CATALOG.md`) and verify the staged set with `git status --short`. A path typo or a sibling subagent committing concurrent work in the same checkout silently pulls unrelated deletions into the commit; unstage anything that is not part of the prune.
