---
name: google-workspace
description: 'Daily Google ops via workspace MCP: Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Tasks, Contacts, Chat. For user tasks.'
when-to-use: "Use when performing daily Google Workspace operations — Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Tasks, Contacts, or Chat — via the workspace MCP server."
argument-hint: "search_gmail_messages <query>|get_gmail_message_content <message_id>|send_gmail_message|manage_event|read_sheet_values|modify_sheet_values|create_doc|modify_doc_text|create_drive_file|list_drive_items|get_events|query_freebusy|start_google_auth"
metadata:
  tags:
    - Google
    - Gmail
    - Calendar
    - Drive
    - Sheets
    - Docs
    - Slides
    - Forms
    - Tasks
    - Contacts
    - Chat
    - OAuth
  related_skills: []
  category: productivity
---

# Google Workspace -- Tool Router

## References

Load on demand; only this page and the tool tables below are always in context.

- [references/pitfalls.md](references/pitfalls.md) — reproduced failure modes: recurring-event 400s, the 3-rejection pause, calendar 404s, real credential paths. Read before debugging an error.
- [references/gmail-search-syntax.md](references/gmail-search-syntax.md) — Gmail query operators (`is:unread`, `newer_than:7d`, `has:attachment`, `-category:promotions`, grouping) with ready-made patterns.
- [references/daily-brief.md](references/daily-brief.md) — start-of-day/next-day brief procedure: day window, events, conflicts, meeting prep, urgent mail, follow-ups owed. Load it when the user asks for a morning brief or "what's on my calendar and what needs attention".
- [references/docs-layout-workflow.md](references/docs-layout-workflow.md) — incremental Google Docs build order that avoids style cascade, index shifting, list merging, and table-cell corruption.
- [references/server-options.md](references/server-options.md) — transport, auth modes, tool filtering/tiers, deployment, credential loading priority.
- Per-service parameter tables: `gmail.md`, `drive.md`, `calendar.md`, `docs.md`, `sheets.md`, `slides.md`, `forms.md`, `tasks.md`, `contacts.md`, `chat.md`, `apps-script.md`, `search.md` — linked from each service section below.
- `references/workflows.md` — common workflows: daily brief, reply to email, find and share a file, read and update a spreadsheet, create a formatted document, process email attachments, edit a Google Doc, plus tips.
- [references/execution-mode.md](references/execution-mode.md) — server registration, MCP tool naming, and CLI usage.
- [references/setup.md](references/setup.md) — OAuth credential creation, client secret placement, and authentication.
- [references/tool-reference.md](references/tool-reference.md) — full tool-to-task mapping for all services.


## Execution Mode

MCP is preferred on this host; the CLI path (`workspace-cli`) is for headless use.
See [references/execution-mode.md](references/execution-mode.md) for server registration, MCP tool naming, and CLI usage.

## First-Time Setup

Auth is already configured if `~/.google_workspace_mcp/credentials/<email>.json` exists.
Walk the user through setup only when a tool call fails with a credential error.
See [references/setup.md](references/setup.md) for OAuth credential creation, client secret placement, and authentication.

## Universal Patterns

- Consolidated "manage" tools use an `action` parameter for create/update/delete.

## Tool Reference

Per-service parameter tables for Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Tasks, Contacts, Chat, Apps Script, Custom Search, and Auth.
See [references/tool-reference.md](references/tool-reference.md) for the full tool-to-task mapping.

## Common Workflows

Common workflows (daily brief, reply to email, find and share a file, read and update a spreadsheet, create a formatted document, process email attachments, edit a Google Doc, plus tips) live in `references/workflows.md`.

## Rules

1. **Confirm before mutating.** Never send mail, create/update/delete calendar events, delete or
   share Drive files, or modify Docs/Sheets without showing the user the exact target
   (recipient, file ID, share role, body) and getting approval. Prefer trashing over permanent
   deletion. A request for a *brief* or a *read* is not authorization to write.
2. **Read back what you wrote.** After an approved mutation, re-read the object and report the
   ID/link, so a silent no-op cannot pass as success.
3. **Verify auth before first use.** If a call fails with a credential error, walk the setup above
   rather than retrying -- three rejected calls trigger the ~60s pause described in
   [references/pitfalls.md](references/pitfalls.md).
4. **Paginate instead of truncating.** `list_calendars`, `get_events`, and the search tools return a
   `Next page token`; pass it back before concluding a result set is complete.
5. **Never invent tool names or parameters.** If a tool is not in the tables above and not in a
   `references/<service>.md`, it does not exist in this server build -- report the gap instead.
