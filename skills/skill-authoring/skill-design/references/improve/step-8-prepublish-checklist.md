# Improve — Step 8: Pre-publish checklist

**Goal:** you can run the pre-publish checklist and confirm the target skill is ready to publish — frontmatter, lint, body shape, references, and content all pass.

- [ ] `aa skills read <name>` — read back the target `SKILL.md` to confirm frontmatter and body landed correctly.
- [ ] `aa skills lint` passes (catalog in `step-4-validator-catalog.md`).
- [ ] Frontmatter satisfies the Global Rules bullets: mandatory keys, Frontmatter semantics, YAML hygiene, parser limits.
- [ ] Body within ~100–200 lines; overflow moved into `references/`; every reference, whatever its depth, is linked from `SKILL.md` (Global Rules: Structure).
- [ ] Every sibling mention and cross-skill link names a skill that exists in the tree (Global Rules: dangling refs).
- [ ] Content detail (`step-7-content-detail.md`) satisfied.
- [ ] `aa skills catalog` has been run so `skills/CATALOG.md` reflects the current frontmatter.
