# Step 4: Classify

Decide what each cluster is so Phase 1 and Phase 2 of the execute step know what to do.

**Goal:** label every cluster as duplicate, variant, shared-tooling, or separate jobs.

## Classes

Each cluster is one of:

- **duplicate** — identical scope; remove in Phase 1.
- **variant** — same domain, distinct scenarios; consolidate in Phase 2 into one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario.
- **separate jobs** — genuinely different; keep separate and note why in the report.
- **shared tooling / bounded purpose** — two skills that wrap the same underlying tooling or share a narrow, overlapping purpose consolidate into one folder in Phase 2; the surviving folder keeps the more complete body and absorbs the other's scenario-specific rules into `references/`.

Detect duplicates and obsolete skills with `sdc lint`; obsolete skills are archived into `_archive/` (never permanently deleted unless `--hard-delete` is explicitly passed).

Phase 1 removes true duplicates; Phase 2 consolidates variants and shared tooling — never skip Phase 1 (`step-0-overview.md` classification rules).

## Confirming a true duplicate (Phase 1 gate)

Descriptions that rhyme are not proof of duplication — before archiving a candidate, prove the two skills own the same job with the same content:

- `sdc discover <domain>` to list the candidates, then diff the scenario content, not the frontmatter. The decisive check is the procedure body (the step files under each skill's `references/`):

```bash
diff <(sed -n '<proc range> p' skills/<cat>/<a>/references/<scenario>.md) \
     <(sed -n '<proc range> p' skills/<cat>/<b>/references/<scenario>.md)
```

- **Byte-equivalent or near-equivalent bodies** (differences are only wording like "connector skill" vs "connector") = true duplicate → archive the less complete one in Phase 1; the more complete body (usually the umbrella's) already owns the scenario, so the dropped folder is dropped, not merged.
- **Different bodies or genuinely distinct completion criteria** = separate jobs or a variant → keep separate or consolidate in Phase 2, do not archive.

Do not rely on `sdc lint` for this — it flags structural issues (name mismatch, unlinked references), not semantic overlap. `sdc discover` + the content diff is the duplicate test.

## Completion

- Every cluster has exactly one class label.
- `sdc lint` ran and flagged duplicates and obsolete skills.
- Phase order is respected: Phase 1 is planned before Phase 2.
