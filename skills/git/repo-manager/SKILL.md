---
name: repo-manager
description: Clone/create/fork repos; manage remotes, releases, settings, secrets, and Actions CI via gh.
when-to-use: Create, clone, fork, configure, and manage GitHub repositories — remotes, settings, secrets, releases, and Actions CI via gh.
argument-hint: <owner/repo> [--public|--private] [--clone] [--description <text>]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Prefer `gh`; fall back to `git` + `curl` (details in references/).

## Global Rules

Rules that apply to every repo-manager operation. Reference files cite these; they never restate them.

- **Auth prerequisite**: Authenticated with GitHub first (see `github-auth` skill). Auth, username, and repo detection live in `github-auth`'s helper — source it rather than re-implementing the fallback chain.
- **Prefer `gh`**: Use `gh` commands; fall back to `git` + `curl` only where `gh` lacks coverage.
- **Single source of auth**: Source `gh-env.sh` from `github-auth`; it resolves from `~/.qwen`, `~/.hermes`, `~/.config/opencode`, or `agents-arwaky/skills` roots.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Setup | [`references/setup.md`](references/setup.md) | Source `gh-env.sh` for auth and repo detection before any `gh` call. |
| Clone | [`references/repos-clone-create-fork.md`](references/repos-clone-create-fork.md) | `gh repo clone owner/repo` (or `git clone <url>`). |
| Create | [`references/repos-clone-create-fork.md`](references/repos-clone-create-fork.md) | `gh repo create NAME --public\|--private --clone`. |
| Fork + sync | [`references/repos-clone-create-fork.md`](references/repos-clone-create-fork.md) | `gh repo fork owner/repo --clone`, then `gh repo sync`. |
| Repo info | [`references/repos-info-settings.md`](references/repos-info-settings.md) | `gh repo view`, `gh repo list`, `gh search repos`. |
| Settings | [`references/repos-info-settings.md`](references/repos-info-settings.md) | `gh repo edit --description ... --visibility ...`, topics, branch protection. |
| Secrets | [`references/repos-secrets-releases-actions.md`](references/repos-secrets-releases-actions.md) | `gh secret set KEY` (curl fallback needs NaCl encryption). |
| Releases | [`references/repos-secrets-releases-actions.md`](references/repos-secrets-releases-actions.md) | `gh release create v1.0.0 --generate-notes`. |
| Actions CI | [`references/repos-secrets-releases-actions.md`](references/repos-secrets-releases-actions.md) | `gh workflow list`, `gh run list/view/rerun`. |
| Gists | [`references/repos-gists-cleanup.md`](references/repos-gists-cleanup.md) | `gh gist create`, `gh gist list`. |
| Clean dirty repo | [`references/repos-gists-cleanup.md`](references/repos-gists-cleanup.md) | Diagnose mode-bit noise, classify JUNK/SECRET/KEEP, untrack with `git rm --cached`. |
| Quick reference | [`references/quick-reference.md`](references/quick-reference.md) | One-line `gh` cheatsheet for the common actions. |
| References index | [`references/references-index.md`](references/references-index.md) | Which reference file to read for each scenario. |
