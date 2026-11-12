---
name: mergify
description: Mergify CLI surface — stacked PRs, merge queue, CI insights, config validation, mergify events.
when-to-use: Run any Mergify workflow — push or stack commits/PRs, diagnose merge-queue PRs, Depends-On/Merge-After/scheduled freezes, JUnit upload and quarantine, scopes detection, write or validate .mergify.yml, browse Mergify events.
argument-hint: <stack|queue|freeze|ci|tests|config|events> [--token <token>] [--repository <owner/repo>]
created_by: curator
---

# Mergify

One skill covers the whole Mergify CLI surface. Pick the scenario below; each file is self-contained for that command group. Do not invent Mergify config or CLI behavior from memory — fetch the docs links inside the scenario file when writing configuration.

## Global Rules

Rules that apply to every Mergify scenario. Scenario files cite these; they never restate them.

- **Credential auth**: Most authenticated commands accept `--token` / `-t` (`MERGIFY_TOKEN`, from `mergify auth login`, or a deprecated GitHub token) and `--repository` / `-r` (`owner/repo`, often auto-detected from git remote or CI).
- **API URL**: `--api-url` / `-u` (`MERGIFY_API_URL`), default `https://api.mergify.com`.
- **CI Insights keys**: CI Insights uses a different key split (`ci` vs `admin` application keys). See [`references/ci.md`](references/ci.md).
- **Facts are self-contained**: Each scenario file owns its CLI behavior; do not restate scenario rules in the body or other scenario files.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Stacked PRs | [`references/stack.md`](references/stack.md) | `git push`, commits, branches, PR create/update, rebase/fixup/squash/reword, amend notes, GitHub-native stacks. Prefer `mergify stack *` over `git push` / `git rebase -i` / `gh pr edit`. |
| Merge queue | [`references/merge-queue.md`](references/merge-queue.md) | Queue/dequeue via PR comments, `mergify queue status/show/pause/unpause`, diagnosing a dequeued PR, dequeue codes. |
| Merge protections | [`references/merge-protections.md`](references/merge-protections.md) | `Depends-On:` / `Merge-After:` headers, scheduled freezes (`mergify freeze`), deployment windows. |
| CI Insights | [`references/ci.md`](references/ci.md) | `mergify ci` (JUnit process/upload, git-refs, scopes, queue-info), `mergify tests` (show, quarantines). |
| Configuration | [`references/config.md`](references/config.md) | Validate, simulate, write or edit `.mergify.yml` / Mergify config. |
| Activity log | [`references/events.md`](references/events.md) | `mergify events` — timeline of what Mergify did to a repo or PR. |


