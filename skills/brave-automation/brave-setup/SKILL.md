---
name: brave-setup
description: Install the baa CLI, initialize its XDG workspace, verify prerequisites, and troubleshoot common Brave automation failures on Linux.
when-to-use: "Use when the user wants to install or repair the baa CLI and its prerequisites, initialize the XDG state/data workspace, resolve XDG path issues, or debug CDP connection failures, Local State locks, and Safe Storage key errors. Not for provisioning profiles (account-manager), importing credentials (password-manager), or Google session scripting."
argument-hint: "<install | init | doctor> [--dir PATH]"
created_by: curator
---

# Brave Setup (`baa init`)

You get the `baa` CLI running on a Linux host: install the CLI from the
`tools/` project, initialize the XDG workspace, and repair common failures.
Profile provisioning, credential import/export, and Google session scripting
belong to the sibling `account-manager` and `password-manager` skills.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | **Linux + Chromium only.** Confirm the host before running anything. | Unsupported platforms produce opaque errors. | `uname -s` returns `Linux`; Brave (native, Flatpak, or Snap) is installed. |
| R2 | **Never use `/tmp` for state.** Logs and sessions live under `$XDG_STATE_HOME/baa` and `$XDG_DATA_HOME/baa`; a reviewer must find output there. | XDG compliance; state survives across runs. | `baa init` output shows XDG paths; no writes to `/tmp`. |
| R3 | **One workspace per host.** `baa init` is idempotent; re-running it re-detects install paths without clobbering existing state. | Re-detection after a Brave move or upgrade. | `baa init` exits 0 and XDG dirs exist under `$XDG_STATE_HOME/baa`. |
| R4 | **Verify with `baa --help` and `baa profile list` after install/init.** A silent install that leaves the console script unresolvable is the main failure mode. | Catch drift between package install and CLI surface early. | Both commands print their trees; no `ModuleNotFoundError`. |

## Routing

| File | Purpose |
|------|---------|
| [`references/install.md`](references/install.md) | Install the `baa` CLI from the `tools/` project with `uv` and verify the console scripts. |
| [`references/init.md`](references/init.md) | Initialize the XDG state/data workspace and configure `profile.csv` / `passwords.csv`. |
| [`references/troubleshooting.md`](references/troubleshooting.md) | CDP connection failures, `Local State` locks, Safe Storage key rotation, XDG path issues. |
