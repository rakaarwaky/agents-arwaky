# Common Mistakes

## Parallel agents committing in the same tree

This repo is worked on by multiple agents (GrokBuild via Orca, Hermes). A
concurrent commit can sweep your staged changes into someone else's commit
(e.g., your `git rm` landing in another agent's commit) and change the HEAD you
snapshotted against. After any snapshot and before committing, re-run
`git log --oneline -4` and `git status`; re-verify on-disk state before
executing; keep your commit scoped to your own task files only — never
`git add -A`.

## Absorbing a skill whose own SKILL.md is a thin TOC over the survivor's references

When the dropped skill's body routes into the surviving skill ("this is covered
in `context7-cli`", links the survivor's references), the two are the same job
with a routing split, not variants with distinct scenarios. Drop the dropped
skill's folder and delete any survivor reference that duplicates it — do not
move the dropped SKILL.md into the survivor's `references/` as a new scenario
file; that restates content that already lives in the survivor's own references
(rule-restatement mistake, not a new sub-scenario).

## Staging with `git add -A .` from inside a subdirectory

Inside `skills/<category>/`, `git add -A .` stages every tracked file under
that subdirectory, not just the prune's changes — a sibling subagent that
committed concurrent work in the same checkout (or a path typo reaching a
parent) silently pulls unrelated deletions into the commit. Use explicit
top-level paths (`git add skills/<category>/ skills/CATALOG.md`) and verify the
staged set with `git status --short` before committing.

## Merging across domains

Two skills with similar-sounding descriptions can be different jobs (e.g.,
"PR code review" vs "local pre-push check"). Verify bodies before merging;
only clusters with the same completion criteria merge.

## Deep references

`references/` files are one level deep. If a scenario needs a sub-scenario,
split the scenario file; do not nest folders. This also applies when absorbing
another skill's references: moving skill B's `references/` into skill A must
stay flat — the executable `category-depth` rule rejects
`references/<subdir>/`; prefixed renames are safe.

## Editing provisioned copies

Copies under `.agents/skills/` or a harness home are generated; fix the repo
source and note that the copy needs re-provisioning; never hand-edit the copy.

## No snapshot

Always commit or stash before deleting a skill folder.

## Interacting with the user during a prune

When the user asks which skills to delete and frames it as "ask me, then
recommend," ask **specific, one-skill, binary yes/no** questions — never a
multi-skill bucket ("do you use the creative pack?" gets rejected as too
broad). Name each skill and its concrete job in the question. Batching a few
independent binary questions per turn is fine; lumping a whole class of skills
into one question is not.

## Restating rules after merge

After merging bodies, search the new `SKILL.md` and `references/` for
duplicated statements; keep one home per fact.

## Dangling cross-references between absorbed files

When a dropped skill's `references/` files are moved next to the surviving
skill's own `references/`, any cross-links in the moved files (or in the
surviving `SKILL.md`) that pointed at `SKILL.md` step N, or at a sibling under
the old folder, now dangle. Rewrite them to name the sibling reference file
directly (`see model-tier-list.md step 6`, not `see SKILL.md step 6`). Step 9's
"all reference links resolve" check only passes if these were re-pointed; add
them to the Step 9 pass before committing. Also re-point any *catalog*
reference to the dropped skill's name: the surviving skill's frontmatter
`description` (which drives routing and catalog search) and the `CATALOG.md`
rows both key off the old skill's name — after the merge, absorb the dropped
skill's trigger terms into the surviving `description` (e.g. a dropped
`find-docs` skill's terms must appear in `context7-cli`'s description) or
catalog search stops routing requests to the surviving skill.

## Skipping the approval gate

Present the dry-run report and wait for explicit confirmation before Step 6;
first-time runs on a skill tree are approval-gated.

## Unattended runs

A headless pass (cron, `/loop`, background task) must use `--evolution`
explicitly; relying on `--auto` is acceptable only when the run has no user to
ask and the snapshot commit is verified before reporting.
