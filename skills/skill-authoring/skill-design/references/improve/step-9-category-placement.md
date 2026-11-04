# Improve — Step 9: Category-placement audit

**Goal:** you can audit and fix skill category placement — move misplaced skills, create a category when none fits, and leave the catalog rebuilt and lint clean.

Use this when skills may be in the wrong category.

1. Run:

```bash
sdc lint
```

2. Read the catalog via the CLI (no need to open the file manually):

```bash
sdc catalog --read
```

3. The catalog's `## Categories` table already carries each category's description, so it is enough to judge placement (step 4). Open `DESCRIPTION.md` directly only when you will **create or edit** a category's description (steps 6/7) or when `sdc lint` flags `missing-category-description` / `empty-category-description` — the catalog row is a stale snapshot until `sdc catalog` is rebuilt.
4. Identify skills whose name or description conflicts with their current category.
5. If duplicate or obsolete skills need pruning, route to `skill-design --prune` — this mode only decides category placement.

6. If no category fits, create one:

```bash
sdc create category CATEGORY_NAME --description "CATEGORY_DESCRIPTION" --apply
```

7. Move each misplaced skill:

```bash
sdc move CATEGORY/SKILL TARGET_CATEGORY --apply
```

8. Rebuild the catalog:

```bash
sdc catalog
```

9. Verify the moved skills appear under the correct category.

## Commands

| Command | Use |
| ------- | --- |
| `sdc lint` | Detect placement issues (`empty-category`, `missing-category-description`, etc.). |
| `sdc catalog --read` | Read the catalog's `## Categories` table without opening the file. |
| `sdc create category CATEGORY_NAME --description "CATEGORY_DESCRIPTION" --apply` | Create a new category when no existing one fits. |
| `sdc move CATEGORY/SKILL TARGET_CATEGORY --apply` | Move a misplaced skill to the correct category. |
| `sdc catalog` | Rebuild the catalog after moves or category changes. |

### Pitfalls

- **Empty source category**: moving the last skill out of a category leaves it empty, and `sdc lint` flags `empty-category`. Delete the empty `DESCRIPTION.md` and category directory, or retire the category row in `CATALOG.md`.
- **Dangling paths**: after a move, grep the pack for the old `category/skill-name` path and update any hardcoded references.

### Completion

- Every misplaced skill identified in steps 4–7 has been moved.
- Duplicates and obsolete skills have been routed to `skill-design --prune`.
- The catalog was rebuilt after moves.
- `sdc lint` reports no placement issues.
