---
name: skill-design
description: Author, validate, and improve agent skills — create skill, write skill, improve skill, validate skill, audit skill, check skill, or scaffold a SKILL.md. Covers frontmatter, naming, structure, and body-versus-reference split. Use when the user asks what each skill in a pack does, requests argument hints for every skill in a directory, or checks that a skill pack's references are current.
when-to-use: Use when creating, writing, structuring, improving, validating, or auditing a skill / SKILL.md, deciding what belongs in the body versus a references/ file, explaining a skill pack's features and usage to the user, or generating argument hints for skills in a tree.
argument-hint: "<create | improve | validate | audit | check | explain | hints> [skill-dir]"
---

# skill-design

Author, validate, and improve SKILL.md files. One skill covers the full lifecycle:
design principles, the interactive creation workflow, and validation rules.

## When to Use

- Asked to create, write, structure, improve, validate, or audit a skill / `SKILL.md`.
- Deciding what goes in the body versus a `references/` file, or how to word a `description:`.
- Don't use for: discovering or reading installed skills (`skill-library`), consolidating
  a skill tree (`skill-lifecycle`)

## Routing

- **`skill-library`** — listing and reading installed skills (`aa skills list/show`).
- **`skill-lifecycle`** — consolidating or de-duplicating a skill tree.
- **`skill-library`** — cataloging, repairing, and weeding the library.

Frontmatter, naming, description, and category-shape constraints are not restated here:
the executable rules and their exact messages live in
[`_rules/skill-rules.md`](../../../modules/skills/_rules/skill-rules.md), generated from
`_rules/skill_rules.py`. This skill teaches how to author, not what the checker enforces.

## Design principles

Apply these when writing a skill from scratch and when editing one. Re-check your diff against
each principle mechanically, not from memory — but never make refactors the user did not ask
for; complete the request first, then report the opportunity.

- **One home per fact.** Keep each rule, value, or list in a single authoritative place.
  When editing and you find an existing copy, make the requested change and report the
  duplication instead of silently rewriting the skill.
- **Avoid no-op statements.** If a sentence does not change behavior, delete it. Guardrails
  that restate the new instruction ("do not do X" after "do Y" replaced X) are no-ops too.
- **Solve the class of problem, not the instance.** Fix the bad output where the fact is
  owned rather than adding a downstream check that catches one symptom. Generalize along
  predictable dimensions, and check every generalization against at least two instances.
- **Set degrees of freedom.** Match specificity to task fragility: high freedom (text steps)
  for context-dependent work, medium (parameterized scripts) when a preferred pattern exists,
  low (exact commands) for fragile, strict-sequence operations.
- **Budget for permanent cost.** The `description:` is injected into the skill list every
  session; the body loads per skill use; `references/*.md` cost nothing until opened. Move
  anything task-conditional out of the body.
- **Consistent terminology.** One term per concept, no synonyms. Model-agnostic wording:
  don't over-explain for strong models or under-specify for light ones.
- **Dangling refs rot fast.** Sibling references (`related_skills:`, prose mentions,
  cross-skill links) are not existence-checked — when editing, resolve every one against
  the tree (`find skills -maxdepth 2 -type d -name <sibling>`) and remove refs to skills
  that don't exist.

## Frontmatter

In our workflow, a skill's frontmatter carries four keys: `name:`,
`description:`, `when-to-use:`, and `argument-hint:`. All four are mandatory.
Every other key (`user-invocable`, `disable-model-invocation`, `paths`, `model`,
`effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata`,
`author`, `platforms`, `version`, ...) is optional and target-dependent.

Mandatory shape:

```yaml
---
name: your-skill-name
description: What it does and when to use it. Third person. Include trigger terms.
when-to-use: "Use when <trigger phrases for auto-invocation>."
argument-hint: "<arg> [--flag] <other-arg>"
---
```

Rules:

- `name:` matches the directory; satisfies the `name-format` and
  `name-mismatch` rules in
  [`_rules/skill-rules.md`](../../../modules/skills/_rules/skill-rules.md).
- `description:` satisfies the `description-*` rules; carries the WHAT +
  WHEN + trigger terms, so auto-invocation works even without
  `when-to-use:`.
- `when-to-use:` holds leftover trigger phrases that would bloat the
  description; kebab-case key, `when_to_use` is the only accepted alias.
- `argument-hint:` shows in slash-command autocomplete; keep it under one
  line, use `[]` for optionals, `|` for choices, and angle-bracket
  placeholders for required args (see sibling skills `review`, `design`,
  `pr-babysit`).

Survey 2-3 sibling skills in the target tree first and match the field set
that tree's validator enforces — hosted upload targets reject keys outside
their allowlist; the Grok Build parser table below lists every optional key
it accepts.

### Grok Build keys

Grok Build parses exactly these keys; unknown keys load silently and do nothing:

| Key | Default | Effect |
| --- | --- | --- |
| `when-to-use` (or `when_to_use`) | — | Extra trigger phrases matched against the prompt alongside `description`. |
| `user-invocable` | `true` | `false` hides the skill from slash commands and from the model's skill tool. |
| `disable-model-invocation` | `false` | `true` removes the skill from the model's listing; slash commands still run it. |
| `argument-hint` | — | Hint shown in slash-command autocomplete (`commit message`). |
| `paths` | — | Gitignore-style globs; the skill is held out of the listing until a touched file matches, then stays active for the session (`/clear` re-hides it). |
| `model` / `effort` | — | Model and reasoning-effort override when the skill runs. |
| `allowed-tools` | — | Displayed in `/extensions`; not enforced at runtime. |
| `license` / `compatibility` | — | Informational. |
| `metadata.author` / `metadata.short-description` | — | Promoted for display; other `metadata` values must be strings — lists are skipped. |
| `origin` | — | Provenance slug `[a-z0-9-]`, max 32 chars, naming the tool that wrote the skill. |

