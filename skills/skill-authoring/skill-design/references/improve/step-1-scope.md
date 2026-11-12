# Improve — Step 1: Resolve scope

The `--improve` flag takes a skills path. Resolve it before editing:

- **Skill directory** — the path names `<category>/<skill>/` containing a `SKILL.md`. Improve that one skill.
- **Category directory** — the path names a category folder without its own `SKILL.md`. Default to improving every `SKILL.md` in that tree. Do not ask the user to pick one skill; the request targets the whole category.
- **Skills root** — the path is the `skills/` folder itself. Improve every skill in the tree.
- **Explicit skill list** — the user names two or more skill directories (by relative or absolute path) in one invocation. Improve every named skill, running the full audit-then-improve recipe on each in order; verify the whole set after all named skills are done, not one at a time. Naming several skills is not ambiguity — act on all of them without asking.

Do not prompt the user to disambiguate unless two or more distinct skills in the tree match the request equally well and acting on both would waste significant effort; in that case, name the two candidates and proceed with the more specific match. A category with exactly one skill is not ambiguity — improve that skill without asking.

## Embedded-catalog guard

Some skill trees are embedded into a compiled artifact (for example a Rust `include_str!` catalog constant counting on-disk skill files, guarded by a test that compares the constant to the disk state). Check for that guard before editing: read the constant and its test to learn exactly what is counted (skill folders vs individual files, which subtree), state the resulting count in the plan up front, and keep the constant and the tree consistent in the same change — a guard failure on its own blocks the whole run even when every skill edit is correct.

## Commands

- `sac read <name>` — read the target `SKILL.md` before editing so the edit preserves its intent.
- `sac lint --category <name>` — preview the target's lint issues scoped to its category before the edit; the lint gate runs again after.
- **Absolute path as argument**: when the user passes a full filesystem path (e.g. `/repo/skills/web-design`), resolve its last segment as the category name and scope `sac lint --category <name>` accordingly. The `sac` CLI does not accept a bare path — only the category name. Verify the path is a directory containing `SKILL.md` files (a category directory) before proceeding; a path pointing at a single skill's directory scopes the run to that one skill.

## Dry-run before `--apply` on mutation verbs

`sac move`, `sac archive`, and `sac create` are dry-run by default and write only with `--apply`. Before running one against the live repo skills tree:

1. Run the verb without `--apply` and read the `[DRY-RUN]` plan to confirm the source exists and the destination is where it should be.
2. `--apply` against the live tree moves real files under `skills/` and rebuilds `catalog.json`. After any exploratory or wrong `--apply` on the live tree, restore: `git restore -- skills/<moved-path>`, `rm -rf skills/<destination-dir>`, then `git restore skills/catalog.json`.
3. For behavior verification, prefer the in-process test harness over the live tree: `run_surface(crafted_tree(tmpdir), 'move', 'drafts/doc-drafts', 'notes')` from `modules/skills_design/tests/fixture_skills.py` drives `cmd_skills` against a `tmp_path` crafted pack — the live tree stays untouched.

Never `--apply` against the live repo to "test" a mutation verb unless the user explicitly asked for the mutation; test on fixtures, apply only on request.

## Completion

- The target skill set is resolved (one skill, a category tree, or the whole tree).
