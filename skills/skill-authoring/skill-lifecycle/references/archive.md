---
title: Archive
role: reference
mode: archive
---

# Archive

Archive a named skill into `_archive/` instead of deleting it permanently.

1. Plan the archive (dry-run by default):

```bash
aa skills archive CATEGORY/SKILL
```

2. Confirm the plan, then pass `--apply` to execute:

```bash
aa skills archive CATEGORY/SKILL --apply
```

3. Rebuild the catalog:

```bash
aa skills catalog
```

4. Run `aa skills validate` to confirm no empty category or placement issues remain.

## Completion

- The named skill was moved into `_archive/` (never permanently deleted unless `--hard-delete` was explicitly passed).
- The catalog was rebuilt.
- `aa skills validate` reports no placement issues left behind.
