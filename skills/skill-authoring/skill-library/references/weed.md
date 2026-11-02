---
title: Weed
role: reference
mode: weed
---

# Weed

Remove duplicate and obsolete skills from the library.

1. Run weed:

```bash
aa skills weed
```

2. For duplicate skill names, decide which skill is authoritative.

3. For duplicate descriptions, compare the skills and choose the better maintained one.

4. Archive obsolete skills:

```bash
aa skills archive CATEGORY/SKILL
```

Never delete permanently unless explicitly asked.

5. Rebuild the catalog:

```bash
aa skills catalog
```

6. Report archived skills and any remaining duplicates.

## Completion

- Duplicate skill names have been resolved to one authoritative skill.
- Obsolete skills have been archived (not permanently deleted).
- The catalog was rebuilt.
- The user received a report of archived skills and any remaining duplicates.
