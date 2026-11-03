# Audit — Naming detail

- Gerund form preferred (`processing-pdfs`) over `pdf-processing`, when both are valid.
- Renaming a skill = rename the directory (`git mv`); the dangling-pointer sweep afterwards is owned by the Verify step of `SKILL.md`. After the rename, verify the skill still resolves and the catalog is consistent:

```bash
aa skills read <new-name>
aa skills catalog
```

`aa skills read` confirms the directory and frontmatter match; `aa skills catalog` refreshes the `## Skills` rows that carry the old path. If `aa skills lint` reports `name-mismatch`, the frontmatter `name:` was not updated to match the new directory name — fix the frontmatter, not the directory.
