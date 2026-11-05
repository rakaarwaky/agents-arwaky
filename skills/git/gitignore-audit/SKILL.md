---
name: gitignore-audit
description: Find .gitignore coverage gaps and add missing rules.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [git, gitignore, repo-hygiene, secrets]
    related_skills: [repo-manager, xdg-spec-compliance]
---

# gitignore-audit

Audit a repo's .gitignore: find items that should be ignored but aren't, add the rules, and report tracked files that a new rule won't untrack.

## When to Use

- User asks what should be added to / checked in the repo's .gitignore.
- A commit just landed that swept in runtime state, caches, lockfiles, or browser-profile files.
- Before shipping a repo-wide cleanup: verify .gitignore actually covers the files on disk.

## Steps

1. Read the existing .gitignore to know the current rule style and what's already covered (catch-all globs, sectioning).

2. **Find candidates by three-way diff** — the three signal sets:
   - `git ls-files | grep -iE 'env|auth|secret|key|pem|lock|sock|cookie|browser|...'` — tracked files that look sensitive; these are already in the index and .gitignore rules won't help (see step 5).
   - `git ls-files --others --exclude-standard` — untracked files; anything showing here that looks runtime/secret is not covered by current rules.
   - `ls -A` plus per-suspicious-dir `ls -A` at repo root and key subdirs — on-disk items missing from both sets above; cross-check each with `git check-ignore -v <path>` to confirm which rule actually covers it (a file can match two rules; the `-v` output shows which).

3. **Confirm gaps with `git check-ignore -v`**: for each suspicious on-disk path, run `git check-ignore -v <path>`. No output = not ignored = gap. When a rule matches, note which rule so you don't duplicate it.

4. **Add the missing rules** via `patch`, grouped into a sensible section of the existing .gitignore (match its comment style and placement; append to the nearest themed section or add a new section at the bottom).

5. **Flag the tracked-but-now-ignored set**: `git ls-files -c` lists tracked files that a new rule now matches. .gitignore never untracks these — the user must `git rm -r --cached <path>` next commit or they keep being committed. Report the count and exact command; do not run the rm yourself unless asked.

6. **Verify**: re-run `git check-ignore -v` on each newly-ignored path to confirm the new rule fires (output now shows the new rule line), and re-run `git ls-files -c` to confirm no *other* tracked files were accidentally swept in by an over-broad rule.

## Pitfalls

- `git check-ignore -v` with zero matches is a bash non-fatal failure in compound pipelines — when scripting over several paths, don't rely on `&&` chains; check output emptiness per-path in a loop.
- Broad glob sections already in the .gitignore silently cover more than they appear to (e.g. `**/*.lock` covers `auth.lock`, `gateway.lock`…; `*.bak*` covers `config.yaml.bak`, `.env.bak-*`). Before adding a rule, run `git check-ignore -v` on a sample of the items you think are gaps — half of them are already covered.
- Tracked files are the real leak, not untracked ones: a .gitignore with no rule for `bot-desktop/` is harmless until files get committed; once committed, the .gitignore alone does nothing for them. Always close the audit with the `git ls-files -c` count and the `rm --cached` command, even when it's zero ("nothing to untrack" is a verified good result, say so explicitly).
- Don't over-ignore: some .snapshot/.db files are intentional backups (the repo's own backup convention) — check the .gitignore's section headers and existing tracked snapshots before blanket-ignoring `*.snapshot` or `*.db`.
