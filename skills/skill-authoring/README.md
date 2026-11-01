# Skill-authoring pack

Seven skills with disjoint scopes, plus one shared pipeline library. This file is the pack entrypoint — it
answers "which skill do I use".

## ROUTING

| Goal | Skill | Where |
|---|---|---|
| Author / validate / audit a `SKILL.md` | `skill-design` | `aa skills validate | show | list` |
| Find / catalog / repair / weed skills | `skill-library` | `aa skills catalog --check | discover | weed` |
| Prune / consolidate / merge skill trees | `skill-lifecycle` | `aa skills repair | move | archive | new-category | merge-plan` |
| Create skills for things you keep typing out | `skill-learning` | `skills/skill-authoring/skill-learning/` |
| Edit skills to adapt to conditions and demand | `skill-evolving` | `skills/skill-authoring/skill-evolving/` |
| Remove skills and surfaces you never use | `skill-unlearn` | `skills/skill-authoring/skill-unlearn/` |

The three trace-learning skills (`skill-learning`, `skill-evolving`, `skill-unlearn`) all
run on the shared deterministic pipeline in [`_trace-pipeline/`](_trace-pipeline/README.md) — one folder of
scripts and references, not a skill (no `SKILL.md` at its root, so the validator does not count it). It produces
phrases, usage counts, and stale-skill signals in a single pass; each skill curates only its own action group
from the shared `report.md` / `actions.json` run directory.

## Pack tooling

The tooling is a first-class feature of the `aa` CLI:

```bash
aa skills <subcommand>
```

Read-only subcommands (`list`, `show`, `validate`, `catalog --check`,
`discover`, `weed`, `rules`, `merge-plan`) run immediately. Mutating
subcommands (`repair`, `move`, `archive`, `new-category`) default to
dry-run — pass `--apply` to execute. Every subcommand accepts
`--skills-root PATH`; the authoring subcommands also accept `--json`.
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
`modules/shared/src/skills/taxonomy_skills_constant.py`; the rendered
reference is `modules/skills/_rules/skill-rules.md` (regenerate with
`aa skills rules --markdown`). Provenance for each rule is recorded in
`modules/shared/src/skills/taxonomy_skills_constant.py`.
