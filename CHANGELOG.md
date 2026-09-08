# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Centralized root/path resolution with validation (`tools/lib/paths.py`).
- Google Drive backup helper (`tools/backup/gdrive.py`).
- Generic retry utility (`tools/lib/utility_retry.py`).
- Capabilities tool resolver (`tools/lib/capabilities_tool_resolver.py`).
- Unified version bump script (`tools/build/bump_version.py`).
- Unit tests for `envfile`, `xdg`, and `manifest`.
- CI pipeline with lint / compile / audit / shellcheck / JSON gates.
- Opt-in Sentry error tracking (`ARWAKY_SENTRY_DSN`).
- Structured logging helpers in `ui.py`.
- `--version` command and `tools/config/version.txt`.
- zsh completion generation.
- `--json` output for `status`, `list`, `doctor`.

### Fixed
- Resolved lint violations across the orchestration layer (Ruff/Mypy/Pylance/Codacy).
- Env file quote round-trip escaping.
- `retry_api` only retries transient errors (429/500/502/503/timeout).
- `restore_tool` cleans target before extraction; backup/restore propagate failures.
- `generate_config.py` derives MCP servers from `manifest.json` (single source of truth).
- PID-file based daemon stop for Anytype native mode; password zeroing in 9Router env.
- ANSI-width-aware table padding and `[OK]/[WARN]/[FAIL]` status labels.
