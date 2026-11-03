# Audit

Mechanical audit for a SKILL.md — before publishing (after create/improve) or on demand (`--audit`). Design rules are Global Rules in `SKILL.md`; this file holds what they do not: the full key table, the validator's rule catalog, naming/description/content detail, the reference-pattern decision, the information-distribution test, and the checklists.

**Goal:** make the target skill(s) pass `aa skills lint` and the pre-publish checklist — fix structure, naming, frontmatter, and dangling references.

## Scope resolution

The audit auto-resolves its scope from the skills-path argument:

- **Single skill** — the path names one skill folder (`<category>/<skill>/`). Run the checklist below for that one `SKILL.md`; run `aa skills lint` scoped to it.
- **Pack / category** — the path names a category (`<category>/`) or the skills root. Run the single-skill checklist for every `SKILL.md` in the tree, and run `aa skills lint` over the whole tree — it covers the `unique-skill-name`, `unique-description`, `skill-placement`, `missing-category-description`, `empty-category-description`, and `empty-category` rules pack-wide. One pack-wide check the tool does not perform: no dangling cross-skill links.

When the path is ambiguous, default to the single-skill scope if it ends in a folder containing a `SKILL.md`, otherwise the pack scope.

## Frontmatter keys

Which keys are mandatory is a Global Rule; this table is the full key reference, including the optional ones.

| Field | Required | Notes |
| ----- | -------- | ----- |
| `name` | Yes | Validator rules `name-format`, `name-mismatch`. |
| `description` | Yes | Validator rules `description-*`. |
| `when-to-use` | Yes | Dedicated trigger phrases; Grok Build matches it together with `description`. |
| `argument-hint` | Yes | Slash-command autocomplete hint, e.g. `<command> [--flag]`. |
| `user-invocable` | Optional | Boolean, default `true`. `false` hides the skill from slash commands and the model's skill tool. |
| `disable-model-invocation` | Optional | Boolean, default `false`. `true` keeps the skill out of the model's listing; slash commands still run it. |
| `paths`, `model`, `effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata` | Optional | Grok Build controls. |
| anything else (`version`, `author`, `platforms`, ...) | Optional | Target-dependent; match the field set the destination validator enforces. |

## Validator catalog — what `aa skills lint` enforces

| Rule | Meaning |
| ---- | ------- |
| `name-mismatch` | Frontmatter `name` equals the skill directory name. |
| `name-format` (invalid-skill-name) | Skill names are lowercase letters, digits, and hyphens. |
| `description-present` (missing-description) | Every skill carries a description. |
| `description-characters` (invalid-description-characters) | Descriptions contain no `<`, `>`, or `"`. |
| `description-length` (description-too-long) | Descriptions are at most 1,024 characters. |
| `skill-md-nesting` (nested-skill-md) | A skill directory holds exactly one `SKILL.md`. |
| `skill-placement` (invalid-placement) | `SKILL.md` lives at `<category>/<skill>/SKILL.md`. |
| `too-deep` | `SKILL.md` is nested too deep without a `pack.toml` marker. |
| `unique-skill-name` (duplicate-skill-name) | Each skill name is used by one folder only. |
| `unique-description` (duplicate-description) | No two skills share one description. |
| `missing-category-description` | A category folder has no `DESCRIPTION.md`. |
| `empty-category-description` | A category `DESCRIPTION.md` has no description text. |
| `empty-category` | A category folder contains no skills. |

## Naming detail

- Gerund form preferred (`processing-pdfs`) over `pdf-processing`, when both are valid.
- Renaming a skill = rename the directory (`git mv`); the dangling-pointer sweep afterwards is owned by the Verify step of `SKILL.md`.

## Description detail

- Third person: "Extracts text from PDFs", never "I can help".
- Specific: "Helps with documents" fails — name the artifact and the action.
- Leftover trigger phrases go to `when-to-use:`, not into an ever-longer description (Global Rules: Frontmatter semantics).

## Content detail

- Concrete examples over abstract description; input/output pairs for style-dependent output.
- Defaults, not menus of alternatives.
- Scripts handle errors themselves, justify constants, list dependencies.
- Prefer referencing existing CLI tools over writing custom scripts.
- MCP tools named fully qualified (`ServerName:tool_name`).
- Forward slashes in paths (`scripts/helper.py`); no time-sensitive content in the body.

