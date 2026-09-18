---
name: psd-timelapse-workflow
description: "Work the psd-timelapse repo: PRD tiers, gates, PR prep."
metadata:
  tags: []
---
# PSD Timelapse project workflow

Use every session working in the psd-timelapse repo.

## PRD priority tiers (ALWAYS use these definitions)

The PRD defines P0-P3 as **product tiers**, not task severity:

| Tier | Meaning | Merge bar |
|------|---------|-----------|
| P0 | Deployment blockers — app crashes, can't release | All P0 must be complete |
| P1 | Core features — app works end-to-end | All P1 must be complete |
| P2 | Improvements — stability, perf, UX polish | Complete or explicitly deferred |
| P3 | Nice-to-have — optional features, docs polish | Complete or documented as optional |

Never invent your own task-severity labels and map them onto PRD tiers. The PRD is the single source of truth for what P0/P1/P2/P3 mean.

When the user asks "what's the status of P0?", report progress against the **PRD-defined P0 items**, not against tasks you classified as high-severity.

## Specs are implementation-agnostic (standing user rule)

PRD.md and FRD.md must NEVER contain source-code paths, module directory references, or code symbols (e.g. `modules/shared/src/...py`, `ClassName.method`, test file names) — specs must stay valid across future refactors/moves. Constant NAMES and numeric VALUES are contract vocabulary and are fine (`BRUSH_MIN_RADIUS = 8.0 px`). Refer to behavior by FR id or contract name ("the Canvas Mapping keyframe-delta operation"), not by symbol. README/docs-about-current-state may cite paths; PRD/FRD may not. Grep added spec lines before PR: `git diff origin/develop -- PRD.md 'modules/**/FRD.md' | grep '^+' | grep -E 'modules/|\\.py'`. When documenting an enum or error-code table, grep each member for emission sites outside its definition; a member that is only defined, never raised, must be labeled "Reserved — not currently emitted" rather than given a fabricated recovery surface consumers can never trigger. Shell-path examples in repo docs must use the fallback form `${XDG_DATA_HOME:-$HOME/.local/share}/...` — bare `$XDG_DATA_HOME` expands to `/...` when unset (it usually is) and the AI reviewer flags every such line.

## Backlog docs: format v2 (state tracker, never spec prose)

Each feature `BACKLOG.md` is a header block (`FRD:` link, `Tier:`, `State:`, `Next action:` one sentence, `Last verified: develop @ <hash>, <date> — <exact command> → <result>`) plus ONE work table: `ID | Spec Ref | Work Item | Priority | State | Actual Condition | Depends On`. - State is the 8-glyph legend in root `BACKLOG.md`; every state needs a UNIQUE glyph (⬜ Open vs ⏸️ Blocked once shared a glyph and broke grep). Priority is a PRD tier or `—`, never invented severity. - Deliberately absent: Owner, Change Log, per-row Updated, a prose "Current Condition" block — git history is the change log and a prose restatement of the table is exactly how rows rot. If the user pastes a generic multi-team backlog template, adopt its state-model ideas (legend, Actual Condition) but keep this shape; the evidence column outvotes template ceremony. - Enforce the AGENTS.md DoD rule: a PR that merges a fix updates every backlog row that fix invalidates, in the same PR. On a docs PR, sweep ALL rows whose cited facts the recent merges invalidated (closed items, dead counts) before writing. - Backlog numbers go stale within hours — PRs merge the same day. Re-run every cited measurement (`pytest modules/<m>`, dashboard vitest/build) on a worktree at freshly-fetched develop immediately before writing, and put the hash in `Last verified`. Never carry numbers from a previous session or from the branch being edited.

## Evidence-before-judgment

Never assess whether a branch/worktree/PR is relevant, stale, or ready without first checking the actual diff and test results. Worktrees can contain active WIP that you have not reviewed — an old commit date and an unopened PR say nothing about relevance.

## Plan verification against the live tree

When verifying a plan document written BEFORE earlier plan increments merged, re-check every finding against the current tree — merged fixes silently invalidate plan line-refs and 'still open' probes. For each finding record CONFIRMED / STALE / PARTLY-WRONG with the grep evidence; a plan's own acceptance criteria can contradict live config (e.g. a tightened fps range rejecting the repo's committed value), so cross-check any narrowing against config.yaml, the API validator, AND the dashboard before delegating. When a plan step's fix touches detection used by skipif-gated tests, trace who consumes the detection result — gating availability probes (not just wiring choices) silently drops regression-test coverage.

