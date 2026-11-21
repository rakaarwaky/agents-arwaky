# Implementation Summary — PSD Timelapse CI/Mergify Standards Remediation

Scope: Only `.github/workflows/mergify.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, and `modules/scripting/benches/conftest.py` were touched. Nothing outside this scope was created, moved, edited, or deleted.

## Files changed

### 1. `.github/workflows/mergify.yml` → `.github/mergify.yml` (relocated via `git mv`)
- The mergify configuration was relocated from `.github/workflows/` to `.github/` root (Mergify reads this file from the default branch `main`).
- Rewritten with the full required configuration:
  - `merge_queue`: `max_parallel_checks: 1`, `status_comments: outcomes`, `queue_controls_comment: true`
  - `defaults.queue_rule`: `update_method: merge`, `merge_method: merge`, `checks_timeout: 15min`
  - `queue_rules.default`: `queue_conditions: [base = main, author = rakaarwaky]`, `merge_method: merge`, `batch_size: 1`
  - `merge_protections_settings.auto_merge_conditions`: `[base = main, author = rakaarwaky]`
  - `priority_rules`: `hotfixes-first` (label = hotfix, priority high, `allow_checks_interruption: true`) and `refactors-last` (label = refactor, priority low)
  - `pull_request_rules`: `keep-prs-up-to-date`, `warn-on-conflicts`, `stale-cleanup`, `close-abandoned-stale`, and `remove the auto-merge label when a PR is merged or closed`

### 2. `.github/workflows/ci.yml` (added `lint` job)
- Added a `lint` job before the existing `test` job:
  ```yaml
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v5
          with:
            enable-cache: true
        - name: Set up Python
          run: uv python install "3.14"
        - name: Install lint-arwaky-cli
          run: uv pip install lint-arwaky-cli
        - name: Run lint-arwaky
          run: uv run lint-arwaky-cli scan
  ```
- Existing `web-ui` and `test` matrix jobs left intact.

### 3. `.github/workflows/release.yml` (hardened tag regex)
- Updated the `create-tag` job line from:
  ```sh
  version=$(git log -1 --format=%s "$MERGE_SHA" | sed -E 's/^chore\(release\): v?//' | xargs)
  ```
  to:
  ```sh
  version=$(git log -1 --format=%s "$MERGE_SHA" | sed -E 's/^chore\(release\): v?([0-9]+\.[0-9]+\.[0-9]+).*/\1/' | xargs)
  ```
  This strips PR suffixes like `(#330)` and keeps only the clean semver digits.

### 4. `modules/scripting/benches/conftest.py` (new file)
- Created to expose fixtures (`classify_layers`, `timeline`, `layer_bounds`, `build_manifest`) defined in `bench_scripting_fixtures.py` so pytest discovers them from the bench files.
- Content:
  ```python
  from modules.scripting.benches.bench_scripting_fixtures import *  # noqa: F401,F403
  ```

## Verification performed

- `git status --short`:
  ```
  RM .github/workflows/mergify.yml -> .github/mergify.yml
   M .github/workflows/ci.yml
   M .github/workflows/release.yml
  ?? modules/scripting/benches/conftest.py
  ```
  Confirms `.github/workflows/mergify.yml` is removed (renamed), `.github/mergify.yml` exists, ci.yml and release.yml modified, and conftest.py is the only new untracked file — clean, in-scope edits only.
- YAML syntax validation passed for `.github/mergify.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`.
- Benchmark collection:
  `uv run pytest modules/scripting/benches/ --co -o "python_files=bench_*.py"` → 14 tests collected across all 5 bench files with zero fixture errors.
- Runtime fixture verification:
  `uv run pytest modules/scripting/benches/bench_layer_classifier.py modules/scripting/benches/bench_manifest_writer.py -o "python_files=bench_*.py" --benchmark-disable -q` → 5 passed.

All five remediations implemented and verified.
