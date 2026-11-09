# README — agents-arwaky

## Project Overview

agents-arwaky is a unified tool orchestrator and agent workspace for AI-native development. It installs, connects, and manages the full toolchain in one place: a skill pack that teaches coding agents how to work, a manifest of vendor  tools and a shell-launcher (`aa`) that ties it all together. The project serves developers and AI agents building with modern toolchains, and delivers a single, reproducible setup where every prerequisite, tool, harness connection, and service daemon is managed by one command surface instead of scattered installers.

## Prerequisites

- Linux with a package manager (apt, dnf/yum, pacman, or apk)
- `uv` (Python package manager; installed by the script if missing)
- Python &gt;= 3.10
- Node.js &gt;= 18 (LTS via NodeSource or nvm)
- Rust toolchain (`cargo` via rustup)
- `git`, `jq`, `curl`, `wget`

- `podman`, `bun`, `pnpm`, `npm` (installed by the script if missing)

## Quick Start


| Step | Action                                                                     | Command                 |
| ---- | -------------------------------------------------------------------------- | ----------------------- |
| 1    | Run the installer (all prerequisites, latest versions, non-interactive)    | `./install.sh`          |
| 2    | Verify all prerequisites are present                                       | `./install.sh --check`  |
| 3    | Open a new shell (or `source ~/.bashrc`) so the `aa` launcher is on `PATH` | `source ~/.bashrc`      |
| 4    | Diagnose the runtime environment and toolchain                             | `aa doctor`             |
| 5    | Install every registered tool (vendor + internal)                          | `aa tool install --yes` |
| 6    | Connect MCP servers, skills, and env to all harnesses                      | `aa connect --all`      |
| 7    | Start the AI gateway daemons                                               | `aa service start`      |
| 8    | Check overall health, submodule, and binary status                         | `aa status`             |


Every command is a plain `aa <noun> <action>` subcommand; run `aa help` for the full table, e.g. `aa tool list`, `aa tool run lint check .`, `aa skills catalog`, `aa mcp list`, `aa backup`, `aa submodules`, `aa clean`.

## Reference


| Artifact                  | Purpose                                                | Link                                                 |
| ------------------------- | ------------------------------------------------------ | ---------------------------------------------------- |
| AGENTS.md                 | Agent operational guide (runtime, structure, commands) | [AGENTS.md](AGENTS.md)                               |
| ARCHITECTURE.md           | AES layer contract and linter rule catalog             | [ARCHITECTURE.md](ARCHITECTURE.md)                   |
| PRD.md                    | What the product does and why                          | [PRD.md](PRD.md)                                     |
| ROADMAP.md                | What ships next, in order                              | [ROADMAP.md](ROADMAP.md)                             |
| CONTRIBUTING.md           | Branch, commit, and PR conventions                     | [CONTRIBUTING.md](CONTRIBUTING.md)                   |
| CHANGELOG.md              | Release history                                        | [CHANGELOG.md](CHANGELOG.md)                         |
| THIRD\_PARTY\_LICENSES.md | Third-party license inventory                          | [THIRD\_PARTY\_LICENSES.md](THIRD_PARTY_LICENSES.md) |
