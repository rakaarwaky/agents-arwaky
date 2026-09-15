---
name: github-repo-management
description: Clone/create/fork repos; manage remotes, releases.
metadata:
  hermes:
    tags: [GitHub, Repositories, Git, Releases, Secrets, Configuration]
    related_skills: [github-auth, github-pr-workflow, github-issues]
---
# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Prefer `gh`; fall back to `git` + `curl` (details in references/).

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)

### Setup

Auth, username, and repo detection all live in `github-auth`'s helper — source it
rather than re-implementing the fallback chain (it also resolves from `~/.qwen`,
`~/.hermes`, or `~/.config/opencode` roots):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
[ "$AUTH" = "none" ] && echo "Not authenticated — resolve it with the github-auth skill first"
```

---

## Workflow Checklist

1. **Clone** — `gh repo clone owner/repo` (or `git clone <url>`).
   Details: [references/repos-clone-create-fork.md](references/repos-clone-create-fork.md#1-cloning-repositories)
2. **Create** — `gh repo create NAME --public|--private --clone`.
   Details: [references/repos-clone-create-fork.md](references/repos-clone-create-fork.md#2-creating-repositories)
3. **Fork + sync** — `gh repo fork owner/repo --clone`, then `gh repo sync`.
   Details: [references/repos-clone-create-fork.md](references/repos-clone-create-fork.md#3-forking-repositories)
4. **Repo info** — `gh repo view`, `gh repo list`, `gh search repos`.
   Details: [references/repos-info-settings.md](references/repos-info-settings.md#4-repository-information)
5. **Settings** — `gh repo edit --description ... --visibility ...`.
   Details: [references/repos-info-settings.md](references/repos-info-settings.md#5-repository-settings)
6. **Branch protection** — read current, then `PUT .../branches/main/protection`.
   Details: [references/repos-info-settings.md](references/repos-info-settings.md#6-branch-protection)
7. **Secrets** — `gh secret set KEY` (curl fallback needs NaCl encryption).
   Details: [references/repos-secrets-releases-actions.md](references/repos-secrets-releases-actions.md#7-secrets-management-github-actions)
8. **Releases** — `gh release create v1.0.0 --generate-notes`.
   Details: [references/repos-secrets-releases-actions.md](references/repos-secrets-releases-actions.md#8-releases)
9. **Actions CI** — `gh workflow list`, `gh run list/view/rerun`.
   Details: [references/repos-secrets-releases-actions.md](references/repos-secrets-releases-actions.md#9-github-actions-workflows)
10. **Gists** — `gh gist create`, `gh gist list`.
    Details: [references/repos-gists-cleanup.md](references/repos-gists-cleanup.md#10-gists)
11. **Clean a dirty backup repo** — diagnose mode-bit noise first (`core.fileMode false`), then classify JUNK/SECRET/KEEP, untrack with `git rm --cached`.
    Details: [references/repos-gists-cleanup.md](references/repos-gists-cleanup.md#11-cleaning-an-over-tracked--dirty-backup-repo)

## Quick Reference Table

| Action | gh |
|--------|-----|
| Clone | `gh repo clone o/r` |
| Create repo | `gh repo create name --public` |
| Fork | `gh repo fork o/r --clone` |
| Repo info | `gh repo view o/r` |
| Edit settings | `gh repo edit --...` |
| Create release | `gh release create v1.0` |
| List workflows | `gh workflow list` |
| Rerun CI | `gh run rerun ID` |
| Set secret | `gh secret set KEY` |

## References

| File | Read it when |
|------|--------------|
| `references/repos-clone-create-fork.md` | Clone/create/fork repos, including the `git` + `curl` fallbacks |
| `references/repos-info-settings.md` | Repo info, settings, topics, branch protection endpoints |
| `references/repos-secrets-releases-actions.md` | Secrets encryption, releases, Actions workflows via API |
| `references/repos-gists-cleanup.md` | Gists and the dirty-backup-repo cleanup procedure |
| `references/github-api-cheatsheet.md` | Raw REST endpoint cheatsheet (settings, topics, releases, dispatch, secrets) |
