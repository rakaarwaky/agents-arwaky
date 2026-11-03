# Audit — Category-placement audit

Use this when skills may be in the wrong category.

1. Run:

```bash
aa skills lint
```

2. Read the catalog via the CLI (no need to open the file manually):

```bash
aa skills catalog --read
```

3. The catalog's `## Categories` table already carries each category's description, so it is enough to judge placement (step 4). Open `DESCRIPTION.md` directly only when you will **create or edit** a category's description (steps 6/7) or when `aa skills lint` flags `missing-category-description` / `empty-category-description` — the catalog row is a stale snapshot until `aa skills catalog` is rebuilt.
4. Identify skills whose name or description conflicts with their current category.
5. If duplicate or obsolete skills need pruning, route to `skill-design --prune` — this mode only decides category placement.
6. If no category fits, create one:

```bash
aa skills create category CATEGORY_NAME --description "CATEGORY_DESCRIPTION" --apply
```

7. Move each misplaced skill:

```bash
aa skills move CATEGORY/SKILL TARGET_CATEGORY --apply
```

8. Rebuild the catalog (still a CLI verb):

```bash
aa skills catalog
```

9. Verify the moved skills appear under the correct category.

### Pitfalls

- **Empty source category**: moving the last skill out of a category leaves it empty, and `aa skills lint` flags `empty-category`. Delete the empty `DESCRIPTION.md` and category directory, or retire the category row in `CATALOG.md`.
- **Dangling paths**: after a move, grep the pack for the old `category/skill-name` path and update any hardcoded references.

### Completion

- Every misplaced skill identified in steps 4–7 has been moved.
- Duplicates and obsolete skills have been routed to `skill-design --prune`.
- The catalog was rebuilt after moves.
- `aa skills lint` reports no placement issues.
