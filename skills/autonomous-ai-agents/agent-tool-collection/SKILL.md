---
name: agent-tool-collection
description: "Add tools to rakaarwaky's agents-arwaky MCP collection."
metadata:
  tags: []
---

# Agent Tool Collection (agents-arwaky)

User maintains https://github.com/rakaarwaky/agents-arwaky — a personal collection of
AI-agent tools (MCP servers, CLIs, skills) where **each tool is a git submodule** plus a
thin local wrapper. When the user says they want to add a tool to their "koleksi", follow
the established pattern below.

## Wrapper layout convention

```text
<tool>-arwaky/
├── <upstream>/         # git submodule of the upstream project
├── script/install.sh   # local build into dist/
├── *_local.json        # ready-made stdio MCP client config snippet
└── README.md           # purpose, prerequisites, config examples

```text

## Steps to add a new tool

1. Clone the repo once if absent: `git clone --recurse-submodules` into `~/agents-arwaky`.
   - If a submodule fails to clone (404/private), note it to the user and continue; don't block.
2. Create a feature branch: `git checkout -b add-<tool>-arwaky`.
3. `git submodule add <upstream-url> <tool>-arwaky/<upstream>`.
4. Write `script/install.sh`, `<tool>_local.json` snippet, and README matching existing entries.
5. Update the main `README.md`: add a row in the Tools table AND an entry in the Repository
   layout tree (both places, keep style consistent).
6. Commit. Git identity may be unset on fresh machines — set repo-local
   `git config user.name/user.email` before committing.

## User preferences (this user)

- Language: Indonesian (Bahasa Indonesia), casual. Reply in Indonesian.
- Prefers the AI agent itself to run terminal commands rather than being handed commands
  to type ("suka AI agent yang menjalankan terminal untuk saya").
- Runs everything locally (Linux PC + Android); no VPS/remote access.
- For choosing between overlapping tools, likes a structured interview first — short
  numbered questions in chat; offer an HTML widget via preview pane (`data-hermes-send`)
  only if chat answers are inconvenient.

## References

- `references/mcp-vs-cli-decision.md` — Anytype MCP vs CLI comparison worked out this session;
  generalizable decision table for "MCP server vs CLI vs both" questions.