## Pre-publish checklist

- [ ] `aa skills read` — read back the target `SKILL.md` to confirm frontmatter and body landed correctly.
- [ ] `aa skills lint` passes (catalog above).
- [ ] Frontmatter satisfies the Global Rules bullets: mandatory keys, Frontmatter semantics, YAML hygiene, parser limits.
- [ ] Body within ~100–200 lines; overflow moved into `references/`; every reference, whatever its depth, is linked from `SKILL.md` (Global Rules: Structure).
- [ ] Every sibling mention and cross-skill link names a skill that exists in the tree (Global Rules: dangling refs).
- [ ] Content detail section above satisfied.

## Category-placement audit

Use this when skills may be in the wrong category.

1. Run:

```bash
aa skills lint
```

2. Read `CATALOG.md`.
3. Read the `DESCRIPTION.md` file for each category involved.
4. Identify skills whose name or description conflicts with their current category.
5. If duplicate or obsolete skills need pruning, route to `skill-auditor --prune` — this mode only decides category placement.
6. If no category fits, create one:

```bash
aa skills create category CATEGORY_NAME --description "CATEGORY_DESCRIPTION" --apply
```

7. Move each misplaced skill:

```bash
aa skills move CATEGORY/SKILL TARGET_CATEGORY
```

8. Rebuild the catalog:

```bash
aa skills catalog
```

9. Verify the moved skills appear under the correct category.

### Pitfalls

- **Empty source category**: moving the last skill out of a category leaves it empty, and `aa skills lint` flags `empty-category`. Delete the empty `DESCRIPTION.md` and category directory, or retire the category row in `CATALOG.md`.
- **Dangling paths**: after a move, grep the pack for the old `category/skill-name` path and update any hardcoded references.

### Completion

- Every misplaced skill identified in steps 4–7 has been moved.
- Duplicates and obsolete skills have been routed to `skill-auditor --prune`.
- The catalog was rebuilt after moves.
- `aa skills lint` reports no placement issues.

## Information distribution

Before editing any fact, route it with the test below. A fact that has more than one home is a bug; one home per fact (Global Rules). This is the check that catches a definition file that should have been split into the Global Rules + step files that use it.

### The test

For each fact, ask one question: **how many steps read this fact during a single invocation?**

