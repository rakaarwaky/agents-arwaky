# ComfyUI Skill Tests

Pytest suite covering the skill's scripts. Pure-stdlib unit tests run
without any setup; cloud integration tests need a Comfy Cloud API key.

## Running

```bash
# Unit tests only (no network required) — runs in <1s
python3 -m pytest tests/ -c tests/pytest.ini -o addopts="-p no:xdist"

# Including cloud integration tests
COMFY_CLOUD_API_KEY="comfyui-..." python3 -m pytest tests/ \
  -c tests/pytest.ini -o addopts="-p no:xdist"

# Just cloud tests
COMFY_CLOUD_API_KEY="comfyui-..." python3 -m pytest tests/test_cloud_integration.py \
  -c tests/pytest.ini -o addopts="-p no:xdist" -v
```

The `-c` and `-o` overrides isolate this suite from any parent
`pyproject.toml` pytest config (e.g. the `-n auto` from a parent repo).

## Test files

| File | Coverage |
|------|----------|
| `test_common.py` | Cloud detection, URL routing, format validation, embeddings, paths, seeds, model-list parsing, folder aliases |
| `test_extract_schema.py` | Connection tracing, positive/negative prompt detection, dedup logic, embedding deps |
| `test_run_workflow.py` | Param injection (incl. -1 seed, link refusal), output download walk, runner construction |
| `test_check_deps.py` | Model-name fuzzy matching, install command suggestions |
| `test_cloud_integration.py` | Live cloud API contract tests (auto-skipped without API key) |

## Adding tests

When you change a script:

1. Add a unit test if the change is pure logic (cloud detection, parsing, etc.)
2. Add a cloud integration test if the change depends on cloud API behavior
   (use `pytestmark = pytest.mark.cloud` so it auto-skips without a key)
3. Workflow fixtures live in `conftest.py` (`sd15_workflow`, `flux_workflow`,
   `video_workflow`)

## Why the explicit `-c` / `-o`?

The parent hermes-agent repo used to enable `pytest-xdist` by default
(`-n auto`); the canonical runner has since moved to per-file subprocess
isolation via `scripts/run_tests_parallel.py` and no longer uses xdist.
This suite is small enough that parallelism isn't worth the complexity, and
pytest-xdist isn't always installed in the user's environment. The
`-c tests/pytest.ini -o addopts="-p no:xdist"` flags make the suite run
identically regardless of the parent project's config.

## Prerequisites

- Python 3 with `pytest` importable
- Nothing else for unit tests (stdlib only); cloud tests also need
  `COMFY_CLOUD_API_KEY`

## Quick Start

From the skill root: `python3 -m pytest tests/ -c tests/pytest.ini -o addopts="-p no:xdist"`.

## Architecture

Unit tests import the scripts under `../scripts/` directly as modules;
`conftest.py` provides shared fixtures (workflow graphs, temp output dirs),
`pytest.ini` pins the isolated config, and cloud contract tests carry
`pytest.mark.cloud` so they skip without an API key.

## Project Structure

| Path | Role |
|------|------|
| `pytest.ini` | Isolated pytest config for this suite |
| `conftest.py` | Shared fixtures (`sd15_workflow`, `flux_workflow`, `video_workflow`) |
| `test_*.py` | One module per script under test |
| `../scripts/` | The scripts this suite exercises |

## Available Scripts

No entry-point scripts here — everything runs through pytest (see Running).

## Configuration

Configuration is `tests/pytest.ini` only; it deliberately overrides parent-repo
pytest config. The cloud tests read `COMFY_CLOUD_API_KEY` from the environment.

## Testing

The directory *is* the tests: run the commands under Running after any script
change, and keep new cloud behaviour behind the `cloud` marker.

## Contributing

When you change a script under `../scripts/`, extend its test module (see
Adding tests): pure logic → unit test, cloud API behaviour → marked cloud test.

## License

Part of the ComfyUI skill pack; the scripts and tests follow the upstream
ComfyUI project's license terms.


## Prerequisites

- See parent skill `SKILL.md` for host prerequisites.
- `python3` ≥ 3.10

## Quick Start

See the skill root `SKILL.md` Quick Start.

## Architecture

Delegates to the parent skill architecture (see `SKILL.md`).

## Project Structure

```
<dir>/
  README.md   # this file
  …           # content owned by this folder
```

## Available Scripts

See commands embedded above and the parent skill `scripts/`.

## Configuration

No environment variables specific to this folder. Parent skill config applies.

## Contributing

See the parent skill `SKILL.md` Contributing notes.

## License

Same license as the parent skill / repository.