Plans are often authored from an exported docs bundle, not the live repo (check the run-metadata header for the source path): a "missing file" finding may be a local unstaged deletion or a bundle exclusion, not a repo gap — check `git ls-tree origin/develop -- <path>` and `git status --short` before planning a fix for it. Verify contract-level findings against CODE, not just doc prose: grep the helper/symbol in `modules/shared/src` and its regression tests in `modules/*/tests/` — a merged fix often leaves one stale sentence in a doc while the contract, the central helper, and its tests are already in place, collapsing a claimed CRITICAL to a wording edit.

## Scratch files are NOT render output

The AGENTS.md XDG output-path rule (`~/.local/share/psd-timelapse/...`) governs RENDER artifacts only. Do not over-generalize it into a home for agent scratch (task briefs, qwen I/O JSON/logs, session-state notes) — that directory is app data + the venv, and littering it is a user-visible mistake. Scratch belongs in `/tmp/<task-slug>/` or a worktree-local path.

## Prove pre-existing failures with a throwaway develop worktree

When a test fails after your change and you suspect order-coupling or pre-existing breakage, do NOT argue it — run `git worktree add --detach .worktrees/tmp-check origin/develop`, reproduce there, `git worktree remove --force` it, and quote both results in the PR/report. Check whole-suite order too: a file-level standalone failure can pass in the CI shard order.

## Virtual environment (standing rule)

The repo's isolated XDG venv is **not** activated by `uv sync` — sync only resolves and locks dependencies. Before any gate command or test run, activate it explicitly:

```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.local/share/psd-timelapse/venv"
source "$UV_PROJECT_ENVIRONMENT/bin/activate"
```

Run `python --version` and `python -c "import psd_tools"` as a two-line smoke test that the environment is live. If `psd_tools` (or any locked dependency) is importable from the system python but missing from the venv python, the venv is not active — do not re-run `uv sync` and assume it fixed itself; activate first.

Pitfall: a gate command that fails with `ModuleNotFoundError` during collection (e.g. pytest collecting 0 tests with import errors) is usually an unactivated venv, not a code problem. Check `VIRTUAL_ENV` and `python -c "import sys; print(sys.prefix)"` before reading the failure as a real test regression.

## Quality gates order

When preparing a branch for PR, run gates in this order:
1. `pytest <scope>` — tests pass
2. `ruff check <scope>` — lint clean
3. `mypy <scope>` — type check passes
4. `lint-arwaky-cli scan <scope> --format json` — AES violations = 0

Run on the worktree scope (e.g. `modules/renderer`), not the whole repo, to avoid noise from unrelated pre-existing issues.

AES and lint-arwaky cover **TypeScript and the frontend modules too**, not just Python/Rust — `lint-arwaky-typescript` documents the full TS command set (`scan`/`fix`/`ci`, workspace `--member`, AES201/403/404 TS rules). Never claim a language is unsupported by the architecture gates without checking the skill library first.

To run `packages/dashboard` tests inside a worktree without reinstalling deps, symlink the main checkout's: `ln -sfn <main-repo>/packages/dashboard/node_modules node_modules`, run `npx vitest run`, and `rm` the symlink before staging — it otherwise shows as untracked debris. `npm test` runs vitest in watch mode headless-unfriendly; `npx vitest run` is the one-shot form.

## Worktree isolation and tool trust (standing rule)

Do not trust a worktree's IDE/LSP diagnostics as ground truth for import resolution or symbol existence — a freshly-created worktree is not IDE-indexed the way the main checkout is, so hover and "could not be resolved" reports are frequently stale or wrong. The real checkers are `mypy`, `ruff`, and `pytest`; an LSP complaint that those three clear is noise — chase the real checker's output, not the editor's.

Pitfall: when mypy clears an "unknown attribute" or "could not be resolved" LSP diagnostic, treat the LSP output as defeated and move on. Do not add `type: ignore` or refactor the code to satisfy the editor.

## Patch safety (standing rule)

When patching a file, use a single specific match with enough surrounding context, NOT `replace_all` on a multi-line dataclass field list or method definition. The patch tool's expand/collapse matching can silently collapse neighboring field definitions and erase surrounding method bodies when the match spans structurally-similar repeated lines. Prefer: one precise match, or `write_file` the whole file when the edit is large.

## File-write encoding (standing rule)

