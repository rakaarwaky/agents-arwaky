---
name: github-workflow
description: "Umbrella for GitHub auth, repo management, issues, PRs, Mergify, and releases. Subsumes github-auth and repo-manager."
when-to-use: "Use for any GitHub task: auth setup (gh CLI or git-only), repo clone/create/fork/configure, issue-to-PR pipeline, PR watch/fix/merge, Mergify stacked PRs and merge queue, release prep and publish, recovery of failed release runs. This skill now includes the auth helper scripts (gh-env.sh, git-credential-token.py) formerly in github-auth."
argument-hint: "<auth | repo | issue | pr | mergify | release> <subcommand> [flags]"
---

# GitHub Workflow

One umbrella for GitHub repository and PR lifecycle work. Split by job: auth, repo management, issue-to-PR, PR babysitting, Mergify, releasing. The Global Rules govern every job.

## Global Rules

- **Auth prerequisite:** Authenticated with GitHub first (auth job). Source `gh-env.sh` for auth and repo detection rather than re-implementing the fallback chain.
- **Prefer `gh`:** Use `gh` commands; fall back to `git` + `curl` only where `gh` lacks coverage.
- **Lane is determined by physical signal, not self-identification.** `HERMES_AGENT=1` → Hermes lane; `GROK_AGENT=1` → Grok lane; unset → stop and report. Never guess.
- **Takes EXISTING issues to PRs; does not create issues.** Issue creation is a separate job.
- **Never merges automatically unless `--ship` is active and ship-ready gates pass on a live re-query.**
- **CI must run green on the release branch before merge; tag created only on the merge commit.** Never bump version directly to main or push a tag outside the prep PR flow.

## Jobs (labeled subsections)

### 1. Auth — GitHub authentication setup
HTTPS tokens, SSH keys, `gh` CLI login (browser and device flow). Run `git --version`, `gh --version`, `gh auth status`, `git config --global credential.helper` before choosing a path.

- **gh authenticated:** use `gh` for everything.
- **gh installed but not authenticated:** `gh auth login` (browser or device flow).
- **gh not installed:** git-only method (HTTPS PAT or SSH key, no sudo needed).
- **Token scopes:** `repo`, `workflow`, `read:org` (90-day expiration recommended).
- **Git identity:** configure `user.name` and `user.email`; required for commits.

Auth helper scripts live in `scripts/`: `gh-env.sh` (auth + repo detection, exports `GH_AUTH_METHOD`, `GITHUB_TOKEN`, `GH_OWNER_REPO`, etc.) and `git-credential-token.py` (extracts a token from the git credential store). Source `gh-env.sh` rather than re-implementing the fallback chain.

### 2. Repo — clone, create, fork, configure
Clone/create/fork repos; manage remotes, releases, settings, secrets, Actions CI via `gh`.

- **Clone:** `git clone <url>` and `gh repo clone owner/repo` (HTTPS, SSH, shallow, branch).
- **Create:** `gh repo create NAME --public|--private --clone` (user, org, template).
- **Fork:** `gh repo fork owner/repo --clone`, then `gh repo sync` to keep in sync.
- **Settings:** `gh repo edit` (description, visibility, topics, default branch) + branch protection REST.
- **Actions & releases:** `gh workflow` / `gh run` / `gh secret` / `gh release`.
- **.gitignore:** three-way diff (tracked / untracked / on-disk) + `git check-ignore -v` to find gaps.
- **Info:** `gh repo view`, `gh repo list`, `gh search repos`.

### 3. Issue — issue to PR
Analyze open GitHub issues and take each from backlog to a PR opened to main. Verify at HEAD, run the decision quiz, 1 issue → 1 Orca worktree → Grok Build implements → Hermes verifies → Hermes pushes branch + opens a (draft) PR to main → close/reopen per result. Never merges.

- **Verify at HEAD** per issue; ask the decision quiz.
- **Spawn one Grok worktree per still-broken issue** and drop the brief.
- **Wait** for each Grok session; verify commits, code, re-run symptom repro.
- **Push** each verified branch, open one draft PR per issue.
- **Close verified-on-main issues** with evidence; rebase still-open branches.

### 4. PR — watch and babysit
Watch a standalone GitHub PR end to end: register it, keep it green, merge it when `--ship` is active. Event-driven — CI re-runs and new review threads trigger fresh passes.

- **Register** the PR, fetch it, check CI once.
- **If red or open threads:** spawn a Grok worktree on the head branch and drop the fix brief.
- **Wait** for the fix pass; re-run CI on the live head SHA.
- **Merge** only when `ship` is true and ship-ready gates pass.

