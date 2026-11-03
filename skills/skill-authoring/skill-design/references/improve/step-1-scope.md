# Improve — Step 1: Resolve scope

The `--improve` flag takes a single skills path. Resolve it before editing:

- **Skill directory** — the path names `<category>/<skill>/` containing a `SKILL.md`. Improve that one skill.
- **Category directory** — the path names a category folder without its own `SKILL.md`. Default to improving every `SKILL.md` in that tree. Do not ask the user to pick one skill; the request targets the whole category.
- **Skills root** — the path is the `skills/` folder itself. Improve every skill in the tree.

Do not prompt the user to disambiguate unless two or more distinct skills in the tree match the request equally well and acting on both would waste significant effort; in that case, name the two candidates and proceed with the more specific match. A category with exactly one skill is not ambiguity — improve that skill without asking.

## Commands

- `aa skills read <name>` — read the target `SKILL.md` before editing so the edit preserves its intent.
- `aa skills lint --category <name>` — preview the target's lint issues scoped to its category before the edit; the lint gate runs again after.

## Completion

- The target skill set is resolved (one skill, a category tree, or the whole tree).
