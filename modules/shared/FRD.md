# FRD — shared

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

`modules/shared/src/` is the flat kernel every feature module imports: value
objects (taxonomy), I/O-free helpers (utility), and cross-cutting contracts.
It is **flat on purpose** — no sub-folders, no per-domain packages; each file is
`<layer>_<concern>_<role>.py` (AES 7-layer naming) at the package root. No
lifecycle contract (`ITool*`) lives here; those are decentralized to the owning
feature module (installer/updater/uninstaller/runner). Shared owns only
cross-feature VOs and utilities.

Flow: feature capability → import a `modules.shared.src.<module>` → VO or
helper → typed error. Shared never imports a feature module (no cycles).

## Functional Requirements

### FR-001: Resolve the repo root from any location

- **Description**: `repo_root()` returns the checkout that owns the manifest.
- **Input**: optional `AGENTS_ARWAKY_ROOT` env hint.
- **Output**: `Path` to the checkout containing `config/manifest.json`.
- **Business Rules**: `AGENTS_ARWAKY_ROOT` is a soft hint — accepted only when it
  actually contains the anchor; otherwise discovery walks up from the calling
  file's own location (works in the main checkout and any git worktree).
- **Edge Cases**: no anchor anywhere up the tree → `RuntimeError` naming the
  missing anchor and the env var to set.
- **Error Handling**: `RuntimeError` with an actionable message; no silent fallback.

### FR-002: Provide XDG-compliant per-tool paths

- **Description**: `utility_xdg_paths` exposes data/config/cache/state/bin
  directories per tool, honoring XDG env overrides with `~/.local` defaults.
- **Input**: tool name (for per-tool dirs).
- **Output**: `Path` values; `ensure_xdg_dirs_exist(tool)` materializes them.
- **Business Rules**: no tool writes persistent state outside these dirs; the
  repo root is never a data location. Env overrides (`XDG_DATA_HOME`,
  `XDG_CONFIG_HOME`, …) win over defaults.
- **Edge Cases**: `XDG_RUNTIME_DIR` unset → falls back to a per-user runtime
  path; a tool dir that cannot be created → raised `OSError` at ensure-time.
- **Error Handling**: `OSError` from directory creation; resolution errors for
  env vars are explicit, not silent.

### FR-003: Read the manifest as the tool registry

- **Description**: `load_tools()` returns all `Tool` VOs; `find_tool(query)`
  resolves id/binary/alias to one.
- **Input**: none (reads `config/manifest.json`); `find_tool(query: str)`.
- **Output**: `list[Tool]`; `Tool | None`.
- **Business Rules**: the manifest is the single source of truth for tool ids,
  runner, binary, path, alias, `is_mcp`. A malformed manifest raises
  `ManifestParseError` at read time, not lazily.
- **Edge Cases**: unknown query (id, binary, or alias) → `None`.
- **Error Handling**: `ManifestParseError` carrying the offending field.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `repo_root()` | env hint | `Path` | `RuntimeError` | impl |
| `tool_data_dir(tool)` etc. | `str` | `Path` | `OSError` (ensure) | impl |
| `load_tools()` | — | `list[Tool]` | `ManifestParseError` | impl |
| `find_tool(query)` | `str` | `Tool \| None` | — (None) | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool registry, anchors | `ManifestParseError`, missing anchor |
| host env (XDG_*, `AGENTS_ARWAKY_ROOT`) | in | path resolution, root hint | `RuntimeError` / bad env |
| all feature modules | out | import VOs + utilities | no feature → shared imports (no cycles) |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Flat layout | zero sub-packages under `shared/src/` | `find modules/shared/src -mindepth 1 -maxdepth 1 -type d` → empty at `5556fd5` |
| No feature imports | shared never imports a feature package | import graph check at `5556fd5` |
| Deterministic root | same checkout → same `repo_root()` | `repo_root()` twice → identical path |

## Test Scenarios

- `repo_root()` finds the anchor in a git worktree without `AGENTS_ARWAKY_ROOT`.
- `repo_root()` raises `RuntimeError` when the anchor is absent from the tree.
- `load_tools()` returns one `Tool` per manifest entry; `find_tool("<alias>")` resolves it.
- XDG helpers honor `XDG_DATA_HOME` when set.

## Assumptions & Constraints

- `config/manifest.json` exists at the resolved root (the anchor contract).
- Flat layout is an architectural invariant, enforced by `aa check`.

## Glossary

- **VO (value object)**: immutable data type in a `taxonomy_*` module; no I/O.
- **flat kernel**: the no-sub-folder shape of `modules/shared/src/`.
