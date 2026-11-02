# Mode selection

Dispatch by the first argument:

- **No argument** — usage help; default to one-shot create-PR flow on the current branch.
- **`/pr-babysit add|remove|list|check|ship ...`** — PR babysitter orchestrator; follow [watchlist.md](watchlist.md).
- **`--squash` / `--auto`** — merge-mode modifier; follow [merging.md](merging.md).
- **Bare intent phrase** ("open a PR", "make sure CI is green", "fix issue #123 and open a PR", "merge when green") — run the create-PR flow, then CI-monitor → auto-fix until green, then merge.
