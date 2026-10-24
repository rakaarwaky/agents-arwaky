# Skill-authoring pack

Four skills with disjoint scopes. This file is the pack entrypoint — it
answers "which skill do I use".

## ROUTING

| Goal | Skill | Where |
|---|---|---|
| Author / validate / audit a `SKILL.md` | `skill-authoring` | `skills/skill-authoring/skill-authoring/SKILL.md` |
| Find / catalog / repair / weed skills | `skill-library` | `skills/skill-authoring/skill-library/SKILL.md` |
| Prune / consolidate / merge skill trees | `skill-lifecycle` | `skills/skill-authoring/skill-lifecycle/SKILL.md` |
| Generate AES-format HOW-TO reference files | `howto-generator` | `skills/aes-architecture/howto-generator/SKILL.md` |

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

The old `python3 skills/skill-authoring/scripts/cli.py <subcommand>` path
still works for one release: it prints a deprecation notice to stderr and
delegates to `aa skills` with identical output and exit codes.

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
reference is `skills/skill-authoring/_rules/skill-rules.md` (regenerate with
`aa skills rules --markdown`), and provenance is recorded in
`_rules/RULES.md`.

## Back-compat shims preserved

- `skills/skill-authoring/scripts/cli.py` — delegates to `aa skills`.
- `skills/skill-authoring/_rules/skill_rules.py` — re-exports the shared
  rule SSOT for in-pack imports.