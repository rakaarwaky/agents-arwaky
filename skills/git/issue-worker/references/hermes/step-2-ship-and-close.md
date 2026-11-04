# Step 2: Push & Open PRs, Close/Reopen Issues

Hermes owns every push, PR, and issue-state operation. Grok never commits, pushes, opens a PR, or writes to the tracker (`grok/step-7-fanout.md` child scope).

## 2a: Push & Open PRs (one PR per issue)

For each verified issue worktree:

```
git -C <worktree_path> push --force-with-lease origin <worktree_branch>
gh pr create --base main --head <worktree_branch> --draft --title "<issue title>" --body "<mechanism from Grok's report>"
```

- Always `--force-with-lease`, never bare `--force`.
- Draft by default; auto-merge is out of scope.
- `Closes #N` goes into the issue/PR **only after the PR merges** — the skill never merges.
- No `gh` or non-GitHub remote: derive the compare URL `https://<host>/<owner>/<repo>/compare/main...<branch>?expand=1` and hand the user a copy/paste-ready `gh pr create` command.

## 2b: Close Verified-on-Main Issues

For each issue 0a marked `fixed-on-main`:

```
gh issue close <N> --reason completed --comment "Verified fixed at HEAD: <file:line> shows <what>. Proof: \`<command>\` → <output>."
```

Never close on label, audit date, or a bare `Closes #N` without tree evidence (`grok/step-4-verify-triage.md`).

## 2c: Reopen Stale Closures

If 0a found an issue closed with `Closes #N` but the fix did not actually land (still broken at HEAD), it is already `still-broken` and got a Grok pass in Step 0 — no separate reopen step. If it was *not* in the original argument list and you found it while auditing, `gh issue reopen <N>` with an evidence comment, then add it to the next wave.

## 2d: Rebase Still-Open Branches (if PRs merged mid-batch)

Per `grok/step-10-rebase.md`: rebase still-open worktree branches onto the current default tip after any PR lands, so later PRs don't carry stale bases.

## Report

> Pushed <N> branches, opened <N> draft PRs (one per issue: <urls>). Closed <K> verified-on-main issues with evidence. <M> issues remain open (Grok pass failed or not yet spawned).

Then proceed to Step 3.
