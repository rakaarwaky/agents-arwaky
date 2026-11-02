---
title: Repair
role: reference
mode: repair
---

# Repair

Fix mechanical faults in `SKILL.md` files (name mismatches, missing category `DESCRIPTION.md`, weak descriptions, broken structure).

1. Run validation:

```bash
aa skills validate
```

2. Run repair (preview by default; pass `--apply` to execute):

```bash
aa skills repair
```

3. Edit remaining invalid `SKILL.md` files — fix missing descriptions, weak trigger wording, invalid YAML, broken references, and nested `SKILL.md` files.

4. Rerun validation until no errors remain.

5. Rebuild the catalog:

```bash
aa skills catalog
```

## Completion

- `aa skills validate` reports no errors.
- No invalid `SKILL.md` files remain.
- The catalog was rebuilt.
