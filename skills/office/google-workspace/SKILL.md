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
  category: office
---

# Google Workspace -- Tool Router

MCP is preferred on this host; the CLI path (`workspace-cli`) is for headless use. Load the matching reference per job below — this page is the router, not the content.

## Global rules

- **Confirm before mutating.** Never send mail, create/update/delete calendar events, delete or share Drive files, or modify Docs/Sheets without showing the user the exact target (recipient, file ID, share role, body) and getting approval. Prefer trashing over permanent deletion. A request for a *brief* or a *read* is not authorization to write.
- **Read back what you wrote.** After an approved mutation, re-read the object and report the ID/link, so a silent no-op cannot pass as success.
- **Verify auth before first use.** If a call fails with a credential error, walk `references/setup.md` rather than retrying blindly — three rejected calls trigger the ~60s pause described in `references/pitfalls.md`.
- **Paginate instead of truncating.** `list_calendars`, `get_events`, and the search tools return a `Next page token`; pass it back before concluding a result set is complete.
- **Never invent tool names or parameters.** Use only the consolidated `manage_*` tools' `action` parameter for create/update/delete, and only parameters documented in the service tables below; if a tool is missing from a table, report the gap instead.
- **Docs layout: build incrementally.** Insert a heading alone, style it, then insert body as `NORMAL_TEXT`; re-read the doc after every batch, since indices shift — `references/docs-layout.md` is required before building a formatted document.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Server registration, tool naming, CLI usage | [`references/execution-mode.md`](references/execution-mode.md) | `workspace` server naming, `mcp__workspace__` prefix, `workspace-cli` headless path. |
| First-time OAuth setup | [`references/setup.md`](references/setup.md) | OAuth credential creation, client-secret placement, and authentication. |
| Task-to-tool index | [`references/tool-reference.md`](references/tool-reference.md) | Full tool-to-task mapping across every service. |
| Per-service parameter tables | [`references/gmail.md`](references/gmail.md), [`references/drive.md`](references/drive.md), [`references/calendar.md`](references/calendar.md), [`references/docs.md`](references/docs.md), [`references/sheets.md`](references/sheets.md), [`references/slides.md`](references/slides.md), [`references/forms.md`](references/forms.md), [`references/tasks.md`](references/tasks.md), [`references/contacts.md`](references/contacts.md) | Full parameter reference per service — read the matching file before calling a service's tools. |
| Gmail query operators | [`references/gmail-search-syntax.md`](references/gmail-search-syntax.md) | `is:unread`, `newer_than:7d`, `has:attachment`, and ready-made query patterns. |
| Common workflows | [`references/workflows.md`](references/workflows.md) | Daily brief, reply, find+share, sheet read/update, formatted doc, attachments, doc editing. |
| Reproduced failure modes | [`references/pitfalls.md`](references/pitfalls.md) | Recurring-event 400s, the 3-rejection pause, calendar 404s, real credential paths. Read before debugging an error. |
| Start-of-day brief | [`references/daily-brief.md`](references/daily-brief.md) | Day window, events, conflicts, meeting prep, urgent mail, follow-ups owed. |
| Docs build order | [`references/docs-layout.md`](references/docs-layout.md) | Incremental Google Docs build order that avoids style cascade, index shifting, and table-cell corruption. |
| Server options | [`references/server-options.md`](references/server-options.md) | Transports, auth modes, tool filtering/tiers, deployment, and credential-loading priority. |
