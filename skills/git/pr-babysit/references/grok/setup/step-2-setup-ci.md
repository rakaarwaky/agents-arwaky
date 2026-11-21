# Step 2 — Setup CI (setup lane)

Write `.github/workflows/ci.yml` for the target repo. CI must exist before
Mergify (step 3) because Mergify's queue conditions reference CI check names
via `check-success = <name>`.

## Detect project language

Check for language indicators in the repo root:

```bash
# Rust
if [ -f "Cargo.toml" ]; then
  LANGUAGE="rust"
fi

# Python
if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
  LANGUAGE="python"
fi

# TypeScript
if [ -f "package.json" ]; then
  LANGUAGE="typescript"
fi

# Multi-workspace
if [ -f "Cargo.toml" ] && grep -q "\[workspace\]" Cargo.toml; then
  LANGUAGE="rust-workspace"
fi
```

## Select CI template

Copy the matching block from [`templates/ci.yml`](../../../templates/ci.yml)
(single file, one `{% if %}` block per language):

| Language | Detection | Template block |
|----------|-----------|----------------|
| Rust | `Cargo.toml` | `{% if language == "rust" %}` |
| Python | `pyproject.toml` / `setup.py` / `requirements.txt` | `{% if language == "python" %}` |
| TypeScript | `package.json` | `{% if language == "typescript" %}` |
| Multi-workspace | `Cargo.toml` + `[workspace]` | `{% else %}` block |

The template covers the three languages this skill supports — Rust, Python,
and TypeScript — plus a multi-workspace fallback that detects the language at
run time. A repo whose language is none of the three still gets a working
workflow through the fallback block.

Source template: [`templates/ci.yml`](../../../templates/ci.yml). Substitute
`<BASE_BRANCH>` with the detected default branch and select the one language
block; delete the others.

## Write CI workflow

1. Create `.github/workflows/ci.yml` if it doesn't exist.
2. If it exists, append the selected block to the file.
3. Use the block from `templates/ci.yml` as the base.

### Per-language CI check names (for Mergify step 3)

After writing, record the job names as the CI check names to use in Mergify's
`check-success` conditions:

| Language | Job names |
|----------|-----------|
| Rust | `lint`, `build`, `test` |
| Python | `lint`, `test` |
| TypeScript | `lint`, `build`, `test` |
| Multi-workspace | `lint`, `test` |

## Validate

```bash
# Check YAML syntax
yamllint .github/workflows/ci.yml
```

## Commit and push

```bash
git checkout -b chore/add-ci-workflow
git add .github/workflows/ci.yml
git commit -m "ci: add standard CI workflow for <language>"
git push origin chore/add-ci-workflow
```

Open a pull request from `chore/add-ci-workflow` targeting `<BASE_BRANCH>` so the workflow change is reviewed before landing. Do not push directly to `<BASE_BRANCH>`.

## Verify

```bash
gh run list --limit 5
```

Check that the CI workflow is running.

## Report to Hermes

> CI: configured
> Language: <detected language>
> Workflow: .github/workflows/ci.yml
> Checks: <comma-separated job names>

## Next

Continue to **step 3** (setup Mergify), using the recorded CI check names as
`check-success` conditions in the Mergify queue rules.