Parser limits: `name` ≤ 64 chars; `description` and `when-to-use` ≤ 1,024 chars (longer
values truncate). Top-level `version:`, `triggers:`, and `entry_points:` are **not parsed**
— trigger phrases belong in `description:` or `when-to-use:`. This file's own top-level
`triggers:` block was removed for that reason; its terms moved into the `description:` and
`when-to-use:` above.

### YAML hygiene

- Quote any value containing `: ` or indicator characters (`{ } [ ] * & # ! | > % @` and
  backticks); a plain `description: Deploy: prod` fails YAML and the skill falls back to a
  body-derived description.
- Never indent a field under a previous field's value. One accidentally nested line
  invalidates the entire frontmatter; the parser recovers only `name`, `description`, and
  `when-to-use` from the broken block — every other key is lost.
- Multi-word keys are kebab-case (`when-to-use`, `allowed-tools`, `argument-hint`);
  single-word keys are written as-is (`model`, `effort`).

## Structure

One `SKILL.md` per skill, at the skill root. Nested `SKILL.md` files are rejected on upload.

```text
my-skill/
├── SKILL.md              # Overview + links (target ~100-200 lines)
├── references/           # One level deep only
│   ├── scenario-a.md
│   └── scenario-b.md
└── scripts/
    └── helper.py         # Executed, not loaded into context
```

- Keep the body a table of contents; push detail into `references/*.md`, never nested deeper.
- End steps with checkable completion criteria ("every modified file accounted for" beats
  "summarize changes"). Use checkbox lists for multi-step workflows with a feedback loop.
- Prefer defaults over menus ("use pdfplumber", not a list of four PDF libraries).
- Examples beat descriptions for style-dependent output. Forward slashes only in paths.
- No time-sensitive content in the main body; say "current method" and collapse old patterns.
- Ship non-trivial logic as `scripts/<file>` and reference it by path — don't expect the model
  to re-write a parser each call. Handle errors in the script, not in prose. Justify constants
  (`TIMEOUT = 30  # HTTP requests complete within 30s`).

## Workflows

- **Creating a skill interactively** → `references/creation-workflow.md` (gather requirements,
  draft the description, scaffold the directory, verify).
- **Validating or auditing a skill** → `references/validation-criteria.md` (frontmatter, naming,
  structure, content rules, pre-publish checklist).
- **Refining frontmatter in place** → follow the Frontmatter section above, then run
  `aa skills validate`. When the user restates which keys are mandatory, the four mandatory
  keys are `name`, `description`, `when-to-use`, and `argument-hint`; every other key is
  optional and target-dependent.

## Explain a skill or pack

When the user asks what a skill does, what a pack covers, or how to use it:

- Read the target `SKILL.md` frontmatter and body; read each `references/*.md` file it
  links to.
- Summarize: purpose, when to invoke it (from `description:` and `when-to-use:`),
  argument/flag surface (from `argument-hint:` and the body), and one concrete example of
  invoking it.
- For a whole pack (a category folder with several skill subfolders), cover each skill in
  the same shape and note which sibling skill handles a nearby job.

## Generate argument hints for a tree

When the user asks for `argument-hint:` values across several skills:

- [ ] List every `SKILL.md` under the given directory (skip `references/` and `scripts/`).
- [ ] For each skill, derive the hint from its `description:`, `when-to-use:`, and body
      workflow commands: `[]` for optional groups, `|` for alternatives, `<...>` for
      required positional args.
- [ ] When a flag is a counterpart to another flag (for example `--auto` as the
      unattended apply mode opposite `--dry-run`), say so in one line in the hint or in
      the flag's body description so the two read as a pair.
- [ ] Show the proposed hint lines to the user before writing.
- [ ] Apply each hint to its `SKILL.md` `argument-hint:` line, keeping the value under one
      line.
- [ ] Run `aa skills validate` to confirm no rule violations.

## Scripts and MCP

- State intent: "run `scripts/x.py`" (execute) vs "see `scripts/x.py`" (read).
- List dependencies explicitly before usage.
- Use fully qualified MCP tool names: `ServerName:tool_name`.

## Creating a new skill: which writer

- **`skill_manage(action=create)`** — the safe path, but it enforces a strict ~60-char
  limit on the `description:` line (the skill index clips anything longer) and rolls back
  the whole batch on any violation. Draft the description first and count it; if it will
  exceed ~60 chars, don't fight the validator loop.
- **Write the `SKILL.md` file directly** (`write_file`) to `<category>/<skill>/SKILL.md`,
  then run `aa skills catalog` to register it. Use this when the description is longer
  than the index budget, when you're building a richer multi-file skill, or when
  `create` keeps rejecting frontmatter. After writing, run `aa skills validate` to confirm
  the file parses and naming/placement rules hold.

Both paths then go to the same verification below. "Never permanently delete skills" and
"one home per fact" apply regardless of which writer you used.

## Verification

For every skill you touch:

- A search across the skill directory shows no second authoritative copy of any fact you added.
- No added sentence is a no-op the updated instruction already covers.
- Every generalization was checked against at least two concrete instances.
- `references/` links resolve, frontmatter parses, `name:` matches the directory.
