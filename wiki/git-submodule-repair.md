---
title: Git submodule .gitdir repair
created: 2026-11-07
updated: 2026-11-07
type: concept
tags: [git, submodules, debugging]
sources: [raw/notes/2026-11-07-git-submodule-repair.md]
confidence: high
---

# Git submodule .gitdir repair

When a submodule's `.git` *pointer file* points to a `.git/modules/<name>`
directory that is missing or not itself a valid gitdir, every git command in
the submodule fails with:

```
fatal: not a git repository: <path>/../../.git/modules/<name>
```

This is the signature of a broken parent repo submodule layout, independent
of the submodule's own code state.

## Diagnosis

Three checks in order, all from the parent repo root:

1. **Is it actually a submodule?** `git config --file .gitmodules --list`
   and `git ls-files -s internal/<name>` (mode `160000` = gitlink).
2. **Does the pointer file exist and point where?**
   `cat internal/<name>/.git` — should be `gitdir: ../../.git/modules/<name>`.
3. **Is the target a valid gitdir?** `ls .git/modules/<name>` — a valid
   submodule gitdir has `HEAD`, `config`, `objects/`, `refs/` at its top
   level. A directory containing only a nested `.git/` subdirectory is
   broken.

## The `git init` trap

Running `git init <gitdir>` where `<gitdir>` lives inside the parent's
`.git/` directory nests one more level: it creates `.git/modules/<name>/.git`
instead of making `.git/modules/<name>` the gitdir. This is the wrong layout
for a submodule gitdir. Any repair that uses `git init` inside `.git/modules/`
will re-nest and fail. `git submodule update --init` does not help either
when the parent's layout is already broken.

## Working repair

```bash
cd /path/to/parent-repo

# 1. Remove the broken gitdir
rm -rf .git/modules/<name>

# 2. Bare-clone the upstream into the modules dir (flat gitdir, no nesting)
git clone --bare --quiet https://github.com/<owner>/<repo>.git .git/modules/<name>

# 3. Demote to non-bare so it can hold an index and track a worktree
git -C .git/modules/<name> config core.bare false

# 4. Point HEAD at the branch the worktree uses
git -C .git/modules/<name> symbolic-ref HEAD refs/heads/main

# 5. Rewrite the submodule's .git pointer file
echo "gitdir: ../../.git/modules/<name>" > internal/<name>/\
> .git  # (i.e. the file at internal/<name>/.git)
```

Verify:

```bash
git -C internal/<name> rev-parse --show-toplevel   # -> the submodule worktree
git -C internal/<name> branch --show-current        # -> main
git -C internal/<name> switch main                  # must not fatal
```

## Interpret the post-repair status correctly

After a fresh bare-clone + relink, the submodule's `git status --short`
often shows `D` lines for tracked files. This is index-vs-worktree drift:
the freshly cloned gitdir has an empty/stale index, while the working tree
has all the files. The files are still on disk — not real deletions. The
lines clear after the index is rebuilt (`git -C internal/<name> reset`).

## Submodule HEAD vs parent-pinned commit

A repaired submodule is not automatically at the commit the parent repo
pins. Compare `git -C internal/<name> rev-parse HEAD` with the gitlink
commit from `git ls-files -s internal/<name>`. A mismatch shows up as
` M internal/<name>` in the parent's `git status`. Two valid resolutions:
commit the new pointer in the parent, or snap the submodule back with
`git submodule update -- internal/<name>`.

## Related

- [[git-submodule-topology]] — how agents-arwaky's submodules are wired
- [[repo-git-state]] — current branch / commit state of this repo
- [[curator-snapshot-rollback]] — pre-mutation snapshot idea, analogous to
  `git stash`/branch before a risky layout change
