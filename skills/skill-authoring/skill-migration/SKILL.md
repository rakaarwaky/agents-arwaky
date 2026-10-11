---
name: skill-migration
description: "Audit and convert skills from a foreign harness into Hermes."
version: 1.0.0
author: Raka (rakaarwaky), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [skills, migration, conversion, audit, cross-harness, frontmatter]
    category: skill-authoring
    related_skills: [author-skill-md, skill-manager, skill-design-principles]
---

# Skill migration between harnesses

Move a batch of skills authored for one agent harness (Grok, Claude, Codex, OpenClaw, a vendor
pack) into the Hermes tree, converting frontmatter and tool references while dropping what is
tool-coupled and unportable.

## When to Use

- Asked to "move", "migrate", "copy", or "port" a skills directory (or a pack of `SKILL.md`
  trees) from another harness into `~/.hermes/skills/` or a profile's `skills/`.
- Asked to make a foreign skill "run on Hermes too" / be harness-agnostic.

Don't use for: provisioning repo skills into a client workspace (`skill-manager`), authoring a
skill from scratch (`author-skill-md`), or editing an already-migrated skill in place.

## Procedure

### 1. Audit the source tree before touching the destination

Never bulk-copy a foreign skill tree. First read every source `SKILL.md`'s frontmatter and grep
the whole source tree for that harness's marker terms. A harness leaves distinctive markers: its
tool names, its home/env vars, its paths, its config-file formats, its subagent/spawn primitives,
scheduler/loop primitives, and `../shared/` dependencies (personas, session readers). Count the
hits per skill dir across ALL its files (not just SKILL.md — scripts and references carry them
too).

```
# per-skill marker census (example marker set; adapt to the source harness)
for f in <src>/**/*; do grep -c -i 'grok\|GROK_HOME\|spawn_subagent\|\.grok' "$f"; done
```

Classify each source skill into exactly one of three buckets:
- **KEEP, clean** — zero or near-zero markers; only frontmatter conversion needed.
- **KEEP, convert** — real capability, but references harness-specific tools/paths that have a
  Hermes equivalent. Map each marker to its Hermes tool before writing (see the coupling map
  below). Convert mechanically: string-replace the markers, then re-sweep to confirm zero
  residue.
- **DROP** — the skill's core capability depends on a primitive the target harness does not have
  (image-generation tools, a harness transcript/session format, a config file only that harness
  reads, a persona/subagent system with no target equivalent). Dropping is a legitimate outcome;
  never force-convert a drop bucket skill — a half-converted skill that references a missing tool
  is worse than no skill.

If the source and target trees already share some skills (e.g. `docx`, `pdf`, `pptx` exist in
both), do not copy or overwrite the target copy. Note them as skipped.

### 2. Check the destination layout and name collisions

Hermes profile skill trees are nested `<root>/<category>/<skill>/SKILL.md`; survey the destination
with `search_files(target='files', path='<root>')` to learn its categories before choosing a
home for each migrated skill. Also check semantic collisions: two skills with the same *name*
are a hard collision (loader keys on the directory), but two skills with the same *role* (a generic
`code-review` next to a `github-code-review`) can both load and cause trigger confusion — rename
the incoming one to its distinguishing trait (`strict-code-quality-review`) rather than dropping
the outgoing one. If the repo's `skills/` directory is bind-mounted or symlinked to the profile's
skills dir, a write via the repo path and a write via the profile path hit the same inode —
verify with `stat` (same inode = same tree) instead of assuming two copies.

### 3. Convert frontmatter to the target's required field set

Foreign frontmatter (`name`/`description` plus harness extras like `argument-hint`,
`when-to-use`, `user-invocable`, `disable-model-invocation`, `metadata.short-description`) is
replaced by the target's shape. For a Hermes profile skill:

```yaml
---
name: <same-or-renamed>
description: "Capability, ≤60 chars, period-terminated."
version: 1.0.0
author: <original credit>, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [short, descriptive, tags]
    category: <existing category>
    related_skills: [<existing target skill>]
---
```

- Collapse the foreign `description` (often a 4-line trigger dump) to the one-sentence capability
  statement. The foreign trigger phrases move into the body's `## When to Use`.
- `author` credits the original skill's author first, then `Hermes Agent` as the converter. A
  pack with no named author: use the pack's provenance as the credit (e.g. `grok-bundled`),
  not `Hermes Agent` alone.
- `related_skills` entries must resolve to skills that already exist in the destination tree
  (validated in step 2). An entry pointing at a dropped skill is a validation failure.

### 4. Convert tool and path references in the body

Map source-harness primitives to target primitives (Grok → Hermes example, adapt per source):

| source concept | target equivalent |
|---|---|
| subagent spawn primitive | `delegate_task` (no resume — re-read persisted state instead) |
| periodic scheduler / loop | `cronjob_manage` |
| background monitor / poller | `terminal` (`background=true`, `notify=`) + `process_manage` |
| harness home dir / config file | XDG dirs (`${XDG_DATA_HOME:-$HOME/.local/share}/…`) or the target's config location |
| harness helper script (UUID, scratch dir, cleanup) | stdlib one-liners (`python3 -c 'import uuid; …'`, `tempfile.mkdtemp()`, `rm -f`) |
| harness transcript/session store | target's session recall tool, or drop the skill |
| bundled scripts (`scripts/`, `watch_*.py`) | copy under the skill's `scripts/` dir; strip machine-local paths out of them |

After every replacement pass, grep the converted tree for the source marker set again. Zero
residue (beyond the `author:` credit line, which is intentional) is the completion criterion.

### 5. Validate before declaring done

For each converted skill: frontmatter parses as YAML starting at byte 0; every required field
present; `description` ≤ 60 chars; every `related_skills` entry resolves in the destination tree;
bundled Python scripts pass an `ast.parse` check; shell scripts have no remaining source-harness
home paths. Then `git status` in the destination — report what was kept, converted, dropped, and
skipped, and do not commit unless asked.

## Pitfalls

- **Bulk-copying without the marker census** — a large fraction of a foreign pack is
  tool-coupled and unportable; copying it all in one shot produces a batch of half-broken skills
  and a huge review. Triage per-skill first, convert only the keep buckets.
- **Converting the drop bucket** — if the source primitive has no target equivalent, deleting the
  skill is the correct outcome, not a best-effort rewrite that references a tool the target can
  never call.
- **Forgetting scripts/** — marker terms live in bundled scripts and reference docs, not just
  SKILL.md; the census must span every file in the skill dir, and the final sweep must do the
  same.
- **Skipping `related_skills` validation** — dropping a referenced skill or renaming one
  silently orphans its inbound `related_skills` entries.
- **Overwriting an existing target skill** — when source and target share a skill name, the
  target copy wins; migration adds the missing ones, it never clobbers.
- **Two descriptions over 60 chars** — foreign descriptions are long; re-cut them, don't just
  quote the first line.

## Verification

- Every kept skill has zero source-marker hits outside its `author:` credit.
- Every `related_skills` entry resolves to an existing destination skill.
- The final report enumerates kept, converted, dropped (with reason), and skipped — no source
  skill is unaccounted for.
