<!-- Hand-written provenance. Not generated: `cli rules --markdown` emits
     skill-rules.md, and this file records where each rule came from. If a
     rule id below disagrees with _rules/skill_rules.py, the SSOT wins. -->

# RULES — provenance

Where each rule in `skill-rules.md` came from: the loader file the
constraint was first read from, or the failure mode it fixes. The
executable rules live in `_rules/skill_rules.py`; this file adds no
constraints of its own.

The 13 rules are the issue types `librarian.py validate` has emitted since
the skill-librarian was written (PR-2 lifted them into the SSOT verbatim,
so the validator's behavior is byte-identical). Provenance for each is
given in the order the doc renders them.

| Rule | Provenance |
|---|---|
| `name-mismatch` | `create-skills/SKILL.md` teaches that `name:` must equal the directory because loaders key discovery on the folder. The failure mode is the skill being silently unresolvable, which no other rule catches — the directory can be perfectly well-named while the frontmatter disagrees. |
| `name-format` | Stated in `create-skills/SKILL.md` and again in `create-skills/references/validation-criteria.md` (one of the seven duplicated copies of this rule, §2.3 P2), and enforced by `NAME_RE` in `_rules/skill_rules.py` (checked by `scripts/validate.py`; `skill-librarian/scripts/librarian.py` is the back-compat shim onto that checker). The 172-row catalog drift (§2.1 fact 2) is why the rule is checked by tooling rather than taught by prose: `skill-migration` was deleted while every prose copy of the rules stayed silent. |
| `description-present` | `create-skills/SKILL.md` (the minimal required frontmatter shape). A missing description leaves the skill unreachable in the listing — the failure mode is invisibility, not an error. |
| `description-characters` | `create-skills/SKILL.md`: Grok Build embeds the value verbatim inside `<skill description="...">`, so an unescaped `<`, `>`, or `"` breaks the embedding, not the YAML. |
| `description-length` | `create-skills/SKILL.md` and `validation-criteria.md` both stated the 1,024-char ceiling; it was still missed — `code-quality/configure-codacy` shipped a 1,242-char description, and `research/learn` an `invalid-description-characters` (§2.3 P2, §4). |
| `skill-md-nesting` | `create-skills/SKILL.md` structure section: nested `SKILL.md` files are rejected on upload. Checked per-directory because the outer file parses fine. |
| `skill-placement` | `create-skills/SKILL.md` (placement) and `skill-librarian/references/category-rules.md` (folder shape). A `SKILL.md` directly under a category is invisible to a loader that walks one level. |
| `category-depth` | `create-skills/SKILL.md` ("loaders walk one level") and `category-rules.md` ("do not create nested subcategories"). |
| `unique-skill-name` | No loader file states it; it is inferred from the loader keying on the folder; the failure mode it fixes — two folders answering to one name — is a real dispute the walk cannot resolve. |
| `unique-description` | Inferred from the same keying: two skills sharing one description collides on `discover` and produces identical rows in `CATALOG.md`. |
| `category-description-present` | `skill-librarian/references/category-rules.md` (DESCRIPTION.md section). |
| `category-description-nonempty` | `skill-librarian/references/category-rules.md`; the description helps the librarian decide where skills belong, so a file with no description is indistinguishable from no file. |
| `category-nonempty` | An empty category folder is dead structure the catalog still lists; no loader file states it as a rule. |

## Why so few citations

Citations are loader files we actually read the constraint from — this
file does not invent them. The two duplicate-name rules and the
empty-category rule constrain the loader's own behavior, which no skill
documented; they are recorded here as inferred rather than cited. Where a
rule had two restated copies (the `name:` rule had seven — §2.3 P2), PR-3
replaced the copies with a link to `skill-rules.md`; this file's citations
name the copies that existed and why eliminating them stopped the drift.

## PR-3 deduplication map

The restated rule copies PR-3 replaced with a link to `skill-rules.md`:

- `create-skills/SKILL.md` — frontmatter `name:`/`description:` constraints and placement
- `create-skills/references/validation-criteria.md` — the duplicated frontmatter/name/description checklist
- `skill-librarian/references/category-rules.md` — the category-shape and category-name rules
- `prune-skills/SKILL.md` — the merged-skill frontmatter shape
- `skill-manager/SKILL.md` — the name/category prose (the stale pack-layout table at `:38-55` is PR-6's to rewrite)
- `create-skills/references/creation-workflow.md` — the name alphabet in Step 1
- `skill-librarian/SKILL.md` — the category rules in the body

`_rules/skill_rules.py` is the executable home of every rule and the SSOT the checker (`scripts/validate.py`) reads; `skill-librarian/scripts/librarian.py` is only the back-compat shim onto the pack CLI.
