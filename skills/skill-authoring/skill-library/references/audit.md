---
title: Audit
role: reference
mode: audit
---

# Audit

Use this when skills may be in the wrong category.

1. Run:

```bash
aa skills validate
```

2. Run:

```bash
aa skills weed
```

3. Read `CATALOG.md`.
4. Read the `DESCRIPTION.md` file for each category involved.
5. Identify skills whose name or description conflicts with their current category.
6. If no category fits, create one:

```bash
aa skills new-category CATEGORY_NAME "CATEGORY_DESCRIPTION"
```

7. Move each misplaced skill:

```bash
aa skills move CATEGORY/SKILL TARGET_CATEGORY
```

8. Rebuild the catalog:

```bash
aa skills catalog
```

9. Verify the moved skills appear under the correct category.

## Completion

- Every misplaced skill identified in steps 5–7 has been moved or archived.
- The catalog was rebuilt after moves or archives.
- `aa skills validate` reports no placement issues.
