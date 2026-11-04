# Step 2: Verify & Ship

Hermes owns the final git operations. Read Grok's report, verify the verification gates actually passed on the committed state, and commit/push/PR as appropriate.

## 2a: Read Grok's Report

Read the step 7 report and cross-check:

- **Verification gates**: Grok claims the language's gates passed. Re-run them yourself against the committed tip (`git -C <worktree_path> status --short` must be clean first — a green run on a dirty tree is not proof): the language's test/lint/build commands from `grok/step-6-verification-gates.md`. A dirty-tree green is not a proof; clean the tree, then run.
- **"Bugs found" section**: if non-empty, surface each bug prominently to the user — these are NOT cleanup items, they are correctness bugs the sweep surfaced. Do not fold them into the cleanup tiers.
- **RISKY-tier items**: list them in the report to the user with their risk descriptions and test-coverage status — they were recorded, not applied (headless mode).

## 2b: Commit (if Grok left it uncommitted)

Grok was told to make one commit. If the worktree has no commit yet (Grok edited files but didn't commit), make it:

```
git -C <worktree_path> add -A && git -C <worktree_path> commit -m "deep-clean: <path> — <N> removed, <M> merged"
```

If `--dry-run`, there must be no commit — verify `git -C <worktree_path> log --oneline -1` matches the branch's base.

## 2c: Push (only if the user asked to ship it)

Deep-clean runs are usually local pre-merge or post-refactor work. Only push and open a PR when the user explicitly asked for it:

```
git -C <worktree_path> push --force-with-lease origin <worktree_branch>
gh pr create --base main --head <worktree_branch> --fill --draft
```

Always `--force-with-lease`, never bare `--force`. No `gh` or non-GitHub remote: derive the compare URL `https://<host>/<owner>/<repo>/compare/main...<worktree_branch>?expand=1`.

## 2d: Report

Report to the user:

> Deep-clean of <path> verified. Gates: <pass/fail>. Bugs found: <N> (listed). RISKY items deferred: <K>. Commit: <sha> (or: dry-run — no commit). <PR URL if pushed.>

Then proceed to Step 3.
