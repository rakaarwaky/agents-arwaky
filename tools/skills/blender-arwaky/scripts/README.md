# Scripts — Helper Scripts

Operational scripts for building, releasing, and running **Blender Arwaky**.
All scripts use 3-word naming (`{verb}_{target}_{modifier}.py`) to match the
project's AES convention.

## Layout

```
scripts/
├── README.md                       # This file
├── build/                          # CI / release automation
│   ├── build_addon_package.py      # Build dist/blender_mcp_addon.zip
│   └── bump_release_version.py     # Bump version, rebuild, tag, push
├── blender/                        # Runtime tools that talk to Blender
│   ├── run_server_headless.py      # Headless TCP server loop (run inside Blender)
│   ├── manage_blender_process.py   # Spawn Blender in background, wait for port
│   ├── install_addon_blender.py    # Install addon into Blender (Win/macOS/Linux)
│   └── launch_blender_runtime.py   # Cross-platform Blender launcher
└── install/                        # User-facing installers
    └── install_cli_wrappers.py     # Install blender-cli / blender-arwaky globally
```

## Build & release

| Script                       | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| `build_addon_package.py`     | Produce `dist/blender_mcp_addon.zip` for releases.   |
| `bump_release_version.py`    | Bump `pyproject.toml` + manifest, build, tag, push.  |

Used by the GitHub Actions release workflow:

```bash
uv run python scripts/build/build_addon_package.py
```

## Blender runtime

| Script                       | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| `run_server_headless.py`     | Run the MCP TCP server inside Blender (background).  |
| `manage_blender_process.py`  | Launch Blender in background and wait for port 9876. |
| `install_addon_blender.py`   | Install the addon into Blender (cross-platform).     |
| `launch_blender_runtime.py`  | Launch Blender with sensible display defaults.       |

Typical headless flow:

```bash
uv run python scripts/blender/manage_blender_process.py
# or, if you want to control Blender yourself:
blender --background --python scripts/blender/run_server_headless.py
```

## CLI install

| Script                       | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| `install.sh`                 | Install `blender-arwaky` and `blender-mcp` globally. |

```bash
bash scripts/install/install.sh
blender-arwaky --help
blender-mcp --help
```

## Conventions

- **Naming:** `{verb}_{target}_{modifier}.py` (3 words, snake_case, no
  abbreviations). Verb-first reads naturally as a CLI command.
- **Shebang:** Always start with `#!/usr/bin/env python3`.
- **Path resolution:** Use `Path(__file__).resolve().parent` to locate the
  project root; do **not** hardcode absolute paths.
- **Cross-platform:** Prefer Python stdlib over `os.system` or shell-isms.
  Detect platform with `sys.platform` and use `pathlib.Path` for I/O.
- **No business logic:** Scripts orchestrate the project; domain code lives
  under `modules/` and the Blender runtime addon lives under `blender_mcp_addon/`.
