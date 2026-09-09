---
name: anytype-mcp
description: Model Context Protocol (MCP) server for interacting with Anytype local spaces, objects, notes, and graph through natural language.
version: 1.0.0
---

# Anytype MCP Server

Anytype MCP connects AI agents to Anytype's local-first knowledge graph, allowing querying, reading, creating, and updating objects, notes, collections, and spaces.

## When to Use This Skill

Activate this skill when:
- Searching for existing knowledge, notes, documentation, or tasks within Anytype.
- Creating or editing pages, bookmarks, notes, or tasks in an Anytype space.
- Inspecting space members, object types, templates, and relation properties.
- Performing cross-space global searches across local knowledge bases.

## Prerequisites & Daemon Connection

The Anytype MCP server communicates locally with the Anytype daemon at `http://127.0.0.1:31012`.
Ensure the daemon is running before making calls:

```bash
# Check daemon status
aa anytype status

# Start daemon if not active
aa anytype start
```

## Primary Tools

| Tool / Function | Purpose | Key Parameters |
|---|---|---|
| `search_global` | Search for objects, notes, and pages across all accessible spaces | `query` (string) |
| `search_space` | Search within a specific space | `space_id` (string), `query` (string) |
| `get_spaces` | List all spaces the agent has access to | None |
| `get_object` | Fetch complete content and metadata of a specific object | `space_id` (string), `object_id` (string) |
| `create_object` | Create a new page, note, or custom type object | `space_id` (string), `type_id` (string), `name` (string), `body` |
| `update_object` | Update properties or content of an existing object | `space_id` (string), `object_id` (string), `fields` |
| `get_types` | Inspect available object types and schemas in a space | `space_id` (string) |

## Authentication Configuration

Authentication headers are managed via `.env` at repository root or XDG config:
```bash
OPENAPI_MCP_HEADERS='{"Authorization":"Bearer <ANYTYPE_API_KEY>", "Anytype-Version":"2025-11-08"}'
```
To generate or refresh agent keys automatically:
```bash
aa anytype auth-key "mcp-agent-key"
```
