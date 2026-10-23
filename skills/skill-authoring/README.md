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

The canonical entrypoint is the script package:

```bash
python3 skills/skill-authoring/scripts/cli.py <subcommand>
```

Read-only subcommands (`validate`, `catalog --check`, `discover`, `weed`,
`rules`, `merge-plan`) run immediately. Mutating subcommands (`repair`,
`move`, `archive`, `new-category`) default to dry-run — pass `--apply` to
execute. The old `skill-library/scripts/librarian.py` shim keeps working and
delegates to the same CLI.
CI runs `validate` and `catalog --check` on every pull request (`.github/workflows/ci.yml`); run both locally before pushing.

## Catalog

`CATALOG.md` at the skills root is the master index. Rebuild with:

```bash
python3 skills/skill-authoring/scripts/cli.py catalog
```

`catalog --check` is the drift gate: it regenerates to a temp file and fails
(~exit 3) when the tracked artifact does not match the live tree.

## Rules

The single source of truth for what a valid skill is lives in
`skills/skill-authoring/_rules/skill-rules.md` (generated from
`_rules/skill_rules.py`).

## Back-compat shims preserved

- `skill-library/scripts/librarian.py` — delegates to `scripts/cli.py` (the
  old `skill-librarian/scripts/librarian.py` path still works).