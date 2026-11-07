---
title: agents-arwaky current git state
created: 2026-11-07
updated: 2026-11-07
type: summary
tags: [git, repo-structure, state]
sources: [raw/notes/2026-11-07-git-submodule-repair.md]
confidence: medium
---

# agents-arwaky current git state

Point-in-time snapshot as of 2026-11-07, after the submodule repair.
Re-check with live commands before relying on this — `git status`,
`git submodule status`, and `git -C <path> branch --show-current` per
submodule.

## Parent repo

- Path: `/home/raka/agents-arwaky`
- Working tree had local modifications in
  `skills/skill-authoring/app/modules/shared/src/skills_design/
  taxonomy_skills_vo.py` (unrelated to the submodule repair) plus
  ` M internal/qwen-web-arwaky` (submodule pointer drift, see below).

## Submodule branches

All four `internal/*` submodules are on `main` after repair.

| Submodule | Branch | HEAD vs parent pin |
|---|---|---|
| `internal/blender-arwaky` | main | matches `bf7691ce` |
| `internal/lint-arwaky` | main | matches `6eac4437` |
| `internal/qwen-web-arwaky` | main | **ahead**: `19cbe39` vs pin `f04388cd` |
| `internal/vision-arwaky` | main | matches `66c0b3f5` |

## Open decision (as of 2026-11-07)

`qwen-web-arwaky` is ahead of the commit the parent repo pins. Two options
were on the table, not yet resolved:

- Keep the local `19cbe39` and commit the new gitlink in the parent repo, or
- Snap back to `f04388cd` via `git -C internal/qwen-web-arwaky switch f04388cd`
  or `git submodule update -- internal/qwen-web-arwaky` from the parent root.

`vendor/9router`'s gitdir was observed missing with the same fatal signature
as the four internal submodules, and was **not** repaired in this session —
it needs the same fix as [[git-submodule-repair]] before it can be used.

## Related

- [[git-submodule-repair]] — how the broken layout was fixed
- [[git-submodule-topology]] — full submodule map including vendor/*
- [[curator-snapshot-rollback]] — snapshot-before-mutation pattern that
  applies to any risky git layout change
