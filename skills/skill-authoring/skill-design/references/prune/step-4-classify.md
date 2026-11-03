# Step 4: Classify

Decide what each cluster is so Phase 1 and Phase 2 of the execute step know what to do.

**Goal:** label every cluster as duplicate, variant, shared-tooling, or separate jobs.

## Classes

Each cluster is one of:

- **duplicate** — identical scope; remove in Phase 1.
- **variant** — same domain, distinct scenarios; consolidate in Phase 2 into one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario.
- **separate jobs** — genuinely different; keep separate and note why in the report.
- **shared tooling / bounded purpose** — two skills that wrap the same underlying tooling or share a narrow, overlapping purpose consolidate into one folder in Phase 2; the surviving folder keeps the more complete body and absorbs the other's scenario-specific rules into `references/`.

Detect duplicates and obsolete skills with `aa skills lint`; obsolete skills are archived into `_archive/` (never permanently deleted unless `--hard-delete` is explicitly passed).

Phase 1 removes true duplicates; Phase 2 consolidates variants and shared tooling — never skip Phase 1 (`step-0-overview.md` classification rules).

## Completion

- Every cluster has exactly one class label.
- `aa skills lint` ran and flagged duplicates and obsolete skills.
- Phase order is respected: Phase 1 is planned before Phase 2.
