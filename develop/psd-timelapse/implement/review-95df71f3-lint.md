# Lint Review — PSD Timelapse CI/Mergify Standards Remediation

**Reviewer:** Lint & Code Hygiene Specialist
**Date:** 2026-11-21
**Branch:** `rakaarwaky/remediate-ci-mergify-standards`
**Files reviewed:**
- `.github/mergify.yml` (renamed from `.github/workflows/mergify.yml`)
- `.github/workflows/ci.yml` (added `lint` job)
- `.github/workflows/release.yml` (hardened tag regex)
- `modules/scripting/benches/conftest.py` (new file)

---

## Summary of Findings

| Severity | Count |
|----------|-------|
| Bug      | 2     |
| Suggestion | 1   |
| Nit      | 1     |
| **Total** | **4** |

---

## Review Issues

### 1. Missing trailing newline in `conftest.py`

- **Severity:** bug
- **File:** `modules/scripting/benches/conftest.py:3`
- **Description:** The file ends without a newline character. `ruff format --check` reports the file as "would be reformatted" — the formatted output adds a trailing `\n` after the last line. The implementer's verification claims ("format passed") is incorrect for this file. The same failure would propagate to the CI lint job.
- **Suggestion:** Add a trailing newline after the last line of the file:
  ```python
  """Expose shared benchmark fixtures to pytest for the scripting bench suite."""

  from modules.scripting.benches.bench_scripting_fixtures import *  # noqa: F401,F403
  <blank line / newline here>
  ```
- **Status:** open

---

### 2. RUF100: Unused `noqa` directive in `conftest.py`

- **Severity:** bug
- **File:** `modules/scripting/benches/conftest.py:3`
- **Description:** `ruff check` reports `RUF100: Unused 'noqa' directive` — `F401` is reported as unused (the wildcard import `*` does not trigger `F401` in ruff's default ruleset for this configuration) and `F403` is "non-enabled" (not in the current ruleset). The `# noqa: F401,F403` suppression hides the lint finding instead of resolving it properly, violating **AES304:BYPASS_COMMENT** (CRITICAL severity in lint-arwaky-cli). The file passes ruff without any `# noqa` comment at all — the import itself is clean.
- **Suggestion:** Remove the `# noqa: F401,F403` comment entirely. The import without suppression passes ruff:
  ```python
  from modules.scripting.benches.bench_scripting_fixtures import *
  ```
  This also eliminates the AES304 violation flagged by `lint-arwaky-cli scan modules/scripting/benches/conftest.py`.
- **Status:** open

---

### 3. AES304: Bypass comment triggers CRITICAL lint-arwaky violation

- **Severity:** suggestion
- **File:** `modules/scripting/benches/conftest.py:3`
- **Description:** `lint-arwaky-cli scan modules/scripting/benches/conftest.py` reports `AES304:BYPASS_COMMENT` at CRITICAL severity — "A lint suppression hides the defect instead of fixing it." This is the lint tool flagging the `# noqa: F401,F403` directive as a bypass comment. This issue is the same root cause as #2 above but reported by a different tool (lint-arwaky vs ruff). Fixing #2 resolves this.
- **Suggestion:** Remove the `# noqa` comment per issue #2.
- **Status:** open

---

### 4. CI lint job runs `lint-arwaky-cli scan` without path argument

- **Severity:** nit
- **File:** `.github/workflows/ci.yml:47`
- **Description:** The new `lint` job runs `uv run lint-arwaky-cli scan` without a path argument. `lint-arwaky-cli scan` without arguments defaults to scanning the current working directory (`.` in practice). The full-repo scan reports 49 pre-existing violations in modules like `packages/shared` (23), `packages/psd` (6), `packages/client` (4), `modules/api` (2), etc. The CI lint job will fail on these pre-existing violations. This is not a regression introduced by this PR — the same 49 violations exist on `main`. However, adding the job means the CI will now fail on every PR until those are resolved.
- **Suggestion:** Either:
  1. Run `lint-arwaky-cli scan .` with an explicit path (cosmetic improvement, same result), **and** resolve or baseline the pre-existing violations separately, OR
  2. Scope the CI lint job to only scan modified files, OR
  3. Add `continue-on-error: true` to the lint job temporarily until pre-existing violations are resolved.
- **Status:** open

---

## Tools Run and Results

| Tool | Target | Result |
|------|--------|--------|
| `lint-arwaky-cli scan .` | Full repo | 49 pre-existing violations (none in modified files except conftest.py's AES304) |
| `lint-arwaky-cli scan modules/scripting` | scripting member | 0 violations |
| `lint-arwaky-cli scan modules/scripting/benches/conftest.py` | conftest.py | 2 violations: AES304 (CRITICAL), AES101 (HIGH) |
| `lint-arwaky-cli scan .github/` | .github dir | 0 violations |
| `lint-arwaky-cli report .` | Full report | Confirms 49 violations match scan output |
| `ruff check modules/scripting/benches/conftest.py` | conftest.py | **FAIL** — RUF100: unused noqa directive |
| `ruff format --check modules/scripting/benches/conftest.py` | conftest.py | **FAIL** — file would be reformatted (missing trailing newline) |
| `mypy modules/scripting/benches/conftest.py` | conftest.py | FAIL — 3 missing-import errors for numpy/pytest (pre-existing, not caused by this PR) |
| `pyyaml safe_load` | All 3 YAML files | All VALID |
| `pytest --collect-only` | benches | 14 tests collected successfully |
| `py_compile` | conftest.py | OK (syntax valid) |
| `yamllint` | All 3 YAML files | Tool not installed; validated via PyYAML instead |

---

## Notes

- **AES101 on conftest.py** (`HIGH`): `lint-arwaky-cli` flags `conftest.py` for not matching a legal naming prefix. The same violation exists for every other `conftest.py` in the repo (e.g., `modules/renderer/tests/conftest.py`). This is a known, expected exception for pytest conftest files and is not a regression introduced by this change.
- **AES101 on YAML files** (ci.yml, release.yml, mergify.yml): These are flagged when scanned as individual files but **not** when scanning the `.github/` directory. They are pre-existing infrastructure files and the violations are not introduced by this PR.
- **mypy errors** (numpy, pytest import-not-found): These are pre-existing dependency stub issues unrelated to this PR's changes. The conftest.py itself has valid Python syntax.
- **AES304 root cause**: The `# noqa: F401,F403` directive is both a ruff RUF100 violation and a lint-arwaky AES304 violation. Removing it resolves both simultaneously.