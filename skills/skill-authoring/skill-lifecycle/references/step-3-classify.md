---
title: Step 3 — Classify
role: step
---

# Step 3: Classify

Each cluster is one of:

- **duplicate** — identical scope; remove in Phase 1.
- **variant** — same domain, distinct scenarios; consolidate in Phase 2 into one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario.
- **separate jobs** — genuinely different; keep separate and note why in the report.

Detect duplicates and obsolete skills with `aa skills lint`; obsolete skills are archived into `_archive/` (never permanently deleted unless `--hard-delete` is explicitly passed).

Phase 1 removes true duplicates; Phase 2 consolidates variants — never skip Phase 1 (Global Rules: Phase order).
