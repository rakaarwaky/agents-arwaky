---
name: github-auth
description: GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login (browser and device flow).
when-to-use: When gh is not authenticated or git lacks a token — run gh auth login (browser or device flow) or configure a git HTTPS token/SSH key so the agent can push, open PRs, and read issues via gh or git.
argument-hint: <git-only|gh-cli> [--with-token]
---

# GitHub Authentication Setup

This skill sets up authentication so the agent can work with GitHub repositories, PRs, issues, and CI. It covers two paths:

- **`git` (always available)** — uses HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

## Global Rules

Rules that apply to both auth paths. Detection and method files cite these; they never restate them.

- **Detection first**: Run `git --version`, `gh --version`, `gh auth status`, and `git config --global credential.helper` before choosing a path.
- **gh authenticated**: If `gh auth status` shows authenticated → use `gh` for everything.
- **gh not authenticated**: If `gh` is installed but not authenticated → use the `gh auth` method (browser or device flow).
- **gh not installed**: If `gh` is not installed → use the `git-only` method (no sudo needed).
- **Token scopes**: For HTTPS, create a personal access token with `repo`, `workflow`, and `read:org` scopes (90-day expiration recommended).
- **git identity**: Always configure `user.name` and `user.email`; required for commits.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Detection | [`references/detection-flow.md`](references/detection-flow.md) | Check `git`, `gh`, `gh auth status`, credential helper; choose git-only or gh-cli path. |
| Git-only auth | [`references/git-only-auth.md`](references/git-only-auth.md) | HTTPS with personal access token or SSH key: full setup steps for both. |
| gh CLI auth | [`references/gh-cli-auth.md`](references/gh-cli-auth.md) | `gh` login methods: browser, device flow, hosts.yml fallback. |

