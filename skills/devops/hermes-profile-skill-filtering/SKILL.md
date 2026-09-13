---
name: hermes-profile-skill-filtering
description: Filter a Hermes profile's skills by its SOUL.md role.
version: 1.0.0
metadata:
  hermes:
    tags: [hermes, profiles, skills, config]
---

# Role-based Skill Filtering for Hermes Profiles

Rule (Raka): named profiles are role specialists; the default profile is the
generalist. Irrelevant skills are DISABLED via config, never deleted from disk.
Deletion is the brute path and gets rejected.

## Install vs apply vs embed — three different requests

- **Install into a profile** = copy the skill dir into `profiles/<p>/skills/` (copy,
  never symlink). That alone completes installation; the next session loads it.
- **Apply a skill to a profile** = the agent itself follows the skill's rules against
  that profile's artifacts (`skill_view` it, then audit/rewrite its skills, SOUL, board
  text). A request like "use skill X on profile Y" almost always means THIS, not the
  copy.
- **Embed a rule into a persona** = editing `profiles/<p>/SOUL.md`. That file IS the
  persona and is only ever touched on an explicit request — never as a presumed part
  of installing or applying. A stray edit is recoverable: profiles' SOUL.md/config are
  tracked in the `~/.hermes` git repo, `git checkout -- profiles/<p>/SOUL.md` reverts.

When the phrasing could mean install or apply, ask one short question before writing
anything; guessing wrong in either direction costs a full correction round-trip.

## Mechanism
- Filter: `skills.disabled:` in `~/.hermes/profiles/<p>/config.yaml`
  (global list ∪ `platform_disabled`, minus ESSENTIAL `hermes-agent`).
  Enforced at prompt-build time: `agent/skill_utils.py: get_disabled_skill_names`.
- Audit inputs: each profile's `SOUL.md` defines the role. Enumerate installed
  skills with `skill_names.extract_skill_name` over `rglob('SKILL.md')` under
  `profiles/<p>/skills` (skip `.hub`), read each frontmatter `description:` and
  decide fit. Show the KEEP-vs-DISABLE report with reasons BEFORE writing; only
  then apply. Whitelist style (installed − KEEP) suits a very dirty profile;
  an explicit disable-list suits an already-curated one.

## Safe write procedure
1. Back up: `config.yaml` -> `config.yaml.bak-roleskills` (skip if exists).
2. Edit with the Hermes venv ruamel: `~/.hermes/hermes-agent/venv/bin/python`,
   `YAML()` round-trip, `preserve_quotes=True`. Plain python3 lacks ruamel and
   system pip is PEP-668 blocked. ruamel keeps the ~21 comment lines intact.
3. Only ADD entries (union); never drop existing disabled names.
4. Verify by LOADING the YAML and doing installed−disabled set math, then
   `hermes --profile <p> skills list` (enabled/disabled per row). Regex over the
   disabled block misleads: ruamel rewrites `    - x` to `  - x`.
5. New profile sessions pick the change up; running sessions need a restart.

## Pitfalls
- Throwaway scripts live in `~/.hermes/tmp/`, NEVER in a git working tree —
  untracked files in the repo are noise Raka did not ask for.
- mnemosyne* skills are dead weight in profiles whose config lacks
  `memory.provider: mnemosyne`; check before keeping.
- Keep each profile's own LOCAL skills (born from its work, e.g.
  hermes-kanban-pm in currie) unless the user explicitly asks.
- Re-run the audit after `aa connect` or a Hermes update re-seeds skills.

## Skill-suite audit (usage + writing-quality pass)

`scripts/skill_suite_audit.py <skills-root>` — per-SKILL.md flags: description past the
57-char index window, missing `## When to Use`, oversized body, over-long prose lines,
banned-word hits with line context, plus `use_count`/`view_count` from the sibling
`.usage.json`. Run it before deciding what to disable or what to repair first; it writes
nothing.

## Pitfalls (audit)

- The skill index shows only the first 57 chars of `description`; anything past that is
  invisible to skill selection. Judge fit — and write descriptions — inside that window;
  a trigger buried at char 150-400 never fires.
- `.usage.json` counters are `use_count`, `view_count`, `patch_count`, `last_used_at` —
  there is no `load_count`. Dump one raw record's keys before any counter math: a guessed
  key returns 0 silently and yields a confidently wrong "nothing is used" report. A skill
  with 0 use and 0 view is a disable candidate — name them in the report, don't pre-fill
  `skills.disabled`.
- Banned-word scans hit technical homonyms: `harness = false` is a TOML key, "harness"
  means the agent host, "journey" can be a diagram genre. Verify each hit's line before
  filing it as slop; lexical scans alone find almost nothing in well-written SKILL.md
  files — the real defects are structural (truncated triggers, missing When to Use,
  append-log step lists of 10+ items with 400+ char steps, which belong in `references/`).
- Run multi-probe audits as a file written with write_file, then `python3 <path>` —
  inline python here-docs in `terminal` trip the nested-payload security scan, and
  f-strings cannot contain backslashes (precompute or use `.format`).
