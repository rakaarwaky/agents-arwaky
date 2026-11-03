# Audit — Scope resolution


The audit auto-resolves its scope from the skills-path argument:

- **Single skill** — the path names one skill folder (`<category>/<skill>/`). Run the checklist below for that one `SKILL.md`; run `aa skills lint` scoped to it.
- **Pack / category** — the path names a category (`<category>/`) or the skills root. Run the single-skill checklist for every `SKILL.md` in the tree, and run `aa skills lint` over the whole tree — it covers the `unique-skill-name`, `unique-description`, `skill-placement`, `missing-category-description`, `empty-category-description`, and `empty-category` rules pack-wide. One pack-wide check the tool does not perform: no dangling cross-skill links.

When the path is ambiguous, default to the single-skill scope if it ends in a folder containing a `SKILL.md`, otherwise the pack scope.