Do not pass Python source through JSON-stringify-then-write — backslash-escape artifacts (`\"\"\"` literal escapes in docstrings, `\\n` inside string literals) land on disk as real text and break Python parsing. Write clean content directly.

## Answer measurement questions with a measured number

"How long does X take?" is answered by running X under a timer and reporting the wall-clock — nothing else. Context, qualifications, and "it depends" prose read as evasion. If it has not been timed, say "measuring now" and measure before answering.

## Pillow decompression bombs escape (OSError, ValueError)

`Image.DecompressionBombError` inherits from bare `Exception` — NOT OSError/ValueError (verified Pillow 12.3.0). Any decode-guard tuple `except (OSError, ValueError)` around PIL leaves a raise path: a PNG whose *declared* IHDR size exceeds 2 * `Image.MAX_IMAGE_PIXELS` raises at `Image.open()` time, before any post-open size check can fire. Catch it explicitly wherever `Image.open`/`load`/`convert` runs in a degrade-to-fallback path, and pin the regression with a fake PNG built via struct+zlib (valid IHDR + truncated IDAT) so no real decode happens in CI. Also: never key a process-global cache by `id()` of a PIL image — CPython recycles freed addresses and keeps the id across in-place pixel edits; key by a blake2b digest of `tobytes()` with mode/size bound in.

## Diagnosing CI hangs with gh

When a pytest job hits the 20-min timeout with no failure output: `gh run view <id> --attempt N --json jobs` to get per-attempt job ids, `gh api repos/<r>/check-runs/<job>/annotations` for the cancel reason, and the `--log` stream's `[ NN%]` progress markers + `Terminate orphan process` lines (grep the `\tRun tests\t` field via `awk -F'\t'`) to pin the last completed test. Exit code 143 = SIGTERM (timeout/replaced); `The operation was canceled.` with an orphaned ffmpeg means a hang mid-suite. Map the hang position to local `pytest --collect-only` test N to identify the culprit. Cross-check a suspected slow test by timing it locally under `taskset -c 0 nice -n 19` before blaming the code.

## CI runner pitfalls (psd-timelapse)

- GitHub `ubuntu-latest` runners do NOT ship the `ffmpeg` **binary** — `ffmpeg-python` (pip) is only bindings and does not provide it. Any test that really spawns FFmpeg fails with `RuntimeError: FFmpeg binary not found at 'ffmpeg'` on CI but passes locally. Fix: apt-install `ffmpeg` alongside `libegl1 libgl1` in every workflow running renderer tests, and guard real-binary tests with `@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg binary not on PATH")` (repo convention, see integration_compositor_renderer_mp4.py). Skipif alone is a trap: without ffmpeg installed CI is green with ZERO encode coverage (plan finding G7) — install it, don't just skip.
- PyOpenGL needs apt `libegl1`/`libgl1` on runners or `import OpenGL.EGL` raises AttributeError (None.platform) at test collection.
- A successful GPU/EGL probe on a runner does NOT mean a GPU exists: Mesa llvmpipe (software GL) makes `init_pipeline()` return True, so backend auto-detection picks the GPU path on CPU-only hosts and real renders crawl to a job timeout. Provide an operator env override that forces the CPU raster path at the container/backend-selection layer (e.g. `PSD_RASTER_BACKEND=cpu`, set on CI test steps), and log the chosen backend at INFO and every degradation at WARNING. Do NOT wire the override into `probe_backend()` itself — GPU regression tests are skipif-gated on `probe_backend()`, so overriding it there would silently drop their coverage on real GPU dev machines.
- Whenever a change makes previously-skipped tests RUN (installing a missing binary, removing a skip), run the full suite locally in the runner's degraded mode before pushing — e.g. force the CPU fallback with a bogus `PYOPENGL_PLATFORM` value and time the integration tests. Newly-enabled code paths fail differently from newly-broken ones: they hang rather than assert-fail.

## Worktree PR prep checklist

1. Check `git diff` to understand what the WIP contains
2. Run quality gates on the modified scope
3. Fix any failures (delegate if production code, patch if test/mock only)
4. Commit all changes (production + tests)
5. Push branch
6. Create PR targeting `develop`
7. Verify CI passes
8. Address AI-reviewer findings (cubic/CodeRabbit): verify EACH finding against the live code with grep before complying — reviewers are often right but may cite stale commits; fix valid ones in a follow-up commit, push, and post one PR comment stating the grep evidence for fix-vs-reject of each item.

For EGL/ctypes mocking patterns in renderer tests, see `references/mock-egl-ctypes.md`.
