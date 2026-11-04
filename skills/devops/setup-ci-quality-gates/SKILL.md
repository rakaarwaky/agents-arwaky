---
name: setup-ci-quality-gates
description: "Set up CI quality gates and architecture checks on GitHub Actions, and reproduce those gates locally via a ci.sh mirror. Use when creating workflows, branch protection rulesets, auto-merge, AI review layers, or building scripts/ci.sh to mirror .github/workflows when GitHub Actions is quota-blocked."
when-to-use: "Use when replicating this repo's CI setup: ci.yml jobs, branch-protection ruleset, auto-merge workflow, AI review layers (cubic, Repowise), local scripts/ci.sh that mirrors the remote workflow, or running the same CI gates locally in a container when GitHub Actions is quota/billing-blocked."
argument-hint: "[<repo-root>]"
metadata:
  tags:
    - ci
    - github-actions
    - quality-gates
    - code-review
    - cubic
    - repowise
    - rust
    - python
    - typescript
    - self-lint
    - architecture
    - aes
  related_skills:
    - lint-arwaky
    - add-docs
    - testing-suite
  triggers:
    - setup ci
    - quality gates
    - ci pipeline
    - code review bot
    - architecture enforcement
    - replicate ci
    - branch protection
    - self-lint
    - local ci
    - run ci locally
    - ci.sh
    - mirror workflow
    - reproduce gates
    - offline ci
    - self-hosted runner
---

# CI Quality Gates System

Replicate the CI setup used by this repo: quality gates enforced by
GitHub Actions + a branch-protection ruleset, architecture enforcement
via the project's own linter (self-lint), and two AI review layers
(cubic, Repowise). This is a copy-and-extend blueprint, not a
one-off checklist — adapt names and paths to the target repo.

## Global Rules

- **The remote workflow is the source of truth; local runs mirror it.**
  `scripts/ci.sh` runs the same commands verbatim; it never replaces
  or weakens the remote gates.
- **Substitute per language from the gate table.** The pattern
  (quality gates → branch protection → AI review) is language-agnostic;
  the commands below are this repo's Rust flavor.

| Concern | Rust | Python | TypeScript/JS |
|---|---|---|---|
| Format | `cargo fmt --check` | `ruff format --check` | `prettier --check` |
| Lint | `cargo clippy -D warnings` | `ruff check` + `mypy` | `eslint` + `tsc --noEmit` |
| Tests | `cargo nextest run` | `pytest` | `vitest` / `jest` |
| Security deps | `cargo audit` | `bandit` + `pip-audit` | `npm audit` / `eslint-plugin-security` |
| Build | `cargo build --release` | `python -m build` | `tsc` / `vite build` |

The self-lint job is the one part that is inherently
project-specific: it runs **this** linter (`lint-arwaky-cli`) on the
repo's own multi-language workspace (`crates/`, `modules/`,
`packages/`).

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| CI workflow | [`references/ci-workflow.md`](references/ci-workflow.md) | The five `ci.yml` jobs (Rust flavor), cache env, the self-lint job, and the supporting release/tag/cleanup/labeler workflows. |
| Self-lint job | [`references/self-lint.md`](references/self-lint.md) | The exit-code-authoritative self-lint script, the ≥24 AES-code fixture assertion, and the `cargo build --release` prerequisite. |
| Branch protection | [`references/branch-protection.md`](references/branch-protection.md) | The "Protect main - quality gates" ruleset with strict + push blocks. |
| Auto-merge | [`references/auto-merge.yml.md`](references/auto-merge.yml.md) | The squash-merge workflow and the PR-metadata env-var injection rule. |
| AI review layers | [`references/ai-review-layers.md`](references/ai-review-layers.md) | cubic ultrareview and Repowise health-gate config, plus fixture exclusion. |
| Local CI | [`references/local-ci.md`](references/local-ci.md) | `scripts/ci.sh` gate helper, two-runtimes dispatch, pitfalls, and the local-CI checklist. |
| Container image | [`references/container-image.md`](references/container-image.md) | Base slimming, `curl` browser download with marker files, CLI version pinning, glibc choice, `tini` PID 1. |
| Verify runtimes | [`references/verify-runtimes.md`](references/verify-runtimes.md) | The host + container gate runs and the browser-launch proof. |
