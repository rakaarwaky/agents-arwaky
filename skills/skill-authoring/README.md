# Skill-authoring pack

Seven skills with disjoint scopes, plus one shared pipeline library. This file is the pack entrypoint — it
answers "which skill do I use".

## ROUTING

| Goal | Skill | Where |
|---|---|---|
| Author / validate / audit a `SKILL.md` | `skill-design` | `aa skills validate | show | list` |
| Find / catalog / move / organize skills | `skill-library` | `aa skills catalog --check | discover | move | new-category` |
| Prune / consolidate / merge / weed / archive skill trees | `skill-lifecycle` | `aa skills weed | archive | merge-plan` |
| Create skills for things you keep typing out | `skill-learning` | `skills/skill-authoring/skill-learning/` |
| Edit skills to adapt to conditions and demand | `skill-evolving` | `skills/skill-authoring/skill-evolving/` |
| Remove skills and surfaces you never use | `skill-unlearn` | `skills/skill-authoring/skill-unlearn/` |
| Learn, evolve, and unlearn skills from session traces (one pass) | `skill-traces` | `/skill-traces --learn [--evolve --unlearn]` → `aa skills trace-collect | trace-materialize | trace-state` |

The three trace-learning skills (`skill-learning`, `skill-evolving`, `skill-unlearn`) all
run on the `aa skills` trace verbs (`trace-collect`, `trace-usage`, `trace-phrases`, `trace-state`), backed by
`capabilities_skills_traces` and `capabilities_skills_state` in `modules/skills`.
They produce phrases, usage counts, and stale-skill signals in a single pass; each skill curates only its own action
group from the shared `report.md` / `actions.json` run directory.

## Pack tooling

The tooling is a first-class feature of the `aa` CLI:

```bash
aa skills <subcommand>
```

Read-only subcommands (`list`, `show`, `validate`, `catalog --check`,
`discover`, `weed`, `merge-plan`) run immediately. Mutating
subcommands (`repair`, `move`, `archive`, `new-category`) default to
dry-run — pass `--apply` to execute. Every subcommand accepts
`--skills-root PATH`; the authoring subcommands also accept `--json`.
Skill content repair (`aa skills repair`) is the `skill-design` audit
mode; duplicate/obsolete pruning (`aa skills weed` / `aa skills archive`)
is the `skill-lifecycle` mode; category moves and creation
(`aa skills move` / `aa skills new-category`) are `skill-library` modes.
CI runs `aa skills validate --summary` and `aa skills catalog --check` on
every pull request (`.github/workflows/ci.yml`); run both locally before
pushing.

## Catalog

`CATALOG.md` at the skills root is the master index. Rebuild with:

```bash
aa skills catalog
```

`catalog --check` is the drift gate: it regenerates to a temp file and exits
3 when the tracked artifact does not match the live tree.

## Rules

The executable rules live in
`modules/shared/src/skills/taxonomy_skills_rule_vo.py`; the rules
reference was `skills/skill-authoring/skill-design/references/skill-rules.md`
and is now folded inline into each skill's SKILL.md under "Validation Rules".
Provenance for each rule is recorded in
`modules/shared/src/skills/taxonomy_skills_rule_vo.py` (CITATIONS table).
