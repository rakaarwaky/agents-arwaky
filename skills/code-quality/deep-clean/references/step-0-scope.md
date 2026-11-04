# Step 0 — Scope Capture

Pick what the pipeline runs over: a diff (scoped request) or a named module/crate (module-scoped request).

## Diff-scoped request

"Simplify my changes", "review my recent changes", a PR/branch name. Capture the diff in this default order:

```bash
git diff              # 1. uncommitted working tree (tracked files)
git diff HEAD         # 2. if empty, include staged
git diff --staged     # "staged changes"
git diff HEAD~1       # "the last commit"
git diff main...HEAD  # "this branch" / "my PR"
git diff -- <path>    # specific file(s)
```

If both `git diff` and `git diff HEAD` are empty and there is no git repo or no changes,
fall back to the files the user explicitly named, or recently created/edited this session.
If there is genuinely nothing to review, say so and stop.

**Large-diff warning:** if the diff exceeds ~2000 changed lines, warn that four
subagents each carrying the full diff is token-heavy, and offer to scope it down
(per-directory, per-commit) before proceeding.

## Module/crate-scoped request

"Deep clean this crate", "clean bloat in `foo/`": skip diff capture; operate
directly on the named module or crate.
