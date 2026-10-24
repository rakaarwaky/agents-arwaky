---
title: Maintenance Workflows
role: reference
---

# Maintenance Workflows

## Audit workflow

Use this when skills may be in the wrong category.

- [ ] Run:

```bash
aa skills validate
```

- [ ] Run:

```bash
aa skills weed
```

- [ ] Read `CATALOG.md`.
- [ ] Read the `DESCRIPTION.md` file for each category involved.
- [ ] Identify skills whose name or description conflicts with their current category.
- [ ] If no category fits, create one:

```bash
aa skills new-category CATEGORY_NAME "CATEGORY_DESCRIPTION"
```

- [ ] Move each misplaced skill:

```bash
aa skills move CATEGORY/SKILL TARGET_CATEGORY
```

- [ ] Rebuild the catalog:

```bash
aa skills catalog
```

- [ ] Verify the moved skills appear under the correct category.

## Repair workflow

Use this when skills have broken or weak metadata.

- [ ] Run:

```bash
aa skills validate
```

- [ ] Run safe mechanical repairs:

```bash
aa skills repair
```

- [ ] Edit remaining invalid `SKILL.md` files.
- [ ] Fix missing descriptions, weak trigger wording, invalid YAML, broken references, and nested `SKILL.md` files.
- [ ] Rerun validation until no errors remain.
- [ ] Rebuild the catalog.

## Weed workflow

Use this when the library may contain duplicates or obsolete skills.

- [ ] Run:

```bash
aa skills weed
```

- [ ] For duplicate skill names, decide which skill is authoritative.
- [ ] For duplicate descriptions, compare the skills and choose the better maintained one.
- [ ] Archive obsolete skills:

```bash
aa skills archive CATEGORY/SKILL
```

- [ ] Rebuild the catalog.
- [ ] Report archived skills and any remaining duplicates.

## Organize workflow

Use this when categories are broad, missing, overlapping, or empty.

- [ ] Read the Categories table in `CATALOG.md`.
- [ ] Identify categories with too many skills, vague descriptions, or no skills.
- [ ] Create new categories where needed:

```bash
aa skills new-category CATEGORY_NAME "CATEGORY_DESCRIPTION"
```

- [ ] Move skills into better categories:

```bash
aa skills move CATEGORY/SKILL TARGET_CATEGORY
```

- [ ] Improve category `DESCRIPTION.md` files where the description is vague.
- [ ] Rebuild the catalog.
- [ ] Report the final category structure.
