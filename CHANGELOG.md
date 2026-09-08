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

### Changed
- **XDG Standardization**: All internal tools now follow consistent XDG Base Directory paths:
  - Venv: `~/.local/share/<tool>/venv/` (not in source directory)
  - Config: `~/.config/<tool>/`
  - Cache: `~/.cache/<tool>/`
  - State: `~/.local/state/<tool>/`
- **Install scripts rewritten**: `install_blender.py`, `install_vision.py`, `install_qwen_web.py` now create venv in XDG data directory using pip (not uv run).
- **Uninstall scripts standardized**: All 4 internal tools use same XDG pattern with `TOOL_NAME`, `BIN_DIR`, `DATA_DIR`, `CONFIG_DIR`, `CACHE_DIR`, `STATE_DIR`.
- **lint-arwaky install consolidated**: Merged 4 install scripts (`install.local.sh`, `install.remote.sh`, `install.global.sh`, `install.dev.sh`) into single `install.sh` with `--local`, `--global`, `--remote`, `--dev` flags.
- **Venv symlinks moved to init**: `.venv`/`venv` symlinks in source directories are now created during `<tool> init`, not during install.

### Fixed
- Resolved lint violations across the orchestration layer (Ruff/Mypy/Pylance/Codacy).
- Env file quote round-trip escaping.
- `retry_api` only retries transient errors (429/500/502/503/timeout).
- `restore_tool` cleans target before extraction; backup/restore propagate failures.
- `generate_config.py` derives MCP servers from `manifest.json` (single source of truth).
- PID-file based daemon stop for Anytype native mode; password zeroing in 9Router env.
- ANSI-width-aware table padding and `[OK]/[WARN]/[FAIL]` status labels.
