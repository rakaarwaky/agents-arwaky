# Step 3 — Setup Mergify (setup lane)

Write `.github/mergify.yml` from the template, using the repo facts
and customization answers from step 1 and the CI check names from step 2.

This step writes and commits the config in the worktree. It does NOT open the
pull request — that is step 4.

## Template reference

The authoritative template is [`templates/mergify.yml`](../../../templates/mergify.yml).
Use that file as the source for all YAML structure, placeholders, and
customization rules. Do not inline or duplicate it here.

## Detect Mergify

Check in this order (stop at first positive):

### 1. Config file in the worktree

```bash
for f in .mergify.yml .mergify.yaml .mergify/config.yml .mergify/config.yaml .github/mergify.yml .github/mergify.yaml; do
  if [ -f "$f" ]; then
    MERGIFY_CONFIG="$f"
    MERGIFY_AVAILABLE="configured"
    break
  fi
done
```

### 2. Mergify check-runs on the PR

```bash
SHA=$(gh pr view <number> --json headRefOid -q .headRefOid)
gh api "repos/$OWNER_REPO/commits/$SHA/check-runs" \
  -q '.check_runs[] | select(.app.slug == "mergify") | .name' 2>/dev/null | head -1
```

Non-empty result → `MERGIFY_AVAILABLE="installed"` (app installed, no local config).

### 3. Default

No config, no check-runs → `MERGIFY_AVAILABLE="none"`.

If Mergify is already `configured`, report it and skip to the report below —
no new file, no PR.

## Ask the user (when `"none"` or `"installed"`)

> PR <number> targets a repo without Mergify merge-queue configuration.
> To use Mergify auto-merge, I'll add a `.github/mergify.yml` with a merge-queue rule
> modeled on the lint-arwaky role model, customized for this repo.
> Proceed?

If declined, set `MERGIFY_AVAILABLE="declined"` and stop.

## Write `.github/mergify.yml`

Before writing the new config, check for and remove any old Mergify config
locations that would cause Mergify to detect **multiple configurations** and
refuse to run:

| Old location | Action |
|--------------|--------|
| `.mergify.yml` (repository root) | Delete |
| `.mergify.yaml` (repository root) | Delete |
| `.github/workflows/mergify.yml` | Delete (Mergify never reads it; GitHub Actions treats it as invalid) |

```bash
for f in .mergify.yml .mergify.yaml .github/workflows/mergify.yml; do
  if [ -f "$f" ]; then
    git rm -f "$f"
    echo "Removed old Mergify config: $f"
  fi
done
```

Then substitute all `<...>` placeholders with values from step 1 (presetup) and
step 2 (CI check names):

| Placeholder | Source | Default |
|-------------|--------|---------|
| `<BASE_BRANCH>` | step 1 `BASE_BRANCH` | detected default branch |
| `<check-name>` | step 2 CI job names | one `check-success = <name>` per check |
| `<duration>` | step 1 checks timeout | `15min` |
| `<N>` | step 1 max parallel checks | `1` |
| `<merge|rebase>` | step 1 merge method | `squash` |
| `<merge|rebase>` (update_method) | step 1 update method | `merge` |
| `<required_approvals>` | step 1 required approvals | `0` |
| `{% if ... %}` blocks | step 1 yes/no answers | `yes` → include, `no` → omit |

## Validate

```bash
mergify config validate
```

If it fails, fix and retry (max 2 attempts). If still failing, report the error and stop.

Note: `mergify` CLI may not be installed on this host. If so, validate YAML
syntax locally and note that live validation happens on GitHub after the config
PR merges.

## Commit in the worktree

Commit on a dedicated branch. Do not open the pull request here.

```bash
git checkout -b chore/configure-mergify-rules
git add .github/mergify.yml
git commit -m "ci: configure Mergify auto-merge rules"
git push origin chore/configure-mergify-rules
```

## Report to Hermes

> Mergify: configured
> Config file: .github/mergify.yml
> Branch: chore/configure-mergify-rules (pushed)
> Base branch: <BASE_BRANCH>
> CI checks: <comma-separated>
> Rules: CI green + [approvals] + non-draft → merge queue

## Next

Continue to **step 4** (open PR) to open the pull request for this branch with
the `setup` label.