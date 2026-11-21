# Setup step 1 — Pre-setup & Issue Tracker Audit (setup lane)

Audit the repository's issue tracking setup, labels, and issue templates before automating issue resolution.

## Step 1.1 — Inspect repository issue templates

Check if the repository has existing issue templates:

```bash
gh api repos/<owner/repo>/contents/.github/ISSUE_TEMPLATE 2>/dev/null || true
```

If issue templates exist, inspect the template fields (e.g., bug report format, reproduction steps, expected vs actual behavior).
If no issue templates exist, templates from `templates/bug-report.md` and `templates/feature-request.md` in this skill can be offered.

## Step 1.2 — Audit existing labels

Inspect all existing repository labels:

```bash
gh label list --repo <owner/repo> --limit 100 --json name,color,description
```

Check for standard labels needed by the issue triage and worker lifecycle:
- `bug`
- `enhancement`
- `triage`
- `in-progress`
- `fixed-on-main`
- `wontfix`

## Step 1.3 — Check repository permission

Verify that the active user has write or triage permission on the repository to edit labels and assignees:

```bash
gh api repos/<owner/repo>/collaborators/$(gh api user --jq .login)/permission --jq .permission
```

Permissions `admin`, `write`, or `triage` allow label assignment and issue status management. If read-only, report permission limits to the owner.

## Next

Proceed to [step-2-setup-labels.md](step-2-setup-labels.md) to ensure all required labels exist.
