---
title: Discover
role: reference
mode: discover
---

# Discover

Find skills by query; recommend the best match; if none, suggest creating one via `skill-design`.

1. **List every skill:**

```bash
aa skills list
```

2. **Rebuild the catalog first if it is missing:**

```bash
aa skills catalog
```

3. **Run discover:**

```bash
aa skills discover QUERY
```

3. **Recommend** the best match from the catalog. If no skill matches, suggest creating one via `skill-design`.

## Completion

- The catalog was rebuilt if it was missing or stale.
- The user receives the best match, or a create-via-skill-design suggestion.
