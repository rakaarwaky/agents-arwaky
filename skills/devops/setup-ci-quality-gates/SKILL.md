---
name: setup-ci-quality-gates
description: "Set up CI quality gates and architecture checks on GitHub Actions. Use when creating workflows, branch protection rulesets, auto-merge, or AI review layers."
when-to-use: "Use when replicating this repo's CI setup: ci.yml jobs, branch-protection ruleset, auto-merge workflow, AI review layers (CodeRabbit, Codacy, cubic, Repowise), and local scripts/ci.sh."
argument-hint: "[<repo-root>]"
metadata:
  tags:
    - ci
    - github-actions
    - quality-gates
    - code-review
    - coderabbit
    - codacy
    - cubic
    - repowise
    - rust
    - python
    - typescript
    - self-lint
    - architecture
    - aes
  related_skills:
    - local-ci
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
---

# CI Quality Gates System

Replicate the CI setup used by this repo: quality gates enforced by GitHub
Actions + a branch-protection ruleset, architecture enforcement via the
project's own linter (self-lint), and four AI review layers (CodeRabbit,
Codacy, cubic, Repowise). This is a copy-and-extend blueprint, not a
one-off checklist — adapt names and paths to the target repo.

**Language-agnostic.** The pattern (quality gates → branch protection →
AI review) applies to any language. The commands below are this repo's
Rust flavor; substitute per language:

| Concern | Rust | Python | TypeScript/JS |
|---|---|---|---|
| Format | `cargo fmt --check` | `ruff format --check` | `prettier --check` |
| Lint | `cargo clippy -D warnings` | `ruff check` + `mypy` | `eslint` + `tsc --noEmit` |
| Tests | `cargo nextest run` | `pytest` | `vitest` / `jest` |
| Security deps | `cargo audit` | `bandit` + `pip-audit` | `npm audit` / `eslint-plugin-security` |
| Build | `cargo build --release` | `python -m build` | `tsc` / `vite build` |

The self-lint job is the one part that is inherently project-specific: it
runs **this** linter (`lint-arwaky-cli`) on the repo's own multi-language
workspace (`crates/`, `modules/`, `packages/`).

## Architecture overview

```text
PR opened / pushed
   │
   ├─ CI workflow (.github/workflows/ci.yml)
   │    ├─ Format  (cargo fmt --check)
   │    ├─ Clippy  (cargo clippy -D warnings)
   │    ├─ Build   (cargo build --release)
   │    ├─ Tests   (cargo nextest run)
   │    └─ Self-Lint (lint-arwaky-cli check .  == 0 violations)
   │
   ├─ Codacy Static Code Analysis (app.codacy.com)
   ├─ CodeRabbit (app.coderabbit.ai) — change review
   ├─ cubic AI reviewer (www.cubic.dev) — ultrareview
   └─ Repowise bot (.repowise/bot.yaml) — health gate advisory
   │
   └─ Ruleset "Protect main" (GitHub rulesets)
        ├─ required_status_checks: Format, Clippy, Build, Tests,
        │    Self-Lint, Codacy Static Code Analysis
        ├─ strict: true (must be up to date)
        ├─ non_fast_forward + deletion: blocked
        └─ auto-merge workflow (squash) merges when all pass

```text

## 1. GitHub Actions workflow (.github/workflows/ci.yml)

Five jobs on `ubuntu-latest` (Rust flavor shown; see the table at the top
for Python/TypeScript equivalents). Cache with sccache + Swatinem/rust-cache.

| Job | Command | Notes |
|---|---|---|
| `fmt` | `cargo fmt --all -- --check` | rustfmt component only |
| `clippy` | `cargo clippy --all-targets -- -D warnings` | clippy component; install `mold` linker |
| `build` | `cargo build --release` | needs: build for downstream |
| `test` | `cargo nextest run --workspace --lib --tests -j 2` | needs: build; install nextest via curl |
| `self-lint` | `lint-arwaky-cli check .` == 0 violations | needs: build; also assert ≥24 AES codes on `workspaces-bad` |

Key env in `.github/workflows/ci.yml`: `RUSTC_WRAPPER=sccache`,
`CARGO_BUILD_JOBS=4`, `RUST_MIN_STACK=33554432`. (`CARGO_INCREMENTAL=0`
belongs in `scripts/ci.sh` for local runs, not in the workflow.)

