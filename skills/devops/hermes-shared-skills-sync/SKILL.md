---
name: hermes-shared-skills-sync
description: "Use when sharing/syncing skills across Hermes profiles."
---

# Hermes Shared Skills via Symlinks (current layout, since 2026-09-14)

**True source of truth = `~/agents-arwaky/skills/`** (git repo, remote rakaarwaky/agents-arwaky).
`~/.hermes/skills` is itself a symlink into it, created by `aa connect`
(`tools/connect/hermes_adapter.py`, symlink provisioning — commit a47f3e3).
Deliberate design: edits by any agent anywhere write through the chain into the repo,
and every harness (Hermes, Qwen Code, OpenCode, Antigravity) reads the same tree.

Chain (current, since 2026-09-14 11:53): `profiles/<p>/skills` -> `~/.hermes/skills` ->
`~/agents-arwaky/skills` (real files). The WHOLE root skills dir is one symlink per
profile, not the individual skill subdirs — so every profile sees the identical, full
hub set and new hub skills appear with zero re-sync step.

Consequence to remember: per-profile skill state (`.usage.json`, `.curator_state`,
`.bundled_manifest`, `.hub/`) is now SHARED through the hub root, and profile-unique
skills must live in the hub (they would otherwise be invisible). This supersedes the
per-skill "symlink buta" layout and the 2026-09-13 "copy, never link" rule.

## Sync procedure
No re-sync needed any more. `~/.hermes/scripts/symlink_profile_skills.py` (per-skill
linking) is OBSOLETE — do not run it: `profiles/<p>/skills` is no longer a real dir, so
its `shutil.move` / `rmdir` steps fail or misbehave.

One-time migration (what was actually done, reproducible for a new profile):
1. `mv` any profile-unique skill dir into the hub UNDER ITS CATEGORY (`<hub>/<category>/<name>`)
2. `mv` all non-symlink entries (state files, `.hub/`) out to a timestamped backup.
3. `find <dir> -maxdepth 1 -type l -delete && rmdir <dir> && ln -s ~/.hermes/skills <dir>`.

## Layout rule (user's standing rule)
HUB skills NEVER sit directly at `skills/` root — every skill dir must live inside a
category subfolder (`skills/devops/foo/`, `skills/autonomous-ai-agents/bar/`).
`skill_manage create` defaults to the root, so ALWAYS pass `category=` (e.g.
`category="devops"`). If a skill ever appears at root (also happens when relocating
profile-unique skills into the hub), move it into a matching category right away.
Root-level bare dirs that are categories-only (apple, email, web, social-media hold just
DESCRIPTION.md) are fine; a root dir containing SKILL.md is a violation.

## Verify after changing the layout
`hermes -p <p> skills list | tail -2` — expect the same count on every profile
(139 = 127 local + 12 hub-installed as of 2026-09-14).

## Facts (verified 2026-09-14)
- Hermes walks the profile `skills/` dir and follows symlinked skill/category dirs fine
  (`hermes -p <prof> skills list` counts them as local, e.g. linus 97 entries).
- `skills.external_dirs` (config) is the native no-symlink alternative: fallback
  read-only dirs, local copies win name collisions. Tested working (linus +55 skills)
  but user preferred symlinks.
- Loader indexes hyphen names from hub underscore dirs (`anytype_mcp` → `anytype-mcp`).

## Pitfalls
- Root-symlinking a profile's whole `skills/` dir is now the intended layout, but it
  silently hides any profile-unique skill — relocate those into the hub FIRST.
- A profile whose `skills/` is a symlink: `find <path>` (no `-L`) returns 0 SKILL.md,
  which looks like a broken install. Always use `find -L` or `hermes -p <p> skills list`.
- Backup dir `skills-pre-symlink/` must stay OUTSIDE any `skills/` tree, and name the
  backups `<p>-<timestamp>` so the pre-migration per-skill backups are not overwritten.
- `hermes skills inspect` resolves hub/marketplace sources, NOT local profile skills —
  use `skills list` / `skill_view` to verify local loading.