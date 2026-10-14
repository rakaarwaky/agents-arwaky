---
name: prune-skills
description: Prunes and consolidates SKILL.md collections — deduplicates overlapping skills into one folder with one SKILL.md, or keeps one folder with a references/ subfolder for complex variants. Use when cleaning up, auditing, or merging agent skill directories.
metadata:
  tags:
    - skill
    - pruning
    - deduplication
    - consolidation
    - skill-cleanup
    - agent-skills
  related_skills:
    - author-skill-md
    - skill-manager
    - skill-design-principles
    - cleanup-consolidate
  triggers:
    - prune skills
    - clean up skills
    - consolidate skills
    - merge duplicate skills
    - audit skill directory
    - skill cleanup
    - deduplicate skills
    - collapse skill folders
---

# prune-skills

Prunes and consolidates an agent **skill directory** (a collection of `SKILL.md` folders). It finds
skills that overlap semantically and collapses them: two skills covering the same job become one
folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with
one `SKILL.md` plus a `references/` subfolder, one file per scenario. Modeled on
`code-quality/cleanup-consolidate` (two-phase: remove duplicates, then consolidate variants).

**Scope:** skill directories only — `SKILL.md` files, `references/`, `scripts/`, and category
`DESCRIPTION.md` files. Never touch non-skill content. This is the skill-folder analog of dead-code
removal plus consolidation: Phase 1 removes true duplicates, Phase 2 merges overlapping variants.

## Path Handling

- **Default audit root:** `/home/raka/agents-arwaky/skills` (the repo's skill tree).
- **User-supplied path:** if the user names a directory, audit that directory instead. Resolve it
  before starting and confirm it is a skill directory (contains one or more folders with a
  `SKILL.md`). If it contains no `SKILL.md` subfolders, stop and say the path is not a skill tree.
- A skill folder = `<dir>/<name>/SKILL.md`, optionally with `references/` and `scripts/`
  subfolders. Category folders (e.g. `code-quality/`, `devops/`) hold many skill folders plus a
  `DESCRIPTION.md`.

## Two-Phase Approach

**CRITICAL:** Phase 1 removes duplicates. Phase 2 consolidates remaining variants. Never skip
Phase 1 — merging skills that are already true duplicates is wasted effort.

### Phase 1 — Remove true duplicates

Two skills are duplicates when their scope, procedures, and completion criteria are equivalent and
one adds no scenario the other covers.

- **Same folder name, different trees** — provisioned copies under `.agents/skills/` or a
  harness home that mirror this repo's skill: keep the repo source, note the copy; never edit the
  copy (copies are provisioned artifacts).
- **Byte-identical or near-identical bodies** — merge into one; keep the more complete body, drop
  the rest.
- **Same `name:` in frontmatter appearing in two folders** — one is stale; keep the more
  complete, delete the other.

Before deleting anything, git snapshot the tree (`git add -A && git commit -m "snapshot: before
prune-skills"`, or `git stash` if the tree is dirty for other reasons).

### Phase 2 — Consolidate overlapping variants

Skills are variants when they share a domain but each covers a distinct scenario.

| Input | Output |
|---|---|
| 2+ skills with the same job and overlapping scenarios | **one folder, one `SKILL.md`** — merge bodies, deduplicate rules, union the trigger terms |
| Merged skill now has complex, distinct sub-scenarios | **one folder, one `SKILL.md`, plus `references/`** — `SKILL.md` keeps the shared rules and a routing table; each sub-scenario becomes `references/<scenario>.md`, one level deep |
| Skills that are genuinely different jobs | leave both alone; note in the report why they were not merged |

A merged `SKILL.md` follows `author-skill-md` conventions: frontmatter with `name`,
`description` (third person, includes trigger terms), `metadata.tags`, `related_skills`,
`triggers`; body as a table of contents that links one level deep into `references/`.

## Workflow

Task Progress:

- [ ] Step 1: Confirm audit root (default `/home/raka/agents-arwaky/skills` or the user path).
- [ ] Step 2: Inventory — list every skill folder, read each `SKILL.md` frontmatter and body.
- [ ] Step 3: Group — cluster skills by semantic scope using `description` and trigger terms,
      then verify clusters against body content (two descriptions that rhyme can be different jobs).
- [ ] Step 4: Classify each cluster — duplicate (identical scope) vs variant (same domain,
      distinct scenarios) vs separate jobs.
- [ ] Step 5: Snapshot the tree in git.
- [ ] Step 6: Execute merges per the Phase 2 table. When merging, delete the redundant folders
      (keep one canonical folder name, preferring the existing skill whose `name:` in frontmatter
      matches the surviving scope).
- [ ] Step 7: Update the category `DESCRIPTION.md` if a folder was removed or renamed.
- [ ] Step 8: Verify — every remaining `SKILL.md` parses as valid frontmatter, all `references/`
      links resolve, no two skills share a `name:`.
- [ ] Step 9: Report — see Report format.

## Merge Rules

- **Name survival** — the surviving skill keeps the `name:` that best matches the merged scope;
  if neither matches, pick the more specific one.
- **Frontmatter union** — merge `tags` and `triggers` as unions, de-duplicated; merge
  `related_skills` and drop entries pointing at skills that no longer exist.
- **Body merge** — shared rules go in the `SKILL.md` body exactly once. Scenario-specific rules
  move to `references/<scenario>.md`. Never restate a rule that already exists in a reference.
- **Scripts** — keep `scripts/` of the surviving skill; move or re-link scripts of dropped skills
  only if the surviving skill's scenario needs them.
- **DESCRIPTION.md** — the category description stays one line; update it only if the category's
  skill count changed in a way that breaks the description.

## Report Format

```text
prune-skills report — <audit root>

MERGED:
- <surviving folder>  <-  <dropped folder(s)>
    reason: <duplicate scope / shared domain>
    action:  <body merged | references/ created for scenarios: a, b | duplicates dropped>

KEPT SEPARATE:
- <skill A> vs <skill B>  —  reason: <distinct jobs, e.g. different completion criteria>

DELETED:
- <folder>  —  reason: <true duplicate of <survivor>, stale name collision, ...>

VERIFY:
- N skills remain, 0 shared names, all reference links resolve, all frontmatter parses
```

## Common Mistakes

- **Merging across domains.** Two skills with similar-sounding descriptions can be different jobs
  (e.g. "PR code review" vs "local pre-push check"). Verify bodies before merging; only clusters
  with the same completion criteria merge.
- **Deep references.** `references/` files are one level deep. If a scenario needs a sub-scenario,
  split the scenario file, do not nest folders.
- **Editing provisioned copies.** Copies under `.agents/skills/` or a harness home are generated;
  fix the repo source and note that the copy needs re-provisioning, never hand-edit the copy.
- **No snapshot.** Always commit or stash before deleting a skill folder.
- **Restating rules after merge.** After merging bodies, search the new `SKILL.md` and
  `references/` for duplicated statements; keep one home per fact.
