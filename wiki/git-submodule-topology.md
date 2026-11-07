---
title: agents-arwaky git submodule topology
created: 2026-11-07
updated: 2026-11-07
type: entity
tags: [git, submodules, repo-structure]
sources: [raw/notes/2026-11-07-git-submodule-repair.md]
confidence: high
---

# agents-arwaky git submodule topology

`agents-arwaky` is a parent repo that embeds four independent upstream
repos as submodules under `internal/`, plus several under `vendor/` and one
skill app under `skills/`.

## internal/* (first-party, rakaarwaky account)

| Submodule path | Upstream URL | Pin at 2026-11-07 |
|---|---|---|
| `internal/blender-arwaky` | `https://github.com/rakaarwaky/blender-arwaky.git` | `bf7691ce` |
| `internal/lint-arwaky` | `https://github.com/rakaarwaky/lint-arwaky.git` | `6eac4437` (v3.14.1-20-g) |
| `internal/qwen-web-arwaky` | `https://github.com/rakaarwaky/qwen-web-arwaky.git` | `f04388cd` |
| `internal/vision-arwaky` | `https://github.com/rakaarwaky/vision-arwaky.git` | `66c0b3f5` (v3.0.0-14-g) |

All four set `ignore = dirty` in `.gitmodules`, so the parent reports a clean
status even when a submodule worktree has local uncommitted edits. This masks
drift — see [[git-submodule-repair]] for the "submodule HEAD vs parent-pinned
commit" section.

## vendor/* (third-party)

`vendor/context7`, `vendor/fetch-mcp`, `vendor/codegraph`, `vendor/omniroute`,
`vendor/9router` — each a gitlink under the same layout. `vendor/9router`'s
gitdir was also observed missing/broken as of 2026-11-07 and was not repaired
in that session; it will need the same repair as [[git-submodule-repair]]
if touched.

## skills/automation/brave-automation/app

A gitlink to `https://github.com/rakaarwaky/brave-automation-arwaky.git`.
Same pointer + `.git/modules/` layout as everything else.

## Layout invariants

- Each submodule worktree has a `.git` *file* (not a directory) with
  `gitdir: ../../.git/modules/<name>`.
- The real gitdir lives at the parent's `.git/modules/<name>` and must be a
  **flat** gitdir (top-level `HEAD`, `objects/`, `refs/`), never a directory
  containing a nested `.git/`.
- Breaking either half of that pair produces the
  `fatal: not a git repository: .../.git/modules/<name>` error — the core
  failure mode this page exists to diagnose quickly.

## Related

- [[git-submodule-repair]] — step-by-step fix when the layout breaks
- [[repo-git-state]] — where each repo/branch sits right now
