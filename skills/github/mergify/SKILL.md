---
name: mergify
description: mergify, stacked PR, merge queue, CI insights, config validation.
when-to-use: Run any Mergify workflow — push or stack commits/PRs, diagnose merge-queue PRs, Depends-On/Merge-After/scheduled freezes, JUnit upload and quarantine, scopes detection, write or validate .mergify.yml, browse Mergify events.
argument-hint: <stack|queue|freeze|ci|tests|config|events> [--token <token>] [--repository <owner/repo>]
metadata:
  tags:
    - mergify
    - github
    - pr
    - ci
    - merge-queue
    - stack
  related_skills:
    - github/github-pr-workflow
    - github/github-code-review
    - github/releasing
  triggers:
    - mergify
    - mergify stack
    - stack push
    - stacked PR
    - merge queue
    - dequeue
    - queue status
    - depends-on
    - merge-after
    - freeze
    - mergify config
    - mergify.yml
    - junit
    - quarantine
    - scopes
    - ci insights
    - activity log
    - mergify events
---

# Mergify

One skill covers the whole Mergify CLI surface. Pick the scenario below; each file is self-contained for that command group. Do not invent Mergify config or CLI behavior from memory — fetch the docs links inside the scenario file when writing configuration.

## Shared CLI notes

Most authenticated commands accept:

| Flag / env | Meaning |
|---|---|
| `--token` / `-t` (`MERGIFY_TOKEN`) | Mergify credential from `mergify auth login`, or a GitHub token (deprecated for the Mergify API) |
| `--repository` / `-r` | `owner/repo` (often auto-detected from git remote or CI) |
| `--api-url` / `-u` (`MERGIFY_API_URL`) | Default `https://api.mergify.com` |

CI Insights uses a different key split (`ci` vs `admin` application keys). See [ci.md](references/ci.md).

## Routing table

| Scenario | Use when | Reference |
|---|---|---|
| **Stacked PRs** | `git push`, commits, branches, PR create/update, rebase/fixup/squash/reword, amend notes, GitHub-native stacks | [stack.md](references/stack.md) |
| **Merge queue** | Queue/dequeue via PR comments, `mergify queue status/show/pause/unpause`, diagnosing a dequeued PR, dequeue codes | [merge-queue.md](references/merge-queue.md) |
| **Merge protections** | `Depends-On:` / `Merge-After:` headers, scheduled freezes (`mergify freeze`), deployment windows | [merge-protections.md](references/merge-protections.md) |
| **CI Insights** | `mergify ci` (JUnit process/upload, git-refs, scopes, queue-info), `mergify tests` (show, quarantines) | [ci.md](references/ci.md) |
| **Configuration** | Validate, simulate, write or edit `.mergify.yml` / Mergify config | [config.md](references/config.md) |
| **Activity log** | `mergify events` — timeline of what Mergify did to a repo or PR | [events.md](references/events.md) |

## Decision shortcuts

- Pushing or rewriting commits on a stacked PR → [stack.md](references/stack.md). Prefer `mergify stack *` over `git push` / `git rebase -i` / `gh pr edit`.
- "Why did my PR leave the queue?" → [merge-queue.md](references/merge-queue.md) (`mergify queue show`). Full multi-event trail → [events.md](references/events.md).
- Block a PR until another PR merges, or until a time → [merge-protections.md](references/merge-protections.md). Stack tooling adds `Depends-On` between stack members automatically.
- Upload JUnit, quarantine flaky tests, selective CI scopes → [ci.md](references/ci.md).
- Change what Mergify does (rules, conditions, actions) → [config.md](references/config.md).
