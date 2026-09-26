# Role-based skill filtering for Hermes profiles

Load when deciding which skills a named profile should see, when the user says
"install / apply / embed skill X on profile Y", or before touching `skills.disabled`.

## The rule (stated once, pack-wide)

Named profiles are role specialists; the default profile is the generalist. Irrelevant
skills are **disabled in config — never deleted, never parked in a trash folder**:

- Mechanism: `skills.disabled:` (a YAML **list**) in `~/.hermes/profiles/<p>/config.yaml`.
  Effective set = global list ∪ `platform_disabled`, minus the ESSENTIAL `hermes-agent`.
  Enforced at prompt-build time by `agent/skill_utils.py: get_disabled_skill_names`.
- `~/.hermes/.skill-trash/<profile>/` is **not** a Hermes mechanism: it does not exist on
  this host (verified) and no Hermes code reads it. Moving a skill dir there hides it from
  every profile *and* from the other harnesses that read the same pack root, and it destroys
  the pack's git history for that file. Pruning a profile == adding its skill names to
  `skills.disabled`. Any other skill file that mentions pruning points here.
- Deletion is the brute path and gets rejected. Keep each profile's own LOCAL skills (born
  from its work, e.g. hermes-kanban-pm) unless the user explicitly asks otherwise.

## Install vs apply vs embed — three different requests

- **Install into a profile** = put the skill dir in the pack root it shares,
  `~/agents-arwaky/skills/<category>/<name>/SKILL.md`. The next session loads it.
  Current layout is `profiles/<p>/skills` -> `~/.hermes/skills` -> the pack (one symlink for
  the WHOLE root, per profile), so there is no per-profile copy step and no re-sync — see
  `skills-layout.md`. Copying a skill dir into `profiles/<p>/skills/` is only meaningful for
  a profile whose `skills/` is a real directory (the pre-2026-09-14 layout, still visible as
  `~/.hermes/skills-pre-symlink/`); against today's symlinked root such a "copy" writes
  straight into the shared hub and leaks the skill into every profile and harness.
- **Apply a skill to a profile** = the agent itself follows the skill's rules against that
  profile's artifacts (`skill_view` it, then audit/rewrite its skills, SOUL, board text).
  A request like "use skill X on profile Y" almost always means THIS, not the copy.
- **Embed a rule into a persona** = editing `profiles/<p>/SOUL.md`. That file IS the persona
  and is only ever touched on an explicit request — never as a presumed part of installing or
  applying. A stray edit is recoverable: profiles' SOUL.md/config are tracked in the
  `~/.hermes` git repo, `git checkout -- profiles/<p>/SOUL.md` reverts.
- **A SOUL.md can be silently dead on arrival.** Every context file is scanned for prompt
  injection at prompt-build time and ONE regex hit blocks the whole file (no warning, no
  config opt-out), so the persona never loads while the file looks perfect on disk. Always
  run the scan check in `soul-md-injection-scan.md` after writing or editing a persona, and
  grep `Context file SOUL.md blocked:` in `profiles/<p>/logs/agent.log` before theorising
  about why a persona is not showing. Fix by rewording the trigger line, never by loosening
  core.

When the phrasing could mean install or apply, ask one short question before writing
anything; guessing wrong in either direction costs a full correction round-trip.

## Audit inputs

Each profile's `SOUL.md` defines the role. Enumerate installed skills with
`skill_names.extract_skill_name` over `rglob('SKILL.md')` under `profiles/<p>/skills`
(skip `.hub`), read each frontmatter `description:` and decide fit. Show the
KEEP-vs-DISABLE report with reasons BEFORE writing; only then apply. Whitelist style
(installed − KEEP) suits a very dirty profile; an explicit disable-list suits an
already-curated one.

## Safe write procedure

`skills.disabled` is a YAML list, and the CLI can maintain it — but only in one specific input
form, and the wrong form fails silently. All four rows below were reproduced in a throwaway
`HERMES_HOME` against Hermes Agent v0.21.2 (`hermes_cli/config.py::_coerce_config_set_value`
is what parses the value; `agent/skill_utils.py::parse_config_string_list` is what reads it):

| Write | Stored in config.yaml | Effect |
|---|---|---|
| `config set skills.disabled '["a","b"]'` | real list (`- a` / `- b`) | **works** — quote the arg so the shell keeps the brackets |
| `config set skills.disabled a,b` | `skills.disabled: a,b` (scalar) | **silent no-op** — read as the single name `"a,b"`, so nothing is filtered |
| `config set 'skills.disabled[+]' …` | junk key `skills.disabled[+]` + "not a recognized config key" | no append syntax exists |
| `config get skills.disabled --json` | `["a", "b"]` vs `"a,b"` | the read-back that distinguishes a real list from the scalar trap |

So: prefer the CLI, always pass a JSON array literal, and verify with `config get … --json`
(must print a JSON **array**). Because there is no append flag, adding one name is a
read-modify-write of the whole list:

```bash
p=linus; H=~/.hermes/profiles/$p
cur=$(HERMES_HOME=$H hermes config get skills.disabled --json)         # ["a","b"], or null
new=$(python3 -c 'import json,sys; a=json.loads(sys.argv[1] or "[]"); print(json.dumps(sorted(set(a)|{"x"})))' "$cur")
HERMES_HOME=$H hermes config set skills.disabled "$new"
```

The single reason to leave the CLI: `save_config()` rewrites the whole file, so **hand-written
comments and the original quote style are lost** (only the `security` / `fallback_model` commented
example blocks are re-appended). A profile config carrying comments worth keeping is edited with
the Hermes venv's ruamel round-trip instead — that is the ONE sanctioned exception to the pack's
"never hand-edit config.yaml" invariant (see `hermes-profiles` SKILL.md). Everything else stays
on the CLI.

1. Back up: `config.yaml` -> `config.yaml.bak-roleskills` (skip if exists).
2. If (and only if) preserving comments: edit with the Hermes venv ruamel —
   `~/.hermes/hermes-agent/venv/bin/python`, `YAML()` round-trip, `preserve_quotes=True`.
   Plain python3 lacks ruamel and system pip is PEP-668 blocked. ruamel keeps comment lines intact.
3. Only ADD entries (union); never drop existing disabled names.
4. Verify by LOADING the YAML and doing installed−disabled set math, then
   `hermes --profile <p> skills list` (enabled/disabled per row). Regex over the
   disabled block misleads: ruamel rewrites `    - x` to `  - x`. `config get --json`
   printing a quoted string instead of an array means the entry is dead.
5. New profile sessions pick the change up; running sessions need a restart.

## Pitfalls

- Throwaway scripts live in `~/.hermes/tmp/`, NEVER in a git working tree —
  untracked files in the repo are noise the user did not ask for.
- mnemosyne* skills are dead weight in profiles whose config lacks
  `memory.provider: mnemosyne`; check before keeping.
- Re-run the audit after `aa connect` or a Hermes update re-seeds skills.

## Skill-suite audit (usage + writing-quality pass)

`scripts/skill_suite_audit.py <skills-root>` — pass the pack root
(`~/agents-arwaky/skills`) or either path in the symlink chain; the script resolves it.
Per-SKILL.md flags: description past the 57-char index window, missing `## When to Use`,
oversized body, over-long prose lines, banned-word hits with line context, plus
`use_count`/`view_count` from the sibling `.usage.json`. Run it before deciding what to
disable or what to repair first; it writes nothing.

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
