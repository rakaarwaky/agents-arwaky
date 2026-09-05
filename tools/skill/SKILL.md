---
name: skill-manager
description: Discover, inspect, and provision AI agent skill guides (SKILL.md) across internal and vendor tools to current workspaces.
version: 1.0.0
---

# Skill Manager (aa skill)

The Skill Manager provides skill discovery, integrity auditing, inspection, and automated provisioning of agent skill definitions (`SKILL.md`) from `agents-arwaky`'s internal and vendor tools into client workspaces.

## When to Use This Skill

Activate this skill when:
- Discovering what agent skills and tool capabilities exist within the `agents-arwaky` ecosystem.
- Provisioning tool usage guidelines to a workspace (`agents/skill/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`).
- Checking whether all registered tools have complete and valid `SKILL.md` documentation.
- Inspecting a tool's agent guide or MCP parameters directly in the terminal without opening browsers or files manually.

## Available Commands

| Command | Action | Example |
|---|---|---|
| `aa skill list` | List all available skills across internal, vendor, and curated tools | `aa skill list` |
| `aa skill check` | Audit readiness of `SKILL.md` across all registered manifest tools | `aa skill check` |
| `aa skill install <name>` | Copy skill definition to current workspace (or `--target <dir>`) | `aa skill install blender` |
| `aa skill install all` | Provision all canonical skills to the workspace at once | `aa skill install all` |
| `aa skill show <name>` | Display the full markdown content of a skill in the terminal | `aa skill show fetch` |

## Workspace Target Layout

When `aa skill install <name>` runs, it provisions the skill to standard agent discovery locations:
1. `agents/skill/<name>/SKILL.md` (project workspace convention)
2. `.agents/skills/<name>/SKILL.md` (OpenClaw / Claude / Antigravity / AES convention)

Custom destination paths can be specified with `--dest <custom_path>`.
Existing files can be overwritten using `--force` or `-f`.
