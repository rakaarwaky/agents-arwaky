---
name: repo-manager
description: Clone/create/fork repos; manage remotes, releases, settings, secrets, and Actions CI via gh.
when-to-use: Create, clone, fork, configure, and manage GitHub repositories — remotes, settings, secrets, releases, and Actions CI via gh.
argument-hint: <owner/repo> [--public|--private] [--clone] [--description <text>]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Prefer `gh`; fall back to `git` + `curl` only where `gh` lacks coverage.

## Global Rules

Rules that apply to every repo-manager operation. Reference files cite these; they never restate them.

- **Auth prerequisite**: Authenticated with GitHub first (see `github-auth` skill). Auth, username, and repo detection live in `github-auth`'s helper — source it rather than re-implementing the fallback chain.
- **Prefer `gh`**: Use `gh` commands; fall back to `git` + `curl` only where `gh` lacks coverage.
- **Single source of auth**: Source `gh-env.sh` from `github-auth`; it resolves from `~/.hermes`, `~/.qwen`, `~/.config/opencode`, or `agents-arwaky/skills` roots.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Setup | `github-auth` skill | Source `gh-env.sh` for auth and repo detection (formerly `setup.md`). |
| Clone | [`references/clone.md`](references/clone.md) | `git clone <url>` and `gh repo clone owner/repo` (HTTPS, SSH, shallow, branch). |
| Create | [`references/create.md`](references/create.md) | `gh repo create NAME --public\|--private --clone` (user, org, template). |
| Fork | [`references/fork.md`](references/fork.md) | `gh repo fork owner/repo --clone`, then `gh repo sync` for keeping in sync. |
| Info | [`references/info.md`](references/info.md) | `gh repo view`, `gh repo list`, `gh search repos`. |
| Settings | [`references/setting.md`](references/setting.md) | `gh repo edit` (description, visibility, topics, default branch) + branch protection REST. |
| Actions & releases | [`references/action.md`](references/action.md) | `gh workflow` / `gh run` / `gh secret` / `gh release` (includes NaCl secrets fallback). |
