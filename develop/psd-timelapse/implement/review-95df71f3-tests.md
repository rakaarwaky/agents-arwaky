# Review: Test Coverage & Quality

## Review Issues

### 1. suggestion — `modules/scripting/benches/conftest.py:3` — Wildcard import exports private names into conftest namespace

**Description:** The `from modules.scripting.benches.bench_scripting_fixtures import *` re-exports all names from `bench_scripting_fixtures.py` into `conftest.py`. Because `bench_scripting_fixtures.py` does not define `__all__`, private helper functions (`_make_layer`, `_build`) and constant tuples (`_CLASSIFY_NAMES`) are re-exported into the `conftest` namespace alongside the `@pytest.fixture` definitions (`classify_layers`, `timeline`, `layer_bounds`, `build_manifest`). While pytest only registers decorated fixtures, wildcard imports obscure which fixtures are provided and can cause name shadowing if additional fixtures or helpers are added later.

**Suggestion:** Replace the wildcard import with explicit fixture imports:
```python
"""Expose shared benchmark fixtures to pytest for the scripting bench suite."""

from modules.scripting.benches.bench_scripting_fixtures import (
    build_manifest,
    classify_layers,
    layer_bounds,
    timeline,
)

__all__ = [
    "build_manifest",
    "classify_layers",
    "layer_bounds",
    "timeline",
]
```
Alternatively, add `__all__ = ["classify_layers", "timeline", "layer_bounds", "build_manifest"]` to `bench_scripting_fixtures.py`.

**Status:** open

---

### 2. nit — `modules/scripting/benches/conftest.py` — File is currently untracked in git

**Description:** `git status` shows `modules/scripting/benches/conftest.py` as an untracked file (`?? modules/scripting/benches/conftest.py`). The implementer created the file but has not yet staged or committed it with `git add`.

**Suggestion:** Ensure `modules/scripting/benches/conftest.py` is staged (`git add modules/scripting/benches/conftest.py`) and committed before opening the pull request, or CI collection will fail with missing fixtures.

**Status:** open

---

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| Pytest collection | `uv run pytest modules/scripting/benches/ --co -o "python_files=bench_*.py"` | ✅ 14 tests collected across 5 files, 0 fixture errors |
| Affected bench tests | `uv run pytest modules/scripting/benches/bench_layer_classifier.py modules/scripting/benches/bench_manifest_writer.py -o "python_files=bench_*.py" --benchmark-disable -q` | ✅ 5 passed |
| All 5 bench files | `uv run pytest modules/scripting/benches/ -o "python_files=bench_*.py" --benchmark-disable -q` | ✅ 14 passed |
| Architecture scan | `uv run lint-arwaky-cli scan modules/scripting/benches/` | ✅ Clean (0 violations in benches) |

## Coverage Assessment

- **Benchmark Fixtures Discovery:** `modules/scripting/benches/conftest.py` correctly exposes the four shared fixtures (`classify_layers`, `timeline`, `layer_bounds`, `build_manifest`) across the entire `benches/` directory. All 14 benchmark test functions across 5 benchmark suites collect cleanly and execute without missing-fixture errors.
- **Workflow / CI Coverage:** The CI `test` job in `.github/workflows/ci.yml` runs `pytest modules/${{ matrix.shard }}/tests/` for all shards including `scripting`. Benchmark files are excluded by default in `pyproject.toml` (`python_files = ["contract_*.py", "unit_*.py", ...]`) to prevent ~24s of unasserted timing runs during regular test gates. The `--co -o "python_files=bench_*.py"` collection verify step ensures bench suites remain syntactically valid and importable.
- No test coverage gaps or regressions found in the implementation changes.
