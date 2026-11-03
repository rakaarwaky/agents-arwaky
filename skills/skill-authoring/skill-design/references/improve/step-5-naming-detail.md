# Improve — Step 5: Naming detail

**Goal:** you can name or rename a skill following the gerund-form convention, keep frontmatter and catalog in sync with the directory, and resolve a `name-mismatch` lint report.

- Gerund form preferred (`processing-pdfs`) over `pdf-processing`, when both are valid.
- **Pipeline reference files follow `step-<N>-<name>.md` in execution order** (Pattern B; decision lives in `step-11-reference-pattern.md`). When converting an existing flat `references/<name>.md` tree to a pipeline: renumber in execution order, merge any content that belongs to one step into that step's file, and use `git mv` so history survives. Two files may never share the same step number — if a conversion would produce `step-2-a` and `step-2-b`, the second file's content belongs inside the first file's step, as a section.
- **After renumbering or merging, sweep for old names.** `git mv` does not rewrite links: every cross-reference, Routing-table row, and `skill_dir`/`args` hint that names a reference file (including workflow agent args that tell agents which file to read) must be updated to the new name, and each renamed file's own `# Title` must match its step. Verify with one grep for the deleted file names — every hit is a dangling link and the renumber is incomplete.
- Renaming a skill = rename the directory (`git mv`); the dangling-pointer sweep afterwards is owned by the Verify step of `SKILL.md`. After the rename, verify the skill still resolves and the catalog is consistent:

```bash
aa skills read <new-name>
aa skills catalog
```

`aa skills read` confirms the directory and frontmatter match; `aa skills catalog` refreshes the `## Skills` rows that carry the old path. If `aa skills lint` reports `name-mismatch`, the frontmatter `name:` was not updated to match the new directory name — fix the frontmatter, not the directory.
