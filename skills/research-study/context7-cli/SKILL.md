---
name: context7-cli
description: Operates the ctx7 CLI (npm ctx7 / npx ctx7@latest) and Context7 MCP registry — resolve a library ID, then query its docs (doc lookup / find-docs), and set up or remove Context7 for an editor or project. Use when the user says how do I use X / gimana cara pakai for a library or tool (e.g. git-cliff, comrak, qlty), mentions ctx7 or context7, looks up up-to-date API docs (training data may be stale), or needs Context7 MCP configured or unconfigured. Note: ctx7 0.8.2 ships no ctx7 skills subcommand and no --universal setup flag; the skills-management commands in references/skills.md target a newer CLI build.
when-to-use: "Use when the user mentions ctx7, context7, or find-docs; asks \"how do I use / gimana cara pakai\" a library, tool, or framework and current docs matter; asks to look up API docs or library docs (training data may be stale); wants docs via the Context7 MCP tools (context7__resolve-library-id / context7__query-docs) or the ctx7 CLI; or needs to set up (or remove) Context7 MCP/CLI for Claude Code, Cursor, VS Code, Devin, Copilot CLI, OpenCode, Codex, Antigravity, or Gemini CLI."
argument-hint: "ctx7 login [--no-browser] | ctx7 logout | ctx7 whoami | ctx7 library <name> [query] [--json] | ctx7 docs <libraryId> <query> [--json] [--language LANG] | ctx7 setup [--mcp] [--cli] [--project] [--yes] [--api-key KEY] [--oauth] [--stdio] [--base-url URL] [--claude] [--cursor] [--vscode] [--devin] [--copilot] [--opencode] [--codex] [--antigravity] [--gemini] | ctx7 remove [--mcp] [--cli] [--all] [--project] [--yes] [--claude] [--cursor] [--vscode] [--devin] [--copilot] [--opencode] [--codex] [--antigravity] [--gemini] | ctx7 upgrade [-y] [--check] | npx ctx7@latest <command>"
metadata:
  tags:
    - documentation
    - context7
---

# ctx7 CLI

The Context7 CLI does three things: fetches up-to-date library documentation, manages AI coding skills, and sets up Context7 MCP for your editor.

Doc *lookup* (the resolve-then-query workflow over MCP tools or the CLI) is
covered in [`references/find-docs.md`](references/find-docs.md); this skill
covers the tool itself.

Make sure the CLI is up to date before running commands:

```bash
npm install -g ctx7@latest

```text

Or run directly without installing:

```bash
npx ctx7@latest <command>

```text

## What this skill covers

- **[Documentation lookup](references/find-docs.md)** — Resolve a library ID, then query its docs (the "find-docs" job; two transports — MCP tools or CLI).
- **[Documentation commands](references/docs.md)** — `ctx7 library` / `ctx7 docs` command reference. Use when writing code, verifying API signatures, or when training data may be outdated.
- **[Skills management](references/skills.md)** — Install, search, suggest, list, remove, and generate AI coding skills. Documented against a CLI build newer than the published `ctx7@0.8.2` (which registers only login, logout, whoami, setup, remove, library, docs, upgrade); verify `ctx7 skills --help` on your installed version before relying on it.
- **[Setup](references/setup.md)** — Configure Context7 MCP for Claude Code / Cursor / OpenCode.

## Quick Reference

```bash
# Documentation
ctx7 library <name> <query>           # Step 1: resolve library ID
ctx7 docs <libraryId> <query>         # Step 2: fetch docs

# Skills
ctx7 skills install /owner/repo       # Install from a repo (interactive)
ctx7 skills install /owner/repo name  # Install a specific skill
ctx7 skills search <keywords>         # Search the registry
ctx7 skills suggest                   # Auto-suggest based on project deps
ctx7 skills list                      # List installed skills
ctx7 skills remove <name>             # Uninstall a skill
ctx7 skills generate                  # Generate a custom skill with AI (requires login)

# Setup
ctx7 setup                            # Configure Context7 MCP (interactive)
ctx7 login                            # Log in for higher rate limits + skill generation
ctx7 whoami                           # Check current login status

```text

## Authentication

```bash
ctx7 login               # Opens browser for OAuth
ctx7 login --no-browser  # Prints URL instead of opening browser
ctx7 logout              # Clear stored tokens
ctx7 whoami              # Show current login status (name + email)

```text

Most commands work without login. Exceptions: `skills generate` always requires it; `ctx7 setup` requires it unless `--api-key` or `--oauth` is passed. Login also unlocks higher rate limits on docs commands.

Set an API key via environment variable to skip interactive login entirely:

```bash
export CONTEXT7_API_KEY=your_key

```text

## Common Mistakes

- Library IDs require a `/` prefix — `/facebook/react` not `facebook/react`
- Always run `ctx7 library` first — `ctx7 docs react "hooks"` will fail without a valid ID
- Repository format for skills is `/owner/repo` — e.g., `ctx7 skills install /anthropics/skills`
- `skills generate` requires login — run `ctx7 login` first
