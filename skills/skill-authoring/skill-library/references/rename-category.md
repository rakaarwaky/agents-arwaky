---
title: Rename Category
role: reference
mode: rename-category
---

# Rename Category

`aa skills move` moves individual skills between categories; it does not rename a
category folder itself. When the user asks to rename a category
(e.g. `research` → `research-study`):

1. `mv skills/<old> skills/<new>` (filesystem rename of the category directory).
2. Update `skills/<new>/DESCRIPTION.md` — keep the frontmatter, update the description
   text if the scope changed.
3. Remove the now-empty `<old>` directory if it still exists.
4. Grep the entire skills tree for the old category path and fix all cross-references:

```bash
grep -rn 'skills/<old>/' skills/ --include='*.md' | grep -v 'skills/<new>/'
```

5. Run `aa skills catalog` to rebuild `CATALOG.md`.
6. Run `aa skills lint` — it will flag any empty category left behind; clean it up.

Do not use `aa skills move` to move skills one-by-one into a new category and then rename
the category — that is two separate operations and the first one is unnecessary if the
category is being renamed in place.

## Completion

- The category directory was renamed and its `DESCRIPTION.md` updated.
- No dangling references to the old category path remain in the skills tree.
- `aa skills lint` reports no issues.
