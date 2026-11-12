# .gitignore coverage audit

Find items that should be ignored but aren't, add the rules, and report tracked files a new rule won't untrack.

## When to Use

- User asks what should be added to / checked in the repo's .gitignore.
- A commit just landed that swept in runtime state, caches, lockfiles, or browser-profile files.
- Before shipping a repo-wide cleanup: verify .gitignore actually covers the files on disk.

## Steps

1. Read the existing .gitignore: current rule style, sectioning, catch-all globs already in play.

2. **Find candidates by three-way diff** — three signal sets:
   - `git ls-files | grep -iE 'env|auth|secret|key|pem|lock|sock|cookie|browser|...'` — tracked files that look sensitive; already in the index, .gitignore rules won't help (step 5).
   - `git ls-files --others --exclude-standard` — untracked files; anything here that looks runtime/secret is not covered by current rules.
   - `ls -A` plus per-suspicious-dir `ls -A` at repo root and key subdirs — on-disk items missing from both sets above; cross-check each with `git check-ignore -v <path>` (a file can match two rules; `-v` shows which).

3. **Confirm gaps with `git check-ignore -v`**: for each suspicious on-disk path, `git check-ignore -v <path>`. No output = not ignored = gap. When a rule matches, note which one so you don't duplicate it.

4. **Add the missing rules** via `patch`, grouped into a sensible section of the existing .gitignore (match its comment style and placement; append to the nearest themed section or add a new one at the bottom).

5. **Flag the tracked-but-now-ignored set**: `git ls-files -c` lists tracked files that a new rule now matches. .gitignore never untracks them — the user must `git rm -r --cached <path>` next commit. Report the count and exact command; do not run the rm unless asked.

6. **Verify**: re-run `git check-ignore -v` on each newly-ignored path (output now shows the new rule line) and re-run `git ls-files -c` to confirm no *other* tracked files were accidentally swept in by an over-broad rule.

## Pitfalls

- `git check-ignore -v` with zero matches is a non-fatal failure in compound pipelines — when scripting over several paths, check output emptiness per-path in a loop, not `&&` chains.
- Broad glob sections already in the .gitignore silently cover more than they appear to (`**/*.lock` covers `auth.lock`, `gateway.lock`; `*.bak*` covers `config.yaml.bak`, `.env.bak-*`). Before adding a rule, run `git check-ignore -v` on a sample of the items you think are gaps — half are already covered.
- Tracked files are the real leak, not untracked ones: a missing rule is harmless until files get committed; once committed, .gitignore alone does nothing. Always close with the `git ls-files -c` count and the `rm --cached` command, even when zero ("nothing to untrack" is a verified good result, say so explicitly).
- Don't over-ignore: some .snapshot/.db files are intentional backups — check section headers and existing tracked snapshots before blanket-ignoring `*.snapshot` or `*.db`.
