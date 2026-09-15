---
name: skill-manager
description: Discovers and provisions skill guides. Use when inspecting, installing skills across tools.
---
# Skill Manager (aa skill)

The Skill Manager provides skill discovery, integrity auditing, inspection, and automated provisioning of agent skill definitions (`SKILL.md`) from `agents-arwaky`'s internal and vendor tools into client workspaces.

## When to Use This Skill

Activate this skill when:
- Discovering what agent skills and tool capabilities exist within the `agents-arwaky` ecosystem.
- Provisioning tool usage guidelines to a workspace (`.agents/skills/<name>/SKILL.md`).
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

## Copy vs Symlink (provisioning contract)

Two provisioning paths, deliberately different:

- **`aa skill install` → project workspace (`.agents/skills/`): always COPIES.**
  A project is committed and pushed; a symlink to the agents-arwaky checkout is
  stored by git as mode 120000 with an absolute path that is dead in anyone
  else's clone (and becomes plain text on Windows with `core.symlinks=false`).
  Refresh a copy from the pack with `--force`. `--link` exists for local,
  uncommitted workspaces that want live pack tracking — do not commit it.
- **`aa connect <harness>` → harness skills dir: the WHOLE folder becomes ONE
  SYMLINK to the pack (`<harness>/skills -> agents-arwaky/skills`).** There is
  no per-skill provisioning step at all: add, remove, or edit a skill anywhere
  in the pack and every linked harness sees it instantly — self-improving
  agents (Hermes, Qwen Code) edit *through* the link, so their updates land in
  the repo and all harnesses share them; `aa update`/`git pull` propagates
  pack changes with zero re-provisioning. Harness runtimes that write state
  beside their skills (`.hub`, `.usage.json`, curator files, `skills-lock.json`)
  keep working because the state now lives in the pack — `.gitignore` keeps it
  out of history. Only harnesses verified to follow the root symlink are
  linked (per-adapter `SKILL_LINK_VERIFIED`); others fall back to copies.
  `aa connect --force` migrates an existing skills dir by MOVING leftovers
  into the pack (never deleting); `--copy-skills` forces copies everywhere;
  `aa disconnect` unlinks the root (restores an empty real dir) and never
  touches pack sources.

## Workspace Target Layout

When `aa skill install <name>` runs, it provisions the skill exclusively to the standard AI agent location:
- `.agents/skills/<name>/SKILL.md` (OpenClaw / Claude / Antigravity / AES standard)

Custom destination paths can be specified with `--dest <custom_path>`.
Existing files can be overwritten using `--force` or `-f`.
