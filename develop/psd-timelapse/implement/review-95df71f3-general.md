# Review Issues — psd-timelapse CI/Mergify Standards Remediation (95df71f3)

Scope reviewed: `.github/mergify.yml` (moved from `.github/workflows/mergify.yml`), `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `modules/scripting/benches/conftest.py`.

All four files were read in full. Local verification performed: YAML syntax validation for all three config files, `uv run pytest modules/` (802 passed, 1 pre-existing environment failure in `regression_renderer_golden_frame_pixel_diff.py` that passes with `PSD_RASTER_BACKEND=cpu` as CI sets it), `uv run ruff check modules/`, `uv run ruff format --check modules/`, `uv run mypy modules/` (pre-existing errors unrelated to changed files), `lint-arwaky-cli scan .`, and bench collection/run (`--co` → 14 tests collected; `--benchmark-disable -q` → 5 passed).

---

## Review Issues

### 1. Bug — `.github/workflows/ci.yml:40`

`uv pip install lint-arwaky-cli` runs with no active virtual environment. The `lint` job does not run `uv sync`, `uv venv`, or set `VIRTUAL_ENV`/`UV_PROJECT_ENVIRONMENT`. `uv pip` requires a virtual environment and will error with "no virtual environment or project found". Even if installation somehow succeeded, the next step `uv run lint-arwaky-cli scan` resolves binaries from the project venv, which does not exist in this job.

**Suggestion:** Replace the two steps (`uv pip install` + `uv run`) with a single ephemeral run:
```yaml
      - name: Run lint-arwaky
        run: uv run --with lint-arwaky-cli lint-arwaky-cli scan
```
Or run `uv sync` / `uv venv` first, then `uv pip install lint-arwaky-cli`. Confirm against `scripts/ci_local.sh` which calls `lint-arwaky-cli scan .` directly (the tool is expected to already be on PATH in the dev environment; CI needs an explicit install path).

**Status:** open

### 2. Bug — `modules/scripting/benches/conftest.py:3`

`# noqa: F401,F403` is unused. Ruff reports `RUF100: Unused noqa directive (unused: F401; non-enabled: F403)` — `F401` does not fire on star imports and `F403` is not enabled in this project's ruff config. Running `uv run ruff check modules/` fails solely on this line.

**Suggestion:** Remove the noqa directive:
```python
from modules.scripting.benches.bench_scripting_fixtures import *
```

**Status:** open

### 3. Suggestion — `.github/mergify.yml:8-9` and `:53-54`

Contradictory comments about auto-merge behavior. Lines 8-9 state "only a PR carrying the `auto-merge` label is queued automatically (`auto_merge_conditions` below)", but lines 53-54 state "every PR targeting `main` is queued and merged automatically **without** requiring the `auto-merge` label". Moreover, `auto_merge_conditions` contains only `base = main` and `author = rakaarwaky` — it does not check for `label = auto-merge`. The comments describe two different models; only one matches the code.

**Suggestion:** Reconcile the comments with the implemented behavior. If the model is "every PR by rakaarwaky targeting main is auto-queued/merged without a label" (as the code and lines 53-54 say), rewrite lines 8-9 accordingly. If the intent is opt-in via `auto-merge` label, add `label = auto-merge` to `auto_merge_conditions` and add a `pull_request_rule` with `actions.queue`/`actions.merge`.

**Status:** open

### 4. Nit — `.github/mergify.yml:130`

File has no trailing newline (last byte is `e` from `auto-merge`). POSIX text files should end with `\n`.

**Suggestion:** Add a trailing newline to `.github/mergify.yml`.

**Status:** open

---

## Items Verified — No Issues

| Item | Detail | Status |
|------|--------|--------|
| `.github/mergify.yml` location | Moved from `.github/workflows/mergify.yml` to `.github/mergify.yml`, which is a valid Mergify config path per docs (`.github/mergify.yml` is in the search list). Avoids GitHub Actions treating it as a workflow file. | Verified |
| `author = rakaarwaky` gate in queue | `queue_rules.default.queue_conditions` includes `base = main` and `author = rakaarwaky`. | Verified |
| `author = rakaarwaky` gate in auto-merge | `merge_protections_settings.auto_merge_conditions` includes `base = main` and `author = rakaarwaky`. | Verified |
| Mergify schema validity | `merge_queue` (`max_parallel_checks`, `status_comments: outcomes`, `queue_controls_comment`), `defaults.queue_rule`, `queue_rules` (no `merge_conditions` — single-step CI), `priority_rules`, `pull_request_rules` all match the documented Mergify file-format schema. | Verified |
| YAML syntax | `.github/mergify.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml` all parse with `yaml.safe_load`. | Verified |
| `.github/workflows/ci.yml` lint job | A `lint` job exists before `test`, using `actions/checkout@v4`, `astral-sh/setup-uv@v5`, Python 3.14. The step is present; only the install/run mechanism is broken (see issue #1). | Verified |
| `release.yml` semver regex | `sed -E 's/^chore\(release\): v?([0-9]+\.[0-9]+\.[0-9]+).*/\1/'` correctly handles `v` prefix with or without, strips `(#NNN)` PR suffix via `.*`, and the subsequent `[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]` validation rejects non-semver. Tested mentally against `chore(release): 1.0.1 (#330)` → `1.0.1`, `chore(release): v1.0.0 (#330)` → `1.0.0`, `chore(release): v1.0.0` → `1.0.0`. | Verified |
| `conftest.py` fixture export | `from modules.scripting.benches.bench_scripting_fixtures import *` re-exports `classify_layers`, `timeline`, `layer_bounds`, `build_manifest`. Pytest collects 14 bench tests across 5 bench files with zero fixture errors; 5 bench tests pass. | Verified |
| Test suite | `uv run pytest modules/` → 802 passed, 37 skipped, 1 failed (`regression_renderer_golden_frame_pixel_diff.py` — fails only because `PSD_RASTER_BACKEND` is not `cpu` locally; passes with `PSD_RASTER_BACKEND=cpu uv run pytest modules/renderer/tests/regression_renderer_golden_frame_pixel_diff.py`, matching CI's env var). Pre-existing, unrelated to changes. | Verified |