### 5. Mergify — stacked PRs, merge queue, CI
Mergify CLI surface: `git push`, commits, branches, PR create/update, rebase/fixup/squash/reword. Queue/dequeue via PR comments; diagnose dequeued PRs. `Depends-On:` / `Merge-After:` headers, scheduled freezes. CI Insights (JUnit upload, quarantines, scopes). Validate `.mergify.yml`. Browse Mergify events.

- **Prefer `mergify stack *`** over `git push` / `git rebase -i` / `gh pr edit`.
- **Credential auth:** `--token` / `--repository` (`MERGIFY_TOKEN`, `MERGIFY_API_URL` default `https://api.mergify.com`).
- **CI Insights keys:** different key split (`ci` vs `admin` application keys).

### 6. Release — cut a release
Cut a CalVer release of the mergify CLI autonomously: bump via bump script, open and merge release prep PR, build and publish draft through GitHub workflows, recover failed release runs.

- **Repo guard:** confirm `git remote -v` is `Mergifyio/mergify-cli` and CalVer scheme (`YYYY.M.D.N`) targeting PyPI + Homebrew.
- **Prep PR mandatory:** CI must run green on release branch before merge; tag created only on merge commit.
- **Never `gh release create` or push a tag by hand.** A release outside the workflow has no binaries.
- **Step 4 (Publish) is irreversible:** locks the release and pushes to PyPI.

## References

| Topic | File | Purpose |
|-------|------|---------|
| Auth detect | `references/step-0-detect.md` | Check git, gh, auth status; choose git-only or gh-cli path. |
| Auth gh-cli | `references/step-1-gh-cli-auth.md` | `gh` login: browser, device flow, hosts.yml fallback. |
| Auth git-only | `references/step-2-git-only-auth.md` | HTTPS PAT or SSH key setup. |
| Clone | `references/clone.md` | `git clone` and `gh repo clone`. |
| Create | `references/create.md` | `gh repo create`. |
| Fork | `references/fork.md` | `gh repo fork` and sync. |
| Settings | `references/setting.md` | `gh repo edit` + branch protection. |
| Actions | `references/action.md` | `gh workflow` / `gh run` / `gh secret` / `gh release`. |
| Gitignore | `references/gitignore-audit.md` | Three-way diff + `git check-ignore -v`. |
| Info | `references/info.md` | `gh repo view` / `gh repo list` / `gh search repos`. |
| Issue triage | `references/hermes/step-0-triage-and-spawn.md` | Verify at HEAD, decision quiz, spawn worktree. |
| Issue verify | `references/hermes/step-1-wait-and-verify.md` | Wait for Grok, verify commits and repro. |
| Issue ship | `references/hermes/step-2-ship-and-close.md` | Push branch, open draft PR, close/reopen issues. |
| Issue report | `references/hermes/step-3-final-report.md` | Final report: verdicts, PRs, closed issues. |
| PR watch | `references/hermes/step-0-watch-and-spawn.md` | Verify auth, fetch PR, register, check CI. |
| PR reverify | `references/hermes/step-1-wait-and-reverify.md` | Wait for fix pass, re-run CI. |
| PR merge | `references/hermes/step-2-merge.md` | Merge when ship-ready gates pass. |
| PR report | `references/hermes/step-3-final-report.md` | Final report to user. |
| Mergify stack | `references/stack.md` | Stacked PRs via `mergify stack *`. |
| Mergify queue | `references/merge-queue.md` | Queue/dequeue, diagnose dequeued PRs. |
| Mergify protections | `references/merge-protections.md` | Depends-On, Merge-After, freezes. |
| Mergify CI | `references/ci.md` | JUnit upload, quarantines, scopes. |
| Mergify config | `references/config.md` | Validate, simulate, write `.mergify.yml`. |
| Mergify events | `references/events.md` | Timeline of Mergify actions. |
| Release bump | `references/step-0-version-bump.md` | Version bump and changelog generation. |
| Release prep | `references/step-1-prep-pr.md` | Release prep PR: branch, CI green, merge. |
| Release preflight | `references/step-2-preflight.md` | Verify main clean, report what ships. |
| Release build | `references/step-3-build-draft.md` | Trigger release.yml, verify seven assets. |
| Release publish | `references/step-4-publish.md` | Publish draft, confirm PyPI + Homebrew. |
| Release verify | `references/step-5-verify.md` | Verify after publishing. |
