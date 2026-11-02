---
name: pr-babysit
description: >-
  Complete GitHub PR skill. Create the PR (branch, commit, push, open via gh or
  curl), monitor CI, auto-fix red checks, address review comments, resolve
  merge conflicts, merge/squash, and merge-ready ship. Watchlist mode monitors
  many PRs in parallel, detects CI/review/conflict issues, and fixes them in
  isolated worktrees. Supports independent PRs, Graphite stacks, and GitHub
  stacked PRs (gh-stack).
when-to-use: >-
  Triggers on "/pr-babysit". Create-a-PR phrasing: "pr to main", "open a PR",
  "merge PR when green", "take this branch to a merged PR", "fix issue #123
  and open a PR". Babysit phrasing: "check every open PR", "fix PR 162",
  "merger to main" (land ready PRs when green).
argument-hint: "add [--ship] <number> | remove <number> | list | check | ship [on|off] [number...]"
disable-model-invocation: true
metadata:
  tags: [github, pr, ci, review, worktree, graphite, gh-stack, babysit, conventional-commits]
  category: github
  related_skills: [github-auth, review, hermes-agent]
  backends: [grok-build, hermes]
---

# PR Workflow & Babysitter

One skill for the whole GitHub PR lifecycle. The create path opens a PR from a
worktree or branch — branch, conventional commit, push, create — and shepherds
CI to green via an auto-fix loop. The babysit path monitors many open PRs in
parallel, fixes failures in isolated worktrees, and lands ready PRs when
shipping is enabled.

## Mode selection

Dispatch by the first argument:

- **No argument** — usage help; default to one-shot create-PR flow on the current branch.
- **`/pr-babysit add|remove|list|check|ship ...`** — PR babysitter orchestrator; follow the sections below.
- **`--squash` / `--auto`** — merge-mode modifier; follow Merging.
- **Bare intent phrase** ("open a PR", "make sure CI is green", "fix issue #123
  and open a PR", "merge when green") — run the create-PR flow, then
  CI-monitor → auto-fix until green, then merge.

---

## Create-PR flow (one-shot)

Auth, token resolution, and owner/repo extraction live in `github-auth` —
source its helper rather than re-implementing the fallback chain:

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" \
         "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
echo "Using: $AUTH"; echo "Owner: $OWNER, Repo: $REPO"
```

Then route:

| Task | Recipe |
|------|--------|
| Branch, commit, push, open the PR | [`references/branch-commit-pr.md`](references/branch-commit-pr.md) |
| Commit/PR title grammar (Conventional Commits) | [`references/conventional-commits.md`](references/conventional-commits.md) |
| Watch CI until green | [`references/ci-monitoring.md`](references/ci-monitoring.md) |
| Auto-fix a red check, push, re-verify | [`references/ci-auto-fix.md`](references/ci-auto-fix.md) |
| Red log is ambiguous — flake vs real failure | [`references/ci-troubleshooting.md`](references/ci-troubleshooting.md) |
| Squash/rebase/merge, auto-merge, branch cleanup | [`references/merging.md`](references/merging.md) |
| End-to-end "Fix issue #123" with premise validation, regression test, class-level fix | [`references/issue-to-pr.md`](references/issue-to-pr.md) |

`references/pr-body-feature.md` and `references/pr-body-bugfix.md` are body
skeletons for `gh pr create --body-file` — fill the matching one when the PR
body runs longer than a few lines.

---

## Babysitter orchestrator (watchlist mode)

You are a PR babysitter. Monitor open PRs, detect CI failures, human and
bot/automated review comments, and merge conflicts, then fix them
autonomously. Fixes and commits happen **only** in subagents (spawned via
`spawn_subagent`) with worktree isolation — never as direct orchestrator edits
on the main workspace. Three PR topologies are supported:

1. **Independent PRs** — standalone PRs targeting the default branch.
2. **Graphite stacks** — stacked PRs managed by the `gt` CLI.
3. **GitHub stacked PRs** — stacked PRs managed by `gh stack`.

### Todo scaffold

For each babysat PR, create three todos:
- `pr-<n>:ci-green` — all CI checks passing
- `pr-<n>:comments-addressed` — all open review threads either fixed+resolved or substantively replied
- `pr-<n>:merge-ready` — labels applied, base up to date

When `ship` is true, also create `pr-<n>:shipped`. It completes only when the
PR is merged.

### Commands

| Command | Behavior |
|---------|----------|
| `add [--ship] <number> [<number>...]` | Add to watchlist; auto-detect stack membership; register whole stack |
| `remove <number>` | Remove from watchlist |
| `list` | All watched PRs grouped by stack, with status and ship flag |
| `check` | One check cycle — query, detect, fix; then ship cycle for `ship: true` PRs |
| `ship on|off [number...]` | Enable/disable shipping |
| `ship [number...]` | Enable if numbers given, then one ship cycle |

### State file

Per-session: `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`.
`INSTANCE_ID` is a UUID generated on first `add` (via
`<python> scripts/host.py uuid --full`, rejecting WindowsApps stubs) and held
in conversation context. Load [`references/check-cycle.md`](references/check-cycle.md)
for the full state schema and lifecycle, and [`references/adding-prs.md`](references/adding-prs.md)
for stack detection (Graphite / GitHub / API chain).

### Check cycle

Load [`references/check-cycle.md`](references/check-cycle.md) — the full
query, decision tree, conflict resolution, CI auto-fix, review-thread
handling, and bot-comment handling per subagent.

### Shipping

Load [`references/shipping.md`](references/shipping.md) when the command is
`ship`, or when any watched PR has `ship: true`.

### Hermes variant

Load [`references/hermes.md`](references/hermes.md) when running inside a
**Hermes** session — it carries the Hermes dispatch primitives
(`delegate_task`, `cronjob_manage`, Orca worktrees) and the
`${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit/` state path. The body above
targets the Grok Build harness.
