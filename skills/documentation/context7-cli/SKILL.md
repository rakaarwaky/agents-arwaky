---
name: context7-cli
description: Operates the ctx7 CLI and Context7 MCP registry — resolve a library ID, then query its docs (doc lookup / find-docs), skills install/search/suggest/list/remove/generate, and MCP setup. Use when mentioning ctx7 or context7, looking up API docs or library docs for a library or framework, finding docs via ctx7, installing skills, or configuring Context7 MCP for an editor.
when-to-use: Use when the user mentions ctx7, context7, or find-docs; asks to look up API docs or library docs for a library or framework; wants docs via MCP (context7__resolve-library-id / context7__query-docs) or the ctx7 CLI; wants to install, search, suggest, list, remove, or generate skills; or needs Context7 MCP set up for Claude Code, Cursor, OpenCode, or a project.
argument-hint: ctx7 library <name> [query] [--json] | ctx7 docs <libraryId> <query> [--json] | ctx7 setup [--mcp|--cli] [--project] [--yes] [--api-key KEY] [--oauth] [--stdio] [--base-url URL] [--claude|--cursor|--opencode|--universal|--antigravity] | ctx7 auth login [--no-browser] | logout | whoami | ctx7 skills install|search|suggest|list|remove|info [--claude|--cursor|--opencode|--universal|--antigravity] [--global] [--project] [--yes] [--all] [--json] | ctx7 skills generate [-o DIR] [--all] [--global] [--claude|--cursor|--universal|--antigravity] | ctx7 upgrade [-y] [--check]
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
- **[Skills management](references/skills.md)** — Install, search, suggest, list, remove, and generate AI coding skills.
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
