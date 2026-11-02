# Phase F — Rebase open work after merges

After a wave of PRs lands on the default branch, rebase every still-open branch onto the new tip before letting CI re-run. A stale base fails self-lint and format against already-merged code, and the fix is a one-command rebase.

Rebase **one** branch at a time and confirm `git status` is clean before force-pushing — a blind rebase-and-force-push loop across worktrees leaves dirty rebase states that block the next wave.

Sibling-PR conflict shape, stale-CI diagnosis, and the rebase checklist: [wave-rebase.md](wave-rebase.md).
