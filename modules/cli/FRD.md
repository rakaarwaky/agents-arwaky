# FRD — cli

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The cli feature is the `aa` command surface: `modules/root_cli_entry.py` (the
process entry point, flat at `modules/` root per `fdf5faf`) owns argument
parsing and top-level verb dispatch; `modules/cli/src/surface_*_command.py`
modules own each subcommand's rendering and orchestration calls. Every surface
module lives under `modules/cli/src/` — no surface file exists in a feature
module (enforced convention, verified at `5556fd5`). The router
(`surface_cli_router.py`) maps `tool install|update|uninstall|run|list` to the
aggregate orchestrators; the completion surface generates shell completions.

Flow: user runs `aa <verb>` → `root_cli_entry.py` parses → `cmd_<verb>` → a
`modules/cli/src/surface_*_command` handler → orchestrator aggregate → capability.

## Functional Requirements

### FR-001: Dispatch every `aa` verb to its orchestrator

- **Description**: `cmd_<verb>(argv)` routes a top-level or subcommand to the
  right surface handler and returns the process exit code.
- **Input**: `argv: list[str]` as split by the shell.
- **Output**: `int` exit code (0 = success).
- **Business Rules**: verb→handler mapping is total (every documented verb has a
  handler); unknown verb → usage error with the verb list, exit non-zero. The
  entry point is `modules/root_cli_entry.py`, not a `modules.cli.__main__`.
- **Edge Cases**: `aa help` / no args → prints command reference, exit 0;
  `--help` on any subcommand → that subcommand's help.
- **Error Handling**: unexpected exception → caught at the top, printed as
  `ERROR: <msg>`, non-zero exit (never a raw traceback into the user's shell).

### FR-002: Keep all surface command modules under `modules/cli/src/`

- **Description**: every `surface_*_command.py` is owned by the cli feature.
- **Input**: —.
- **Output**: —.
- **Business Rules**: feature modules expose orchestrators/contracts, not CLI
  surfaces; a feature `__init__.py` may *re-export* a surface from
  `modules.cli.src.*` for convenience, but the definition lives in cli.
- **Edge Cases**: a new verb added in a feature module → its surface handler is
  still created in `modules/cli/src/`.
- **Error Handling**: a surface file found outside `modules/cli/src/` is a
  convention violation flagged in review (gate-adjacent, not a compile error).

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `cmd_install(argv)` | `list[str]` | `int` | non-zero + `ERROR:` line | impl |
| `cmd_run(argv)` | `list[str]` | `int` | child exit code | impl |
| `cmd_mcp(argv)` | `list[str]` | `int` | non-zero + message | impl |
| `surface_cli_router.dispatch` | verb + args | `int` | usage error on unknown verb | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `modules/root_cli_entry.py` | in | process entry, verb dispatch | top-level `ERROR:` catch |
| `modules/cli/src/surface_*` | out | per-verb handlers | handler returns non-zero |
| feature orchestrators (runner/installer/… aggregate) | out | do the work | capability `*Result(success=False)` |
| host shell (completions) | out | `surface_completion_command` | missing shell → report |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| No traceback escape | any failing verb prints `ERROR: <msg>`, not a stack | `aa <bad-verb>` → clean error line, exit 1 |
| Verb coverage | every documented verb has a handler | `aa help` lists them; each runs |
| Surface locality | zero `surface_*.py` outside `modules/cli/src/` | `find modules -name 'surface_*.py'` → all under `modules/cli/src` at `5556fd5` |

## Test Scenarios

- `aa help` (or no args) prints the command reference and exits 0.
- `aa tool run <installed-tool> --help` exits 0.
- An unknown verb prints usage and exits non-zero without a traceback.
- No `surface_*.py` file exists outside `modules/cli/src/`.

## Assumptions & Constraints

- The entry point is `python -m modules.root_cli_entry` (post-`fdf5faf` layout);
  CI may still reference the older `modules.cli` path (root WS-08).
- Surfaces are thin: they parse args and call orchestrators, no business logic.

## Glossary

- **surface**: the CLI-facing module for a verb; lives only in `modules/cli/src/`.
- **verb**: a top-level `aa` command (`tool`, `mcp`, `check`, `connect`, …).
