# Step 2: Verify & Ship

Hermes owns the final verification and shipping. Read Grok's commit and report, verify the regression test actually proves the fix, and ship as appropriate.

## 2a: Read the Commit & Report

Read Grok's debug summary and `git -C <worktree_path> show --stat HEAD`:

- **Iron law check**: the commit must contain (1) a failing regression test that catches this exact bug, (2) the minimal fix. A commit with the fix but no regression test violates the iron law — report it to the user; do not hand-write the test yourself.
- **Diff discipline**: `git -C <worktree_path> diff <base>..HEAD` must show exactly the fix + test, not a drive-by refactor. Verify the diff, not the commit message.
- **Red-flag stops**: if the report says Grok stopped on a red flag (architecture question after 3+ failed attempts, unresolvable hypothesis), surface it to the user as an open decision — do not ship past it.

## 2b: Re-Run the Verification

Run the regression test and the repo's test suite yourself against the committed state:

```
git -C <worktree_path> status --short   # must be clean
<repo's test command, scoped to the new regression test>
<repo's full test / lint / build gate>
```

- A green run on a dirty tree is not proof — clean the tree first (if it's dirty with out-of-scope files, revert them in your own tools before running).
- **Treat a green local run that then fails CI as a verification defect, not a flake.** When CI reports a failure on the pushed SHA, pull the job log, confirm the failing line is really in the committed content, and report it — do not argue with the log.

## 2c: Commit (if Grok left it uncommitted)

If the worktree has uncommitted changes, make the commit yourself:

```
git -C <worktree_path> add -A && git -C <worktree_path> commit -m "fix: <issue-or-error> — regression test + minimal fix"
```

Commit message: conventional, repo-conforming. Amend any stray artifacts before pushing.

## 2d: Push & PR (if the user asked to ship it)

```
git -C <worktree_path> push --force-with-lease origin <worktree_branch>
gh pr create --base main --head <worktree_branch> --fill --draft
```

Always `--force-with-lease`, never bare `--force`. No `gh` or non-GitHub remote: derive the compare URL `https://<host>/<owner>/<repo>/compare/main...<worktree_branch>?expand=1`.

## 2e: Report

Report to the user:

> Bug fixed in <worktree_path>. Root cause: <...>. Regression test: <name> (proves the fix). Gate: <pass/fail>. Commit: <sha> (or PR: <url>).

Then proceed to Step 3.
