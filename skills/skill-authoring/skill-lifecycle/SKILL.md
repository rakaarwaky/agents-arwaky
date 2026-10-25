---
name: skill-lifecycle
description: Prunes and consolidates SKILL.md collections — deduplicates overlapping skills into one folder with one SKILL.md, or keeps one folder with a references/ subfolder for complex variants. Use when cleaning up, auditing, or merging agent skill directories, pruning skills, consolidating skills, merging duplicate skills, auditing a skill directory, collapsing skill folders, or running a scheduled self-evolution pass over a skill tree.
when-to-use: Use when cleaning up, auditing, or merging agent skill directories; pruning skills; consolidating skills; merging duplicate skills; auditing a skill directory; collapsing skill folders; or running a scheduled (headless) evolution pass that applies approved changes without an interactive approval gate.
argument-hint: "[<skill-dir>] [--dry-run | --auto | --evolution]"
metadata:
  tags:
    - skill
    - pruning
    - deduplication
    - consolidation
    - skill-cleanup
    - agent-skills
---

# skill-lifecycle

Prunes and consolidates an agent **skill directory** (a collection of `SKILL.md` folders). It finds
skills that overlap semantically and collapses them: two skills covering the same job become one
folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with
one `SKILL.md` plus a `references/` subfolder, one file per scenario. Modeled on
`code-quality/cleanup-consolidate` (two-phase: remove duplicates, then consolidate variants).

**Scope:** skill directories only — `SKILL.md` files, `references/`, `scripts/`, and category
`DESCRIPTION.md` files. Never touch non-skill content. This is the skill-folder analog of dead-code
removal plus consolidation: Phase 1 removes true duplicates, Phase 2 merges overlapping variants.

## Routing

- **`skill-design`** — authoring a new skill or auditing one `SKILL.md` (the prune happens after
  the authoring, not instead of it).
- **`skill-library`** — cataloging the library and repairing mechanical frontmatter faults before
  a prune.
- **`skill-library`** — read-only listing and inspecting skills (`aa skills list/show`), for the
  inventory a prune starts from.
- **`code-quality/cleanup-consolidate`** — the code-level duplicate removal this skill is modeled on.

Frontmatter constraints for a merged `SKILL.md` are not restated here: the executable rules and
their messages live in [`../../../modules/skills/_rules/skill-rules.md`](../../../modules/skills/_rules/skill-rules.md), generated from
`_rules/skill_rules.py`. A merge that produces a rule violation is caught by running
`aa skills validate`.

## Path Handling

