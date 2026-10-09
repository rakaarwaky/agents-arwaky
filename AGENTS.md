---
trigger: always
description: "agents-arwaky operational guide."
---
# agents-arwaky

## Runtime

- Language: Python 3.10+, Rust (cargo), Node.js 18+ (pnpm), Bun, C.
- Environment: host bare-metal; XDG base directories. No Docker. Anytype
  is the only Podman-containerized service. OmniRoute runs host-native.
- Artifacts: XDG prefixes. Data in ${XDG_DATA_HOME:-$HOME/.local/share}/,
  config in ${XDG_CONFIG_HOME:-$HOME/.config}/, cache in
  ${XDG_CACHE_HOME:-$HOME/.cache}/, launchers in
  ${XDG_BIN_HOME:-$HOME/.local/bin}/.

```bash
python3 --version
uv sync
```

## Project Quick Facts

INPUT  = config/manifest.json (tool registry, SSOT)
OUTPUT = XDG-compliant host binaries plus MCP server configs plus launchers

## Pipeline

manifest, adapter, capability, orchestrator, surface CLI

## Project Structure

```
agents-arwaky/
├── config/manifest.json   # tool registry (SSOT)
├── modules/               # AES features (vertical slices)
├── internal/              # sibling repos (submodules)
└── vendor/                # upstream tools (submodules)
```

## Commands

Every command must match the exact CI gate.

```bash
# Tests
python3 -m pytest modules/ -q                            # whole-workspace Python tests
python3 -m pytest modules/<feat>/tests -q                # one feature
python3 -m pytest modules/<feat>/tests/unit_<feat>.py -q # one file

# Lint / types / architecture
python3 -m ruff check modules/ --fix                     # matches ci.yml ruff job
python3 -m mypy modules/ --strict                        # type checker
lac scan . --format json                                  # architecture scanner (lint-arwaky)
lac scan . --fix                                           # dry-run variant, fixer is destructive
```

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) - the 7-layer AES vertical-slicing system.
- [ROADMAP.md](ROADMAP.md) - cross-cutting feature roll-up and status.
- [CONTRIBUTING.md](CONTRIBUTING.md) - how to add, update, or remove a vendor tool.
- [README.md](README.md) - quickstart and operator workflow.

---
