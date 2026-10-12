---
name: aa-connect-hermes-profile-skill-provisioning
description: "aa connect: symlink pack into all Hermes profiles."
metadata:
  tags:
    - hermes
    - profiles
    - skills
    - aa-connect
    - agents-arwaky
    - symlinks
    - provisioning
  related_skills:
    - agent-harness-connectors
    - hermes-profiles
    - profile-scoped-plugins
---

# `aa connect --hermes`: link the skill pack into every Hermes profile

Use when the user wants the agents-arwaky skill pack available in **all** Hermes
profiles, or when a named-profile session cannot see the pack. This is the
current model — it supersedes the older "named profiles must NOT get the
generalist pack" rule. Standing instruction: **every profile gets the pack**;
role filtering happens per-profile via `skills.disabled` config, never by
withholding the symlink.

## When to Use

- The user wants the agents-arwaky skill pack in **all** Hermes profiles, or
  says "make skills available in every profile."
- A named-profile session cannot see the pack.
- After an `aa connect --hermes --skills-only --force` apply that may have
  left stray runtime state files in the pack root.

## Why profiles need explicit linking

Hermes named profiles are isolated `HERMES_HOME`s at
`~/.hermes/profiles/<p>/` with their own `skills/` dir. They do **not**
inherit `~/.hermes/skills`. So the default-home symlink alone leaves every
named profile skill-blind. `aa connect --hermes --skills-only` therefore
links the pack into the default home **and** each detected
`~/.hermes/profiles/<p>/skills`, driven by `HermesAdapter.skills_targets()`
(returning `(Default Profile, ~/.hermes/skills)` plus one
`(Profile: <p>, ~/.hermes/profiles/<p>/skills)` per profile dir).
`HarnessSkills._provision_one` loops all of these via the
`_skills_targets_for(adapter)` helper; adapters without `skills_targets()`
fall back to their single `skills_dir()`. `aa disconnect --hermes` mirrors
the same loop — it is the clean inverse.

## Procedure

1. **Dry-run first** (no mutation, shows the full target plan):
   ```bash
   aa connect --hermes --skills-only --dry-run --force
   ```
   Output lists `Default Profile` + every `Profile: <p>`.
   Without `--force`, `connect` aborts if any profile `skills/` dir is a
   non-empty real directory that is not already a pack symlink. That
   abort is the intended guardrail, not a bug.

2. **Apply** (backs up live state, replaces each target with a pack symlink):
   ```bash
   aa connect --hermes --skills-only --force
   ```

3. **Verify** — every target is now a symlink to the pack:
   ```bash
   for p in ~/.hermes/skills ~/.hermes/profiles/*/skills; do
     [ -L "$p" ] && echo "OK  $p -> $(readlink $p)" || echo "BAD $p"
   done
   ```
   Live-state backups land at `~/.hermes/profiles/<p>/skills.backup-<ts>/`.
   Re-count with `hermes -p <p> skills list` per profile; a profile that
   disagrees has a broken/missing symlink — `ls -ld ~/.hermes/profiles/*/skills`.

4. **Clean stray pack files** if a previous apply crashed mid-migration (the
   old merge-into-pack path left runtime state in the pack root):
   ```bash
   rm -f <pack>/skills/.usage.json <pack>/skills/.usage.json.lock \
         <pack>/skills/.curator_state <pack>/skills/.bundled_manifest
   ```
   These are git-ignored. Confirm with `git status --short skills/` that only
   genuine skill files are untracked.

## State-safety invariant (the crash that motivated it)

A live profile `skills/` dir holds runtime state files: `.usage.json`,
`.usage.json.lock`, `.curator_state`, `.bundled_manifest`. `_link_skills_root`
(in `modules/harness/src/capabilities_harness_skills.py`) detects these via
the `_LIVE_SKILLS_STATE` set. When present, it **backs up the whole dir in
place** to `skills.backup-<ts>/` and never merges state into the pack.
Ordinary non-live dirs keep the old migrate-into-pack union semantics.

Do **not** remove the live-state branch to simplify the code: merging state
files into the pack root (a) crashes on a non-directory hidden file with
`NotADirectoryError`, and (b) pollutes the shared pack with per-profile state
that is git-ignored anyway. The pack must stay clean of runtime state.

## Pitfalls

- `--force` is required after any `--copy-skills` run or manual profile work;
  plain `aa connect` correctly aborts on a real-dir profile — that guardrail
  is the feature, not a defect.
- The first apply can crash mid-migration; check for stray pack files (step 4)
  after **every** `--force` run, not just the first.
- A live Hermes session running during apply is safe: writes to
  `.usage.json` etc. through the symlink land in the pack, are git-ignored,
  and re-appear at the next session start. No data loss — just expect them in
  `git status` noise until gitignored (they already are).
- `aa disconnect --hermes` unlinks every pack-pointing profile skills dir but
  leaves the `skills.backup-*/` dirs alone (real dirs, not symlinks).
- The `aa` launcher resolves to the main clone's modules; applying from a
  worktree runs main-clone code. Merge worktree changes into main before the
  real apply.

## Code locations

| Symbol | File |
|---|---|
| `HermesAdapter.skills_targets()` | `modules/harness/src/capabilities_harness_hermes_adapter.py` |
| `_skills_targets_for(adapter)` | `modules/harness/src/capabilities_harness_skills.py` |
| `_link_skills_root(...)` + `_LIVE_SKILLS_STATE` | same file |
| `_remove_skill_provisioned_targets(adapter)` | `modules/harness/src/capabilities_harness_disconnector.py` |
| `--force` → `provision_skills` | `modules/harness/src/capabilities_harness_connector.py` |

## Stale user-owned skills to adopt

The two user-owned skills that still encode the obsolete "never link profiles"
rule are `agent-harness-connectors` and `hermes-profiles` (devops). Until they
are adopted, this skill is the authoritative statement of the current model.
Recommended: `hermes curator adopt agent-harness-connectors` and
`hermes curator adopt hermes-profiles`, then their `references/` can be updated
in place to match.