- **Default audit root:** `/home/raka/agents-arwaky/skills` (the repo's skill tree).
- **User-supplied path:** if the user names a path, audit that path instead. Resolve it before
  starting. Reject the request if the path resolves to a file instead of a directory.
- **Scoping:** The user can supply the root `/skills` directory for a full tree audit, or a
  specific category folder (e.g., `/skills/devops`) to scope the audit strictly to that category.
- **Scoped multi-skill merge:** the user can also name two or more specific skill folders
  (e.g., two sibling skills in the same category) and ask to prune/consolidate just those.
  In that case skip the full-tree inventory; treat exactly the named skills as the audit
  set, run Steps 2–4 on that set, and produce a scoped report listing the named audit root
  rather than the whole tree. Do not let the default audit root expand the scope beyond the
  skills the user named — other folders are out of scope unless they are affected (e.g.
  `CATALOG.md` rows pointing at a dropped skill).
- **Validation:** Confirm the resolved directory contains one or more folders with a `SKILL.md`.
  If it contains no `SKILL.md` subfolders, stop and inform the user that the path is not a valid
  skill tree.
- **Definitions:** A skill folder = `<dir>/<name>/SKILL.md`, optionally with `references/` and
  `scripts/` subfolders. Category folders (e.g., `code-quality/`) hold many skill folders plus a
  `DESCRIPTION.md`.

## Two-Phase Approach

**CRITICAL:** Phase 1 removes duplicates. Phase 2 consolidates remaining variants. Never skip
Phase 1 — merging skills that are already true duplicates is wasted effort.

### Phase 1 — Remove true duplicates

Two skills are duplicates when their scope, procedures, and completion criteria are equivalent and
one adds no scenario the other covers.

- **Same folder name, different trees** — provisioned copies under `.agents/skills/` or a
  harness home that mirror this repo's skill: keep the repo source, note the copy; never edit the
  copy (copies are provisioned artifacts). Flag in the report that the copy needs re-provisioning.
- **Byte-identical or near-identical bodies** — merge into one; keep the more complete body, drop
  the rest.
- **Same `name:` in frontmatter appearing in two folders** — one is stale; keep the more
  complete, delete the other.

### Phase 2 — Consolidate overlapping variants

Skills are variants when they share a domain but each covers a distinct scenario.

| Input | Output |
|---|---|
| 2+ skills with the same job and overlapping scenarios | **one folder, one `SKILL.md`** — merge bodies, deduplicate rules, union the trigger terms |
| Merged skill now has complex, distinct sub-scenarios | **one folder, one `SKILL.md`, plus `references/`** — `SKILL.md` keeps the shared rules and a routing table; each sub-scenario becomes `references/<scenario>.md`, one level deep |
| Skills that are genuinely different jobs | leave both alone; note in the report why they were not merged |

A merged `SKILL.md` follows `skill-design` conventions: frontmatter with `name` and
`description` (third person, includes trigger terms), routing in the body rather than in
non-parsed keys (`triggers:` and `metadata.related_skills` are not parsed by Grok Build —
trigger terms go in `description:`/`when-to-use:`, sibling skills in a body section), and a
body that is a table of contents linking one level deep into `references/`. The exact
frontmatter constraints are the rules in [`../../../modules/skills/_rules/skill-rules.md`](../../../modules/skills/_rules/skill-rules.md).

## Workflow

**`--auto`** — skip the dry-run approval gate: after Step 4 classification, proceed straight to Step 6 snapshot then Steps 7–9 execution. Use only when you have already reviewed the planned prune and accept automatic application.

**`--evolution` (headless mode)** — for scheduled or unattended runs (a cron job, `/loop`, a background task with no interactive user): apply the planned changes without waiting at the Step 5 approval gate. Before executing, the run must still pass Step 9 verification, and the rollback snapshot from Step 6 is the undo path — record the snapshot SHA in the commit message and the final report. A headless run that cannot commit (dirty tree, no git) falls back to `--dry-run` and reports instead of applying.

Task Progress:

- [ ] Step 1: Confirm audit root (default `/home/raka/agents-arwaky/skills`, a specific category,
      or the user's path).
- [ ] Step 2: Inventory — list every skill folder, read each `SKILL.md` frontmatter and body.
- [ ] Step 3: Group — cluster skills by semantic scope using `description` and trigger terms, then
      verify clusters against body content (two descriptions that rhyme can be different jobs).
- [ ] Step 4: Classify each cluster — duplicate (identical scope) vs variant (same domain, distinct
      scenarios) vs separate jobs.
- [ ] Step 5: **Dry Run & Approval** — generate the planned report (see Report Format). Present it
      to the user and explicitly ask: *"Here is the planned prune. Shall I proceed with the git
      snapshot and execute these changes?"* **Wait for user confirmation before proceeding.**
      With `--auto` or `--evolution`, skip this gate and proceed straight to Step 6.
- [ ] Step 6: Snapshot the tree in git (`git add -A && git commit -m "snapshot: before
      skill-lifecycle"`, or `git stash` if the tree is dirty for other reasons). If the
      working tree already holds unrelated in-progress changes, record the current `HEAD`
      commit SHA as the rollback target and stage only the skill-tree paths you touch —
      never `git add -A` into the same commit as unrelated work. The rollback target is
      that HEAD SHA; `git reset --hard <sha>` after the merge restores both the skill and
      unrelated state.
- [ ] Step 7: Execute merges per the Phase 2 table. When merging, delete the redundant folders
      (keep one canonical folder name, preferring the existing skill whose `name:` in frontmatter
      matches the surviving scope).
- [ ] Step 8: Update the category `DESCRIPTION.md` if a folder was removed or renamed. If a category
      is left completely empty, delete the category folder and its `DESCRIPTION.md`. Also
      reconcile `skills/CATALOG.md`: drop the row for every dropped skill, add/update the row
      for the surviving skill's new description, and adjust the category's skill-count
      column. The catalog is a generated artifact (`aa skills catalog [--check]`), so after
      the manual edit run that command to confirm it is consistent before committing.
- [ ] Step 9: Verify — every remaining `SKILL.md` parses as valid frontmatter, all `references/`
      links resolve (including cross-links *within* the `references/` set, not just from
      `SKILL.md` to `references/`), no two skills share a `name:`, and `aa skills validate`
      reports no issues. Also confirm `skills/CATALOG.md` still matches the on-disk state
      (or run `aa skills catalog` to regenerate it). *If verification fails, trigger the
      Rollback Protocol.*
- [ ] Step 10: Report — Output the final executed `skill-lifecycle report`.

## Merge Rules

- **Name survival** — the surviving skill keeps the `name:` that best matches the merged scope; if
  neither matches, pick the more specific one.
- **Frontmatter union** — merge `tags` and `when-to-use` as unions, de-duplicated; merge any
  body Routing sections and drop entries pointing at skills that no longer exist. Merge
  `triggers:` terms into `description:`/`when-to-use:` — the key is not parsed. If the
  surviving skill had `tags: []` and the dropped skill had populated `tags`, carry the
  dropped skill's tags into the survivor — otherwise the surviving skill loses its
  searchability for that topic and the catalog search no longer reaches it.
- **Body merge** — shared rules go in the `SKILL.md` body exactly once. Scenario-specific rules
  move to `references/<scenario>.md`. Never restate a rule that already exists in a reference.
- **Conflict Resolution** — if merged skills contain contradictory rules (e.g., opposing
  instructions), prioritize the rule from the skill with the more complete body. If a clear winner
  isn't obvious, flag the contradiction in the report for the user to resolve manually.
- **Scripts** — keep `scripts/` of the surviving skill; move or re-link scripts of dropped skills
  only if the surviving skill's scenario needs them. Ensure no scripts referenced in the surviving
  body are deleted.
- **Empty Category Cleanup** — if deleting duplicate skills leaves a category folder entirely
  empty (no skill subfolders remain), delete the empty category folder and its `DESCRIPTION.md` as
  well. Note this in the DELETED section of the report.
- **DESCRIPTION.md** — if a category is not empty, its description stays one line; update it only
  if the category's skill count changed in a way that breaks the description.

## Report Format

```text
skill-lifecycle report — <audit root>

MERGED:
- <surviving folder>  <-  <dropped folder(s)>
    reason: <duplicate scope / shared domain>
    action:  <body merged | references/ created for scenarios: a, b | duplicates dropped>

KEPT SEPARATE:
- <skill A> vs <skill B>  —  reason: <distinct jobs, e.g. different completion criteria>

DELETED:
- <folder>  —  reason: <true duplicate of <survivor>, stale name collision, empty category cleanup>

ROLLBACK TARGET:
- <snapshot commit SHA or stash ref>

VERIFY:
- N skills remain, 0 shared names, all reference links resolve, all frontmatter parses
```

## Rollback Protocol

Verification (Step 9) is the gate for rollback:

1. **Hard failure** — a `SKILL.md` no longer parses, a `references/` link is broken, or two skills
   share a `name:`. Restore the snapshot (`git reset --hard <sha>` or `git stash pop`), re-run
   only the offending merge, and re-verify.
2. **Soft failure** — a merge looks structurally valid but content was lost or contradicted.
   Restore the affected files only, keep the rest of the prune, and flag the conflict for manual
   resolution.
3. If the user aborts between snapshot and execution, restore the snapshot and leave the tree
   unchanged.

## Common Mistakes

- **Merging across domains.** Two skills with similar-sounding descriptions can be different jobs
  (e.g., "PR code review" vs "local pre-push check"). Verify bodies before merging; only clusters
  with the same completion criteria merge.
- **Deep references.** `references/` files are one level deep. If a scenario needs a sub-scenario,
  split the scenario file; do not nest folders. This also applies when absorbing another
  skill's references: moving skill B's `references/` into skill A must stay flat — the
  executable `category-depth` rule rejects `references/<subdir>/`; prefixed renames are safe.
- **Editing provisioned copies.** Copies under `.agents/skills/` or a harness home are generated;
  fix the repo source and note that the copy needs re-provisioning; never hand-edit the copy.
- **No snapshot.** Always commit or stash before deleting a skill folder.
- **Interacting with the user during a prune.** When the user asks which skills to delete and
  frames it as "ask me, then recommend," ask **specific, one-skill, binary yes/no** questions —
  never a multi-skill bucket ("do you use the creative pack?" gets rejected as too broad).
  Name each skill and its concrete job in the question. Batching a few independent binary
  questions per turn is fine; lumping a whole class of skills into one question is not.
- **Restating rules after merge.** After merging bodies, search the new `SKILL.md` and
  `references/` for duplicated statements; keep one home per fact.
- **Dangling cross-references between absorbed files.** When a dropped skill's
  `references/` files are moved next to the surviving skill's own `references/`, any
  cross-links in the moved files (or in the surviving SKILL.md) that pointed at
  `SKILL.md` step N, or at a sibling under the old folder, now dangle. Rewrite them to
  name the sibling reference file directly (`see model-tier-list.md step 6`, not
  `see SKILL.md step 6`). Step 9's "all reference links resolve" check only passes if
  these were re-pointed; add them to the Step 9 pass before committing.
- **Skipping the approval gate.** Present the dry-run report and wait for explicit confirmation
  before Step 6; first-time runs on a skill tree are approval-gated.
- **Unattended runs.** A headless pass (cron, `/loop`, background task) must use `--evolution`
  explicitly; relying on `--auto` is acceptable only when the run has no user to ask and the
  snapshot commit is verified before reporting.
