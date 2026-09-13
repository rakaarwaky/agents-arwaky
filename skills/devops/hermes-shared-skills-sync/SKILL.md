---
name: hermes-shared-skills-sync
description: "Use when sharing/syncing skills across Hermes profiles."
---

# Hermes Shared Skills via Symlinks (current layout, since 2026-09-14)

User decision: hub `~/.hermes/skills/` is the SINGLE source of truth. Profile skill dirs
that exist in the hub are replaced by symlinks INTO the hub ("symlink buta" — accepted
drift: editing a skill in a profile edits it for everyone). Only profile-unique skills
remain real directories. This supersedes BOTH the old shared-skills farm (dangling links)
and the 2026-09-13 "copy, never link" rule.

## Sync procedure
`python3 ~/.hermes/scripts/symlink_profile_skills.py` — for each real dir in
`profiles/<p>/skills/<name>`: if hub has `<name>` or its hyphen/underscore variant,
move the copy to `~/.hermes/skills-pre-symlink/<p>/<name>` (backup, outside the skills
tree so loaders never see it) and symlink under the HUB's canonical name. Idempotent;
safe to re-run after `hermes update` or new skill installs.

## Facts (verified 2026-09-14)
- Hermes walks the profile `skills/` dir and follows symlinked skill/category dirs fine
  (`hermes -p <prof> skills list` counts them as local, e.g. linus 97 entries).
- `skills.external_dirs` (config) is the native no-symlink alternative: fallback
  read-only dirs, local copies win name collisions. Tested working (linus +55 skills)
  but user preferred symlinks.
- Loader indexes hyphen names from hub underscore dirs (`anytype_mcp` → `anytype-mcp`).

## Pitfalls
- Never point a profile's WHOLE `skills/` dir at the hub — profile-unique skills live there.
- Backup dir `skills-pre-symlink/` must stay OUTSIDE any `skills/` tree.
- `hermes skills inspect` resolves hub/marketplace sources, NOT local profile skills —
  use `skills list` / `skill_view` to verify local loading.