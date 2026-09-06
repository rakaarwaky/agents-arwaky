---
name: google-workspace-mcp
description: Comprehensive Google Workspace MCP for Gmail, Calendar, Drive, Docs, Sheets, Slides, Tasks, and Chat.
version: 1.0.0
---

# Google Workspace MCP Server

Google Workspace MCP provides natural language control and tools over Google Workspace services (Gmail, Google Calendar, Google Drive, Docs, Sheets, Slides, Tasks, Forms, Contacts, and Chat) via standardized Model Context Protocol tools.

## When to Use This Skill

Activate this skill when:
- Searching, reading, drafting, or sending emails in Gmail.
- Scheduling, checking, creating, or modifying events in Google Calendar.
- Searching, uploading, downloading, moving, or managing files and folders in Google Drive.
- Creating or editing Google Docs, Sheets, Slides, Forms, or Google Tasks.
- Querying Google Contacts or sending messages in Google Chat / Spaces.

## Single Login & Authentication Model

In `agents-arwaky`, authentication is unified across all agent harnesses (Antigravity, Hermes, OpenCode, Claude Code, Cursor):

- **OAuth Client Configuration**: `${XDG_CONFIG_HOME:-$HOME/.config}/google-workspace-mcp/client_secret.json`
- **Cached User Session Tokens**: `${XDG_DATA_HOME:-$HOME/.local/share}/google-workspace-mcp/credentials/`

### First-Time Login
The first time any tool is invoked from any harness:
1. A local browser opens to the Google OAuth consent page.
2. Grant permissions for your Google account.
3. The refresh token is saved to the central XDG data directory.
4. All other agent harnesses immediately reuse this session without repeating login.

## Key Services & Tools Overview

| Service | Key Capabilities |
|---|---|
| **Gmail** | `list_gmail_messages`, `get_gmail_message`, `send_gmail_message`, `create_gmail_draft`, `search_gmail_messages` |
| **Calendar** | `list_calendar_events`, `create_calendar_event`, `update_calendar_event`, `delete_calendar_event` |
| **Drive** | `search_drive_files`, `get_drive_file_metadata`, `download_drive_file`, `upload_drive_file` |
| **Docs** | `get_doc_content`, `create_doc`, `insert_doc_text`, `batch_update_doc` |
| **Sheets** | `get_sheet_values`, `append_sheet_values`, `update_sheet_values`, `create_sheet` |
| **Tasks** | `list_tasks`, `create_task`, `update_task`, `delete_task` |
| **Chat** | `send_chat_message`, `list_chat_spaces`, `get_chat_space` |

## CLI & Orchestrator Execution

Execute Workspace MCP commands directly via `agents-arwaky` CLI:

```bash
# Verify installation and view tool options
aa run workspace-mcp --help

# Run with core tools only (saves token context)
aa run workspace-mcp --tool-tier core

# Run in read-only mode for safety
aa run workspace-mcp --read-only
```
