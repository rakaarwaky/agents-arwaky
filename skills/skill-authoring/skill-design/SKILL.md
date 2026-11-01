---
name: skill-design
description: Author, validate, and improve agent skills — create skill, write skill, improve skill, validate skill, audit skill, check skill, or scaffold a SKILL.md. Covers frontmatter, naming, structure, and body-versus-reference split. Use when the user asks what each skill in a pack does, requests argument hints for every skill in a directory, checks that a skill pack's references are current, or needs a skill created for an unloaded slash command (cli-commands, config-system, doc-rules, external-lint, git-hooks).
when-to-use: Use when creating, writing, structuring, improving, validating, or auditing a skill / SKILL.md, deciding what belongs in the body versus a references/ file, explaining a skill pack's features and usage to the user, or generating argument hints for skills in a tree. Also use when a slash command has no loaded skill and a new skill needs to be authored for it.
argument-hint: "<create | improve | validate | audit | check | explain | hints> [skill-dir]"
---

# Skill Design

You author, validate, and improve SKILL.md files. One skill covers the full lifecycle: design principles, the interactive creation workflow, and validation rules. Every editable rule has exactly one home (a reference file or the Global Rules list below); the body of this skill routes to the right reference and never restates it.

## Execution Flow

1. **Identify the task**: create, improve, validate/audit, explain, or generate argument hints — read `description:` / `when-to-use:` and the argument to pick the mode.
2. **Load the applicable reference**: open only the reference file(s) that the mode names (see Run Steps below); their rules are the executable logic for that mode.
3. **Apply the Global Rules below** throughout: single home per fact, budget for permanent cost, dangling-reference check, one home for each fact you add.
4. **Execute**: follow the reference's steps (gather → draft → scaffold → verify for create; checklist for validate; etc.).
5. **Verify**: after every create/improve, run `aa skills validate`; after every merge or move in a tree, grep the pack for the changed name and fix dangling pointers.
6. **Report**: state what changed, how it was verified, and any duplication you noticed but did not fix (per the one-home rule, you report rather than silently rewrite).

## Global Rules (SSOT)

Rules that apply to every mode. Reference files cite these; they never restate them.

- **One home per fact.** Each rule, value, or list lives in a single authoritative place — a reference file or this list. When editing and you find an existing copy elsewhere, make the requested change and report the duplication instead of silently rewriting the skill.
- **Avoid no-op statements.** If a sentence does not change behavior, delete it. Guardrails that restate the new instruction ("do not do X" after "do Y" replaced X) are no-ops too.
- **Solve the class of problem, not the instance.** Fix the bad output where the fact is owned rather than adding a downstream check that catches one symptom. Generalize along predictable dimensions, and check every generalization against at least two instances.
- **Set degrees of freedom.** Match specificity to task fragility: high freedom (text steps) for context-dependent work, medium (parameterized scripts) when a preferred pattern exists, low (exact commands) for fragile, strict-sequence operations.
- **Budget for permanent cost.** The `description:` is injected into the skill list every session; the body loads per skill use; `references/*.md` cost nothing until opened. Move anything task-conditional out of the body.
- **Consistent terminology.** One term per concept, no synonyms. Model-agnostic wording: don't over-explain for strong models or under-specify for light ones.
- **Dangling refs rot fast.** Sibling references (`related_skills:`, prose mentions, cross-skill links) are not existence-checked — when editing, resolve every one against the tree (`find skills -maxdepth 2 -type d -name <sibling>`) and remove refs to skills that don't exist.
- **Mandatory frontmatter.** Four keys are mandatory: `name:`, `description:`, `when-to-use:`, `argument-hint:`. All other keys (`user-invocable`, `disable-model-invocation`, `paths`, `model`, `effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata`, `version`, ...) are optional and target-dependent. `name:` matches the directory; `description:` carries WHAT + WHEN + trigger terms.
- **YAML hygiene.** Quote any value containing `: ` or indicator characters; never indent a field under a previous field's value (one accidentally nested line invalidates the entire frontmatter — only `name`, `description`, `when-to-use` survive recovery). Multi-word keys are kebab-case.
- **Grok Build parser limits.** `name` ≤ 64 chars; `description` and `when-to-use` ≤ 1,024 chars. Top-level `version:`, `triggers:`, and `entry_points:` are not parsed — trigger phrases belong in `description:` or `when-to-use:`.
- **Structure.** One `SKILL.md` per skill at the skill root; nested `SKILL.md` files are rejected. Keep the body a table of contents (~100–200 lines); push detail into `references/*.md` (subfolders only when the set is large). Every reference, whatever its depth, links directly from `SKILL.md`. End steps with checkable completion criteria. Prefer defaults over menus; examples beat descriptions; ship non-trivial logic as `scripts/<file>` referenced by path.
- **Validation rules** (enforced by `aa skills validate`): name-mismatch — Frontmatter name equals skill directory name; name-format — Skill names are lowercase letters, digits, and hyphens; description-present — Every skill carries a description; description-characters — Descriptions contain no <, >, or "; description-length — Descriptions are at most 1024 characters; skill-md-nesting — A skill directory holds exactly one SKILL.md; skill-placement — SKILL.md lives at <category>/<skill>/SKILL.md; unique-skill-name — Each skill name is used by one folder only; unique-description — No two skills share one description.

## Run Steps

Each reference is mode-scoped and contains the executable steps for that mode. The Global Rules above apply throughout; do not restate them in a reference.

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Create | [`references/creation-workflow.md`](references/creation-workflow.md) | Interactive workflow: gather requirements, draft the description, scaffold the directory, verify. |
| Validate / audit | [`references/validation-criteria.md`](references/validation-criteria.md) | Mechanical checklist: frontmatter, naming, structure, content rules, pre-publish checklist. |
| Explain / hints / writer choice / verify | [`references/authoring-workflows.md`](references/authoring-workflows.md) | Per-mode recipes: explain a skill or pack, generate argument hints for a tree, choose which writer to use, verify a touched skill. |
| Reference patterns | [`references/reference-guide.md`](references/reference-guide.md) | Decision guide: when to use mode-based single files vs sequential `step-N-name.md` vs hybrid `references/<workflow>/step-N-name.md`. |
