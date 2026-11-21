# Simplicity Review — PSD Timelapse CI/Mergify Standards Remediation (95df71f3)

**Reviewer:** Simplicity & Over-Engineering Specialist
**Date:** 2026-11-21
**Branch:** `rakaarwaky/remediate-ci-mergify-standards`
**Files reviewed:**
- `.github/mergify.yml` (renamed from `.github/workflows/mergify.yml`)
- `.github/workflows/ci.yml` (added `lint` job)
- `.github/workflows/release.yml` (hardened tag regex)
- `modules/scripting/benches/conftest.py` (new file)

---

## Review Issues

### 1. suggestion — `modules/scripting/benches/conftest.py:3` — Extra conftest file with wildcard re-export from `bench_scripting_fixtures.py`

**Description:** `modules/scripting/benches/conftest.py` was added solely to re-export pytest fixtures from `modules/scripting/benches/bench_scripting_fixtures.py` via a wildcard import (`from modules.scripting.benches.bench_scripting_fixtures import *  # noqa: F401,F403`). Commit `fd7d7fc6` originally split the 4 shared fixtures (`classify_layers`, `timeline`, `layer_bounds`, `build_manifest`) out of `modules/scripting/benches/conftest.py` into `bench_scripting_fixtures.py`, which broke pytest fixture discovery. Adding a second file (`conftest.py`) that wildcard-imports from `bench_scripting_fixtures.py` introduces an extra file and a wildcard re-export layer instead of consolidating the fixtures into `conftest.py` (or explicitly importing the named fixtures).

**Suggestion:** Move the fixture definitions directly into `modules/scripting/benches/conftest.py` (and remove `bench_scripting_fixtures.py`), or replace the wildcard `import *` with explicit fixture imports if `bench_scripting_fixtures.py` must be retained.

**Status:** open

---

### 2. nit — `.github/workflows/ci.yml:42-44` — Multi-step `uv pip install` + `uv run` for one-off CLI execution

**Description:** In `.github/workflows/ci.yml`, the `lint` job installs `lint-arwaky-cli` into a transient environment via `uv pip install lint-arwaky-cli` (lines 42–43) and then invokes `uv run lint-arwaky-cli scan` (line 45). Because `lint-arwaky-cli` is not a project dependency in `pyproject.toml` or `uv.lock`, a single `uvx lint-arwaky-cli scan` step (or `uv run --with lint-arwaky-cli lint-arwaky-cli scan`) avoids the intermediate `uv pip install` step.

**Suggestion:** Collapse the install and run steps into a single `uvx lint-arwaky-cli scan` (or `uv run --with lint-arwaky-cli lint-arwaky-cli scan`) step.

**Status:** open