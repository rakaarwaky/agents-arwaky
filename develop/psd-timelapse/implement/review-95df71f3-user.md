# User Advocate Review — PSD Timelapse CI/Mergify Standards Remediation

**Reviewer:** Dedicated User Advocate (Ergonomics, Quality of Life & Developer Experience)  
**Date:** 2026-11-21  
**Scope:** `.github/mergify.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `modules/scripting/benches/conftest.py`  
**Reference:** `/home/raka/.agents/develop/psd-timelapse/implement/impl-summary-95df71f3.md`

---

## Executive Summary & Quality of Life Assessment

This review evaluates the implementer's changes strictly through the lens of developer ergonomics, transparency, and friction-free automation:

1. **Zero-friction & Minimal Configuration (Mergify):**  
   - Relocating `.github/workflows/mergify.yml` to `.github/mergify.yml` is a crucial fix; Mergify will now actually discover and process the configuration file.
   - The automated queue configuration for author `rakaarwaky` and automatic branch updates (`keep-prs-up-to-date`) provide a true zero-touch merge experience when CI passes.
   - However, documentation in the header comments directly contradicts the implemented configuration, introducing cognitive friction for maintainers.

2. **Actionable, Friendly Feedback (CI & Release Tagging):**  
   - **Release Workflow:** The hardened version-tag regex in `.github/workflows/release.yml` (`chore(release): v?([0-9]+\.[0-9]+\.[0-9]+).*`) cleanly strips GitHub PR number suffixes (e.g., `(#330)`), completely unblocking automated tagging and artifact drafting upon release PR merge.
   - **CI Lint Job:** The newly introduced `lint` job in `.github/workflows/ci.yml` introduces a fatal failure in CI. `lint-arwaky-cli` is a compiled Rust binary not published to PyPI, and `uv pip install` fails when no virtual environment is present. This breaks the CI gate, which in turn blocks Mergify from auto-merging any PR, creating severe friction for developers.

3. **Scripting Benchmarks Ergonomics:**  
   - Exposing shared fixtures via `modules/scripting/benches/conftest.py` successfully resolves fixture collection errors when executing `pytest modules/scripting/benches/`.

---

## Summary of Findings

| Severity | Count |
|----------|-------|
| Bug      | 1     |
| Suggestion | 2   |
| Nit      | 2     |
| **Total** | **5** |

---

## Review Issues

### 1. Broken CI `lint` job halts automated Mergify merges

- **Severity:** bug
- **File:** `.github/workflows/ci.yml:42`
- **Description:** The newly added `lint` job attempts to install and run `lint-arwaky-cli` via:
  ```yaml
  - name: Install lint-arwaky-cli
    run: uv pip install lint-arwaky-cli
  - name: Run lint-arwaky
    run: uv run lint-arwaky-cli scan
  ```
  This fails in GitHub Actions runner environments on multiple fronts:
  1. `lint-arwaky-cli` is not available on PyPI (the PyPI registry returns 404 Not Found); it is a proprietary compiled Rust binary.
  2. `uv pip install` without an activated virtual environment or `--system` flag exits with:
     `error: No virtual environment found; run 'uv venv' to create an environment, or pass '--system' to install into a non-virtual environment`.
  3. Running `lint-arwaky-cli scan` across the whole repository currently fails (exits with code 1) due to 49 pre-existing architecture and specification findings in `packages/` and `PRD.md`/`ROADMAP.md`.
  Because branch protection rules gate PR merges on passing CI checks, this broken job will turn every PR red and completely block Mergify auto-merge from functioning without manual intervention.
- **Suggestion:** Align the CI `lint` job with the existing project tooling and verified gates:
  - If enforcing architecture scans, provide a precompiled binary or setup action for `lint-arwaky-cli`, or run the scan with flags/thresholds that only gate clean paths.
  - Alternatively, if standard Python linting was intended (as documented in `AGENTS.md` and `CONTRIBUTING.md`), run `uv run ruff check modules/`, `uv run ruff format --check modules/`, and `uv run mypy` using the repository's standard composite action `./.github/actions/setup-psd-env`.
- **Status:** open

---

### 2. Misleading header comments contradict zero-friction auto-merge configuration

- **Severity:** suggestion
- **File:** `.github/mergify.yml:6-10`
- **Description:** The header comment of `.github/mergify.yml` states:
  ```yaml
  # Opt-in model: only a PR carrying the `auto-merge` label is queued
  # automatically (`auto_merge_conditions` below). Every other PR keeps the
  # manual merge flow. Queue any PR by hand with the `@mergifyio queue`
  # command, which the queue conditions accept without the label.
  ```
  However, lines 50–56 implement a zero-friction auto-merge model:
  ```yaml
  merge_protections_settings:
    # Auto-merge: every PR targeting `main` is queued and merged automatically
    # without requiring the `auto-merge` label.
    # Security: only PRs authored by rakaarwaky are allowed.
    auto_merge_conditions:
      - base = main
      - author = rakaarwaky
  ```
  Retaining the obsolete "opt-in" comment causes confusion for maintainers and developers wondering whether they must manually apply the `auto-merge` label to trigger Mergify.
- **Suggestion:** Update lines 6–10 of `.github/mergify.yml` to accurately describe the zero-friction model:
  ```yaml
  # Automatic queue model: every PR authored by rakaarwaky targeting `main` is
  # queued and merged automatically upon passing quality gates. The manual
  # `@mergifyio queue` command remains available as an alternative trigger.
  ```
- **Status:** open

---

### 3. Missing job timeout and unpinned actions in `ci.yml` lint job

- **Severity:** suggestion
- **File:** `.github/workflows/ci.yml:33-40`
- **Description:** Across the repository (`ci.yml` test matrix, `nightly.yml`, and `release.yml`), jobs specify explicit timeouts (e.g., `timeout-minutes: 20`) and use pinned commit SHAs (or the internal `.github/actions/setup-psd-env` action) to prevent unexpected workflow failures and runner hangs.
  The new `lint` job omits `timeout-minutes` and uses unpinned mutable action tags (`actions/checkout@v4`, `astral-sh/setup-uv@v5`). A hung process could consume runner time for up to GitHub's default 6 hours, delaying feedback loops for developers.
- **Suggestion:** Add `timeout-minutes: 10` to the `lint` job and pin action references to consistent commit SHAs or leverage `./.github/actions/setup-psd-env` with `sync-project: 'false'`.
- **Status:** open

---

### 4. Explicitly exclude draft PRs from Mergify auto-merge conditions

- **Severity:** nit
- **File:** `.github/mergify.yml:54`
- **Description:** While `pull_request_rules`'s `keep-prs-up-to-date` rule explicitly specifies `-draft` (line 73), `auto_merge_conditions` and `queue_rules.default` do not explicitly include `-draft`. Adding `-draft` makes the configuration self-documenting and guarantees that work-in-progress draft PRs created by `rakaarwaky` are not prematurely queued or evaluated against merge conditions until the author marks them "Ready for review".
- **Suggestion:** Add `- -draft` to `auto_merge_conditions` (and `queue_conditions`):
  ```yaml
  merge_protections_settings:
    auto_merge_conditions:
      - base = main
      - author = rakaarwaky
      - -draft
  ```
- **Status:** open

---

### 5. Missing trailing newline at EOF in `.github/mergify.yml`

- **Severity:** nit
- **File:** `.github/mergify.yml:133`
- **Description:** The `.github/mergify.yml` file ends without a trailing newline. While YAML parsers tolerate this, standard POSIX formatting conventions and git diff tooling flag missing newlines (`\ No newline at end of file`), adding minor visual noise to future diffs.
- **Suggestion:** Ensure `.github/mergify.yml` terminates with a single trailing newline.
- **Status:** open