- **More than one step (or all steps)** → `SKILL.md` Global Rules. Cross-step policy, signal definitions, invariants, record formats.
- **Exactly one step** → that step's reference file. Commands, field shapes, per-action rules, stop conditions, worked examples.
- **Neither — the fact is a shared definition used by several pipeline skills** (the trace pipeline's `signals` definitions, `report-format` shapes, …) → it is a shared reference, not owned by any one step. In this pack the shared definition is inlined into the consuming skill's step file (as in the trace-pipeline skill `skill-traces`, which carries one `step-3-read-report.md`, `step-4-apply.md`, and `step-5-verify.md` covering all three modes); the standalone shared file is deleted, not kept. A standalone `references/<name>.md` linked from several consumers is legitimate only when the fact genuinely has no per-skill step home — which in this pack means a new shared pipeline has not yet been created.

### Rules

- **Learned mistake (do not repeat).** When inlining a shared definition into a consuming skill's step file, the step file that gains the content must name the file it absorbed by reference, and the standalone file must be deleted in the same edit. The mistake that produced this rule: the trace skill's `signals.md`, `report-format.md`, and `apply-rules.md` were inlined into `step-1`, `step-3`, and `step-4` respectively, but the three standalone files were left on disk and still linked from `SKILL.md` — creating second copies. The check that catches it: after inlining, grep the skill's `SKILL.md` and step files for the deleted filename; every hit is a dangling link and a second copy, and the edit is incomplete until both are removed.
- A Global Rules bullet that fully defines a signal, action type, or invariant is the home for it; a step file that repeats that definition in full is the second copy. Point at the bullet, do not restate it.
- A step file may reference the Global Rules bullet by name; it does not restate the bullet's content.
- The shared-reference case (third rule above) is the only situation where a non-step `references/<name>.md` is legitimate in a Pattern B pipeline; name it in the `SKILL.md` Routing table and link it from the step that consumes it.

## Choosing the reference pattern

Run this decision **before** restructuring the `references/` folder. The pattern must match the skill's shape — never match by convention.

### Pattern shapes (file trees)

**Pattern A — one file per mode:**

```
references/creation.md
references/audit.md
references/improve.md
```

**Pattern B — numbered step files (single ordered pipeline):**

```
references/step-0-resume-or-price.md
references/step-1-collect.md
references/step-2-launch.md
references/step-3-read-report.md
references/step-4-apply.md
references/step-5-verify.md
```

**Pattern C — hybrid: per-mode subdirs of numbered steps:**

```
references/create/step-0-gather.md
references/create/step-1-draft.md
references/create/step-2-write.md
references/create/step-3-verify.md
references/audit/step-0-frontmatter.md
references/audit/step-1-structure.md
```

Worked example (Pattern B, `skill-traces` — a single pipeline with mode flags, so it is B, not A):

```
skill-traces/
├── SKILL.md
└── references/
    ├── step-0-resume-or-price.md
    ├── step-1-collect.md
    ├── step-2-launch.md
    ├── step-3-read-report.md
    ├── step-4-apply.md
    └── step-5-verify.md
```

### Decision steps

The pattern follows the skill's shape, not the tree it currently has. Run Step 1 and Step 2 **before** looking at the existing `references/` layout; if the resulting pattern differs from what is on disk, restructure.

#### Step 1: Does the skill have one ordered pipeline?

Ask: will the agent always execute all steps in sequence, with run state (attempt counters, hypotheses, repro commands, etc.) flowing from one step to the next?

Answer this question from the **Routing table** in `SKILL.md` (the Step rows and whether each row's output feeds the next), not from the filenames under `references/`. Definition files (signal definitions, report-format shapes, …) do not make a skill mode-based; they are inputs a pipeline step reads. If the pipeline is one ordered sequence, the answer is **Yes** even if the current tree is flat Pattern A.

- **Yes** → **Pattern B**: numbered `references/step-<N>-<name>.md` files in execution order. Numbers encode order; sub-variants (`step-<N>a`, `step-<N>b`) branch by a runtime parameter.
  - Examples in this pack: `systematic-debugging`, `implement`, `skill-traces`.
- **No** → continue to Step 2.

#### Step 2: Does the skill have multiple independent modes?

Ask: does the agent pick exactly one mode per invocation, and no shared state flows between modes?

- **Yes** → check each mode file's size:
  - Every mode file is **under ~100 lines and under 5 ordered steps** → **Pattern A**: `references/<mode>.md`, one file per mode, `SKILL.md` routes directly to it.
  - At least one mode file exceeds ~100 lines or has more than 5 ordered steps → **Pattern C** for that mode only: `references/<mode>/step-<N>-<name>.md`. Keep the other modes as Pattern A single files.
- **No** → the skill is not mode-based; it is single-pipeline → return to Step 1 and apply Pattern B.

#### Step 3: What goes in the body vs a reference (placement decision)

Run this before deciding where each fact lands. The test is the Information distribution test above: **how many steps read this fact during a single invocation?**

- **More than one step (or all steps) → `SKILL.md` Global Rules**: cross-step policy (scope, consent, validation), signal definitions, invariants, record formats.
- **Exactly one step → that step's reference file**: commands and flags with exact syntax, outputs and their shape, the step's stop conditions and failure handling, worked examples for that step's shape.
- **Shared definition used by several pipeline skills → inline it into the consuming skill's step file** (as in the trace-pipeline skill `skill-traces`); it is not owned by any one skill's step file. A standalone shared `references/<name>.md` is kept only when a consuming skill has not yet been restructured to Pattern B step files — the moment it does, inline and delete the shared file.

The two trigger fields (`description:`, `when-to-use:`) follow their own budget rule (Global Rules: budget for permanent cost) — they are not "body". Move anything task-conditional out of the body into a reference or a step.

### Placement rules (apply after choosing)

- A fact used across multiple steps belongs in the target skill's `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to Pattern C, keep the other modes as Pattern A single files until they also need splitting.
- Never renumber existing step files for the sake of consistency — the pattern follows the skill's shape.
- Renaming a reference file that other files link to requires a grep sweep of the whole pack for the old name (Global Rules: dangling refs rot fast).
