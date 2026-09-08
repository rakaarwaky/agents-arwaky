# Changelog

Semua perubahan penting pada agents-arwaky akan dicatat di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/id/1.1.0/),
dan proyek ini mengikuti [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-09-08
### Added
- Migrasi penuh toolchain Bash → Python (40 file .py, per-tool installers)
- Struktur tools/ terpusat: cli/, lib/, install/, uninstall/, daemons/, deploy/, config/, skills/
- Skill pack terpusat di tools/skills/ (83 skill, user-managed)
- `aa unconnect` / `aa unskill` untuk memutus harness & membersihkan skill workspace
- Unit tests: test_envfile, test_manifest, test_xdg
- CI workflow (ruff, shellcheck, JSON, pip-audit, aa check)
- Secret management: file .env dipindah ke $XDG_DATA_HOME + .gitignore + pre-commit hook

### Security
- Rotasi & hapus kredensial live dari history (filter-branch)
- Sanitasi skill name + path containment (anti path traversal)
- Validasi API key sebelum menulis config / inject env
- Backup rotasi (.bak-arwaky max 3)
- Tar extraction aman (filter="data" + validasi member)
