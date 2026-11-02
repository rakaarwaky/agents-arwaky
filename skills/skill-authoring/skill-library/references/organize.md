---
title: Organize
role: reference
mode: organize
---

# Organize

Reorganize or create categories; improve category `DESCRIPTION.md` wording.

1. Read the Categories table in `CATALOG.md`.

2. Identify categories with too many skills, vague descriptions, or no skills.

3. Create new categories where needed:

```bash
aa skills new-category CATEGORY_NAME "CATEGORY_DESCRIPTION"
```

4. Move skills into better categories:

```bash
aa skills move CATEGORY/SKILL TARGET_CATEGORY
```

5. Improve category `DESCRIPTION.md` files where the description is vague.

6. Rebuild the catalog:

```bash
aa skills catalog
```

7. Report the final category structure.

## Completion

- Categories with too many skills have been split; empty categories have been removed.
- Category `DESCRIPTION.md` files have been improved where vague.
- The catalog was rebuilt.
- The user received a report of the final category structure.