### Self-lint job (architecture enforcement)

This is the differentiator: the repo lints **itself** with its own
architecture rules (AES 7-layer system). CI fails if the codebase violates
its own rules. The `self-lint` job runs two checks: zero violations on the
whole repo, and the AES rule engine still fires all 24 codes on the
intentional-violation fixture workspace (`workspaces-bad`) — the second
check catches a linter that silently stops detecting anything:

```bash
# 1. Whole-repo self-lint must be clean (exit code is authoritative;
#    the parsed count is only for the log line).
set -e
output=$(./target/release/lint-arwaky-cli check . 2>&1) || { echo "$output"; exit 1; }
violations=$(echo "$output" | grep -oP 'Total:\s*\K\d+' || echo "0")
echo "Violations: ${violations}"
[ "${violations}" = "0" ]

# 2. AES codes still fire on the bad workspace (≥24 unique AES codes).
codes=$(./target/release/lint-arwaky-cli scan workspaces-bad 2>&1 \
  | grep -oP "AES\d+" | sort -u | wc -l)
echo "Unique codes: ${codes:-0}"
[ "${codes:-0}" -ge 24 ]

```text

Use `cargo build --release` (or `--bin lint-arwaky-cli`) before these
steps so the binary exists under `./target/release/`.

## 2. Branch protection: GitHub Ruleset

Create a ruleset "Protect main - quality gates" (Settings → Rules →
Rulesets), `target: branch`, enforcement `active`:

- **required_status_checks**: Format, Clippy, Build, Tests, Self-Lint,
  Codacy Static Code Analysis — with `strict: true` (requires up-to-date).
- **non_fast_forward**: blocked.
- **deletion**: blocked.

Effect: no direct push to `main`; every change must go through a PR that
passes all gates. (This is why all work here uses worktrees + PRs.)

## 3. Auto-merge (.github/workflows/auto-merge.yml)

See `references/auto-merge.yml.md` for the squash-merge workflow and
PR-metadata env-var rules.

## 4. AI review layers

See `references/ai-review-layers.md` for CodeRabbit, Codacy, cubic, and
Repowise configuration.

## 5. Local quality gates (scripts/ci.sh)

Reproduce CI locally before pushing — the pre-push hook runs the same
gates (Rust flavor; swap commands per language from the table at the top):

```bash
bash scripts/ci.sh               # fmt + clippy + self-lint + AES codes + tests
CARGO_INCREMENTAL=0 cargo clippy --workspace --all-targets -- -D warnings
cargo nextest run --workspace --lib --tests
lint-arwaky-cli check .        # whole repo, must be 0 violations
```

`scripts/ci.sh` should also accept `--container` and run the identical gates
inside a Podman/Docker image where every dependency, browser, and the linter
are baked in. That removes the hosted-runner quota as a merge dependency.
See the `local-ci` skill for the script structure, container image design,
and the version-drift pitfall that makes local runs disagree with CI.

## 6. Supporting workflows

| Workflow | Purpose |
|---|---|
| `release.yml` | Build release binaries, smoke-test, attest-build-provenance |
| `release-tag.yml` | Tag release PRs |
| `auto-release.yml` | Release on workflow_run after merge |
| `cleanup-branches.yml` | Delete merged branches |
| `labeler.yml` | Auto-label PRs (uses actions/labeler) |

## Checklist — replicate on a new repo

- [ ] `.github/workflows/ci.yml` with fmt/clippy/build/test/self-lint jobs
- [ ] Self-lint job runs the project's own linter, fails on violations
- [ ] Ruleset on `main`: required status checks + strict + no fast-forward
- [ ] Auto-merge workflow (squash) gated on the same checks
- [ ] CodeRabbit + Codacy + cubic apps installed on the repo
- [ ] `.codacy.yaml` excludes fixtures; Codacy in required checks
- [ ] `.repowise/bot.yaml` + `.repowiseIgnore` + `health-rules.json`
- [ ] `scripts/ci.sh` mirrors CI for local run + pre-push hook (see `local-ci`)
- [ ] Release/labeler/cleanup workflows if the release train is needed
