---
name: setup-ci-quality-gates
description: "Set up CI quality gates and architecture checks on GitHub Actions, and reproduce those gates locally via a ci.sh mirror. Use when creating workflows, branch protection rulesets, auto-merge, AI review layers, or building scripts/ci.sh to mirror .github/workflows when GitHub Actions is quota-blocked."
when-to-use: "Use when replicating this repo's CI setup: ci.yml jobs, branch-protection ruleset, auto-merge workflow, AI review layers (CodeRabbit, Codacy, cubic, Repowise), local scripts/ci.sh that mirrors the remote workflow, or running the same CI gates locally in a container when GitHub Actions is quota/billing-blocked."
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
The full local-mirror procedure (script structure, container image design,
runtime verification, and the version-drift pitfall that makes local runs
disagree with CI) is folded in below as **Local half — reproducing the gates
locally (merged from the former `local-ci` skill)**.

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
- [ ] `scripts/ci.sh` mirrors CI for local run + pre-push hook (see the Local half section below)
- [ ] Release/labeler/cleanup workflows if the release train is needed

---

## Local half — reproducing the gates locally (merged from the former `local-ci` skill)

### Local CI Gates

Build a local script that runs the same gates as `.github/workflows/`, so
CI is reproducible without a network round-trip and merge is not blocked by a
hosted-runner quota, a billing block, or an outage. The remote workflow stays
the source of truth; the local script is a mirror of it.


## Architecture overview

```text
.github/workflows/ci.yml          # source of truth
        │
        │  same commands, two runtimes
        ▼
┌──────────────────────────┬────────────────────────────────────┐
│ scripts/ci.sh (host)     │ scripts/ci.sh --container         │
│ uv/venv on the machine   │ container with everything baked in │
│ ~2 min, no setup         │ ~1 min warm, 0 downloads          │
│ fails on missing dep     │ fails on missing browser          │
└──────────────────────────┴────────────────────────────────────┘
```

Both paths call the same `run_gate` helper and print the same pass/fail
lines, so a green local run predicts a green remote run.

## When to use

- GitHub Actions refuses to start jobs: billing block, spending limit, quota
  exhausted. The annotation reads *"The job was not started because recent
  account payments have failed or your spending limit needs to be
  increased."* Jobs show `steps=0` and an empty `runner_name` — proof the
  runner was never allocated, not that the code failed.
- You want merge to stop depending on a hosted runner at all.
- A self-hosted runner is the alternative: it also removes the quota, but
  costs a VM and keeps the workflow YAML as the only definition. A local
  script is cheaper and makes the gates readable.

Do not use this to skip gates. The script runs the same checks; it only
removes the network dependency.

## 1. Inventory the remote gates first

Read the workflow and copy the commands verbatim. Do not paraphrase.

```bash
grep -nE "^  [a-z0-9-]+:$|    name:|      - name:" .github/workflows/ci.yml
```

For qwen-web-arwaky the seven gates are: Format, Lint (ruff + mypy), Build,
Tests (pytest), Self-Lint, template hygiene, and Bandit. Copy the pytest
invocation's **full path list** — CI usually lists thirteen test directories,
and a local script that only runs `tests/` silently skips modules.

A local-only gate worth adding: security scan with tests excluded. Running
Bandit across `modules/` including test files reports thousands of `B101`
(assert) findings and buries the real ones.

```bash
bandit -r modules/ -x '*/tests/*,*/test/*' --severity-level medium --confidence-level medium
```

## 2. Write the script with a gate helper

Structure: a `run_gate` helper that captures output to a log, prints the
last lines on failure, and counts failures without aborting — so one broken
gate still lets the others report.

```bash
#!/usr/bin/env bash
set -euo pipefail

FAILURES=0
run_gate() {
    local name="$1"; shift
    info "Gate: ${name}"
    if "$@" >"/tmp/ci_${name// /_}.log" 2>&1; then
        ok "${name} passed"
    else
        warn "${name} failed (last lines:)"
        tail -8 "/tmp/ci_${name// /_}.log" || true
        FAILURES=$((FAILURES + 1))
    fi
}
```

Exit non-zero when `FAILURES > 0`, so a pre-push hook can call it.

## 3. Make the two runtimes explicit

Detect whether the script is running inside the container rather than
threading a flag through every gate. The container has its venv at
`/opt/venv` and its package installed, so host-mode setup work must be
skipped.

```bash
IN_CONTAINER=0
if [[ -d /opt/venv && -f /opt/venv/bin/<entrypoint> ]]; then
    IN_CONTAINER=1
fi

if [[ "${IN_CONTAINER}" -eq 0 ]]; then
    command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
    uv sync --no-dev
fi
```

The dispatch that reaches the container:

```bash
if [[ "${1:-}" == "--container" ]]; then
    podman ps --format '{{.Names}}' | grep -q '^<container>' \
        || fail "container '<container>' is not running"
    podman exec <container> bash /root/src/scripts/ci.sh
    exit $?
fi
```

The exec path runs the same file with no flag, so container mode falls
through to the shared gate body. Mount the source tree read-write — pytest
fixtures and tool caches write into the tree, and a `:ro` mount turns
`uv sync` into `Read-only file system (os error 30)`.

```bash
VOLUMES="-v ${REPO_ROOT}:/root/src:Z \
         -v ${VOLUME_DIR}/share:/root/.local/share/<app>:Z \
         -v ${VOLUME_DIR}/state:/root/.local/state/<app>:Z \
         -v ${VOLUME_DIR}/config:/root/.config/<app>:Z"
```

## 4. Container image: bake once, run many times

See `references/container-image.md` for base-image slimming, browser
download via `curl`, marker files, prebuilt CLI pinning, glibc base
choice, and `tini` as PID 1.

## 5. Verify both runtimes before trusting either

See `references/verify-runtimes.md` for the host/container verification
commands and the browser-launch proof.

## Pitfalls

- **Linter version drift.** Pin the local binary to the version the workflow downloads.
- **Read-only source mount.** Mount `:Z` without `:ro`.
- **`ENTRYPOINT` shadowing.** Use `--entrypoint` to reach a shell.
- **`podman exec --entrypoint` is not a flag.** Only the command after the container name matters.
- **Exit code from the count, not the parser.** Trust the linter's own exit code.
- **Skipped test directories.** Copy the full path list from the workflow.
- **Bandit vs tests.** Exclude test dirs, gate on medium severity.

## Checklist — add local CI to a repo

- [ ] Read `.github/workflows/ci.yml`; list every job and its exact command
- [ ] `scripts/ci.sh` with a `run_gate` helper; exits non-zero on failure
- [ ] `IN_CONTAINER` detection skips host setup inside the container
- [ ] `--container` flag dispatches through `podman exec` to the same file
- [ ] Source tree mounted read-write at a known path inside the container
- [ ] `Containerfile` bakes deps, browsers, and the linter at CI's version
- [ ] Both runtimes green; browser launch verified, not assumed
- [ ] Security scan excludes tests and gates on medium severity
- [ ] Remote workflow untouched — the script mirrors it, it does not replace it
