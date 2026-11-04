---
name: context7-cli
description: Operates the ctx7 CLI and Context7 MCP registry — resolve a library ID, then query its docs (doc lookup / find-docs), skills install/search/suggest/list/remove/generate, and MCP setup. Use when mentioning ctx7 or context7, looking up API docs or library docs for a library or framework, finding docs via ctx7, installing skills, or configuring Context7 MCP for an editor.
when-to-use: Use when the user mentions ctx7, context7, or find-docs; asks to look up API docs or library docs for a library or framework; wants docs via MCP (context7__resolve-library-id / context7__query-docs) or the ctx7 CLI; wants to install, search, suggest, list, remove, or generate skills; or needs Context7 MCP set up for Claude Code, Cursor, OpenCode, or a project.
argument-hint: "ctx7 library <name> [query] | ctx7 docs <libraryId> <query> | ctx7 skills install|search|suggest|list|remove|info <args> | ctx7 setup [--mcp|--cli] | ctx7 login|logout|whoami | ctx7 upgrade"
metadata:
  tags:
    - documentation
    - context7
---

# ctx7 CLI

The Context7 CLI does three things: fetches up-to-date library documentation,
manages AI coding skills, and sets up Context7 MCP for your editor. Doc
*lookup* (the resolve-then-query workflow over MCP tools or the CLI) is
covered in [`references/find-docs.md`](references/find-docs.md); this skill
covers the tool itself.

## Global rules

- **Keep the CLI current.** `npm install -g ctx7@latest` (or `npx ctx7@latest
  <command>` without installing) before running commands.
- **Library IDs need the `/` prefix** — `/facebook/react`, not
  `facebook/react`. Always run `ctx7 library` to resolve an ID before calling
  `ctx7 docs`; `ctx7 docs react "hooks"` fails without a valid ID.
- **Skills repo format** is `/owner/repo` — e.g. `ctx7 skills install
  /anthropics/skills`.
- **Login requirements.** Most commands work without login. `skills generate`
  always requires it; `ctx7 setup` requires it unless `--api-key` or `--oauth`
  is passed. Set `CONTEXT7_API_KEY` to skip interactive login entirely.
- **Authentication.** `ctx7 login` (browser OAuth), `ctx7 login
  --no-browser` (prints URL), `ctx7 logout` (clear tokens), `ctx7 whoami`
  (current status).

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Doc lookup workflow | [`references/find-docs.md`](references/find-docs.md) | Resolve a library ID, then query its docs — two transports (MCP tools or CLI). |
| `ctx7 library` / `ctx7 docs` | [`references/docs.md`](references/docs.md) | Command reference. Use when writing code, verifying API signatures, or when training data may be outdated. |
| Skills management | [`references/skills.md`](references/skills.md) | `ctx7 skills install /owner/repo`, `search <keywords>`, `suggest`, `list`, `remove <name>`, `generate` (login required). |
| MCP setup | [`references/setup.md`](references/setup.md) | `ctx7 setup` — configure Context7 MCP for Claude Code / Cursor / OpenCode. |
