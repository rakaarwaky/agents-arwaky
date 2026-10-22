---
name: create-skills
description: Author, validate, and improve agent skills. Use when creating a skill, writing or auditing a SKILL.md, or deciding what belongs in the body versus a reference file.
metadata:
  tags:
    - skills
    - authoring
    - creation
    - validation
    - design
  related_skills:
    - skill-manager
    - skill-migration
    - prune-skills
    - howto-generator
triggers:
  - create skill
  - write skill
  - improve skill
  - validate skill
  - audit skill
  - check skill
---

# Create Skills

Author, validate, and improve SKILL.md files. One skill covers the full lifecycle:
design principles, the interactive creation workflow, and validation rules.

## When to Use

- Asked to create, write, structure, improve, validate, or audit a skill / `SKILL.md`.
- Deciding what goes in the body versus a `references/` file, or how to word a `description:`.
- Don't use for: discovering or reading installed skills (`skill-manager`), porting a pack
  from another harness (`skill-migration`), consolidating a skill tree (`prune-skills`), or
  authoring a skill committed to the hermes-agent repo (`hermes-agent-skill-authoring`).

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

## Frontmatter

Minimal required shape for most harnesses:

```yaml
---
name: your-skill-name
description: What it does and when to use it. Third person. Include trigger terms.
---
```

Survey 2-3 sibling skills in the target tree first and match the field set that tree's
validator enforces — hosted upload targets reject keys outside their allowlist; harnesses
that parse extra keys are listed below.

- **`name:`** Max 64 chars; lowercase `a-z`, `0-9`, `-` only; no leading/trailing hyphen,
  no `--`, no XML tags, no reserved words. **Must equal the directory name exactly** —
  loaders key discovery on the folder, so a mismatch means rejected or silently unresolvable.
  Renaming means `git mv` the directory and grepping for inbound mentions, not editing one field.
  Grok Build normalizes names anyway (any char outside `a-z0-9-` becomes `-`, `--` collapses,
  leading/trailing `-` trimmed) and re-keys colliding same-scope skills to their directory
  basename, so keep `name` equal to the directory to survive collisions intact.
- **`description:`** Max 1,024 chars (some targets: 60). Third person: "Extracts text from
  PDFs". Includes WHAT + WHEN + trigger terms. No `<`, `>`, or `"` anywhere — Grok Build
  embeds the value verbatim inside `<skill description="...">`. Specific — "Helps with
  documents" and "Processes data" trigger nothing.
- **Placement:** `<skills-root>/<category>/<skill>/SKILL.md`. Loaders walk one level, so a
  skill nested deeper or sitting at the tree root is invisible rather than broken-looking.

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
— trigger phrases belong in `description:` or `when-to-use:`.

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

## Scripts and MCP

- State intent: "run `scripts/x.py`" (execute) vs "see `scripts/x.py`" (read).
- List dependencies explicitly before usage.
- Use fully qualified MCP tool names: `ServerName:tool_name`.

## Verification

For every skill you touch:

- A search across the skill directory shows no second authoritative copy of any fact you added.
- No added sentence is a no-op the updated instruction already covers.
- Every generalization was checked against at least two concrete instances.
- `references/` links resolve, frontmatter parses, `name:` matches the directory.
