---
name: google-workspace
description: Daily Google ops via workspace MCP: Gmail, Drive, Calendar, Docs. For user tasks.
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

## Execution Mode

### MCP (preferred; this is what runs on this host)

The server is registered under the name **`workspace`** (in `~/.qwen/settings.json` and in
`mcp_servers.generated.json`; manifest id `workspace`, alias `google-workspace`, binary
`workspace-mcp`). So the callable tool names are **`mcp__workspace__search_gmail_messages`**,
`mcp__workspace__manage_event`, and so on.

The tables below list **base names only**. Prefix them with the server name your harness
exposes (`mcp__workspace__` on Qwen Code). Do **not** use a `google-workspace:` prefix — no
server is registered under that name and the calls fail.

If no `mcp__workspace__*` tools are visible, the server is not registered in that harness —
re-provision it (`aa connect <harness>` or `aa mcp generate`) rather than falling back to raw REST.

### CLI (headless / no MCP client)

`workspace-mcp` itself only serves MCP — it has **no `--cli` flag** (verified against
`workspace-mcp --help`). Its companion console script is `workspace-cli`, which talks to a
**running** server and needs no MCP client:

```bash
# Start the server with HTTP transport first (default target http://localhost:8000/mcp):
workspace-mcp --transport streamable-http &

workspace-cli list
workspace-cli call search_gmail_messages query="is:unread" max_results=5
# Override the target with WORKSPACE_MCP_URL; `uv run --directory vendor/google-workspace-mcp workspace-cli ...` if not on PATH.
```

Server-side flags worth knowing (all documented in [references/server-options.md](references/server-options.md)):

```bash
aa tool run workspace-mcp --help        # or: workspace-mcp --help
workspace-mcp --tool-tier core          # fewer tools, fewer tokens
workspace-mcp --read-only               # read-only scopes, write tools disabled
```

For any tool, read the matching `references/<service>.md` before calling it. Only use
parameters documented there — do not invent parameters.

## First-Time Setup

Auth is already configured on this host if `~/.google_workspace_mcp/credentials/<email>.json`
exists. Walk the user through setup only when a tool call fails with a credential error.

### 1. Create OAuth credentials
Direct the user to [Google Cloud Console](https://console.cloud.google.com/apis/credentials):
- Create OAuth 2.0 Client ID (Desktop application type)
- Enable the Google APIs they need (Gmail, Drive, Calendar, etc.)
- Copy the Client ID and Client Secret

### 2. Make the client secret visible to the server process
Do not ask the user to paste secrets into the conversation. Either point the server at a
downloaded JSON file with `GOOGLE_CLIENT_SECRET_PATH`, or put the id/secret in the `env` block
of the harness config that **launches** the server — for Qwen Code that is
`~/.qwen/settings.json` (`mcpServers.workspace.env`, or the top-level `env` block); merge into
any existing `env` object instead of replacing it. This repo's copy lives at
`vendor/google-workspace-mcp/client_secret.json`, which is the default project-root location
because the `workspace-mcp` launcher runs the server from that directory. `vendor/` is a pinned
submodule: treat that file as machine-local config, never a thing to edit or commit.

### 3. Authenticate
- **MCP mode**: call `start_google_auth` to open the browser OAuth flow
- **CLI mode**: run any tool through a streamable-http server -- the first invocation opens the OAuth flow
- Credentials are cached in `~/.google_workspace_mcp/credentials/<email>.json` (override with
  `WORKSPACE_MCP_CREDENTIALS_DIR`, then legacy `GOOGLE_MCP_CREDENTIALS_DIR`) for future sessions

Full loading order, transports, and tool filtering: [references/server-options.md](references/server-options.md)
Reproduced error signatures and their workarounds: [references/pitfalls.md](references/pitfalls.md)

## Universal Patterns

- Consolidated "manage" tools use an `action` parameter for create/update/delete.

## Tool Reference

### Gmail

| Task | Tool |
|------|------|
| Search/find emails | `search_gmail_messages` |
| Read one email | `get_gmail_message_content` |
| Read multiple emails | `get_gmail_messages_content_batch` |
| Read a thread | `get_gmail_thread_content` |
| Read multiple threads | `get_gmail_threads_content_batch` |
| Send email (new or reply) | `send_gmail_message` |
| Create draft | `draft_gmail_message` |
| Download attachment | `get_gmail_attachment_content` |
| Add/remove labels (one) | `modify_gmail_message_labels` |
| Add/remove labels (batch) | `batch_modify_gmail_message_labels` |
| Manage labels | `manage_gmail_label` |
| List labels | `list_gmail_labels` |
| Manage filters | `manage_gmail_filter` |
| List filters | `list_gmail_filters` |

For parameters: [references/gmail.md](references/gmail.md) -- and for the `query` syntax, [references/gmail-search-syntax.md](references/gmail-search-syntax.md).

### Google Drive

| Task | Tool |
|------|------|
| Search files/folders | `search_drive_files` |
| List items in folder | `list_drive_items` |
| Read file content | `get_drive_file_content` |
| Download file | `get_drive_file_download_url` |
| Create file | `create_drive_file` |
| Create folder | `create_drive_folder` |
| Copy file | `copy_drive_file` |
| Update file metadata | `update_drive_file` |
| Share / set permissions | `set_drive_file_permissions` |
| Manage access (add/remove) | `manage_drive_access` |
| Check permissions | `get_drive_file_permissions` |
| Get shareable link | `get_drive_shareable_link` |
| Check public access | `check_drive_file_public_access` |
| Import file to Google Doc | `import_to_google_doc` |

For parameters: [references/drive.md](references/drive.md)

### Google Calendar

| Task | Tool |
|------|------|
| List calendars | `list_calendars` |
| Get events | `get_events` |
| Create/update/delete event | `manage_event` |
| Check availability | `query_freebusy` |

For parameters: [references/calendar.md](references/calendar.md) -- read [references/pitfalls.md](references/pitfalls.md) first for the recurring-event timezone rule and the secondary-calendar 404s.

### Google Docs

| Task | Tool |
|------|------|
| Read doc as Markdown | `get_doc_as_markdown` |
| Read doc content (raw) | `get_doc_content` |
| Create new doc | `create_doc` |
| Modify text / apply styles | `modify_doc_text` |
| Insert elements (tables, lists, breaks) | `insert_doc_elements` |
| Insert image | `insert_doc_image` |
| Create table with data | `create_table_with_data` |
| Update paragraph styles | `update_paragraph_style` |
| Find and replace | `find_and_replace_doc` |
| Inspect structure | `inspect_doc_structure` |
| Batch update (multiple ops) | `batch_update_doc` |
| Headers/footers | `update_doc_headers_footers` |
| Manage tabs | `manage_doc_tab` |
| Export to PDF | `export_doc_to_pdf` |
| List docs in folder | `list_docs_in_folder` |
| Search docs | `search_docs` |
| Comments | `manage_document_comment` / `list_document_comments` |
| Debug table structure | `debug_table_structure` |

For parameters: [references/docs.md](references/docs.md) -- for multi-step layout work (headings, lists, tables) also follow [references/docs-layout-workflow.md](references/docs-layout-workflow.md).

### Google Sheets

| Task | Tool |
|------|------|
| Read cell values | `read_sheet_values` |
| Write/append/clear values | `modify_sheet_values` |
| Format cells | `format_sheet_range` |
| Conditional formatting | `manage_conditional_formatting` |
| Get spreadsheet info | `get_spreadsheet_info` |
| Create spreadsheet | `create_spreadsheet` |
| Create sheet (tab) | `create_sheet` |
| Move rows between sheets | `move_sheet_rows` |
| List spreadsheets | `list_spreadsheets` |
| Comments | `manage_spreadsheet_comment` / `list_spreadsheet_comments` |

For parameters: [references/sheets.md](references/sheets.md)

### Google Slides

| Task | Tool |
|------|------|
| Get presentation | `get_presentation` |
| Get specific slide | `get_page` |
| Get slide thumbnail | `get_page_thumbnail` |
| Create presentation | `create_presentation` |
| Batch update | `batch_update_presentation` |
| Speaker notes | `get_presentation` (`include_speaker_notes`) + `batch_update_presentation` |
| Comments | `manage_presentation_comment` / `list_presentation_comments` |

For parameters: [references/slides.md](references/slides.md)

### Google Forms

| Task | Tool |
|------|------|
| Get form | `get_form` |
| Create form | `create_form` |
| Batch update form | `batch_update_form` |
| List responses | `list_form_responses` |
| Get one response | `get_form_response` |
| Publish settings | `set_publish_settings` |

For parameters: [references/forms.md](references/forms.md)

### Google Tasks

| Task | Tool |
|------|------|
| List task lists | `list_task_lists` |
| Get task list | `get_task_list` |
| Manage task list (CRUD) | `manage_task_list` |
| List tasks | `list_tasks` |
| Get task | `get_task` |
| Manage task (CRUD/move) | `manage_task` |

For parameters: [references/tasks.md](references/tasks.md)

### Google Contacts

| Task | Tool |
|------|------|
| Search contacts | `search_contacts` |
| Get contact | `get_contact` |
| Manage contact (CRUD) | `manage_contact` |
| Batch manage contacts | `manage_contacts_batch` |
| List contact groups | `list_contact_groups` |
| Get contact group | `get_contact_group` |
| Manage contact group | `manage_contact_group` |
| List all contacts | `list_contacts` |

For parameters: [references/contacts.md](references/contacts.md)

### Google Chat

| Task | Tool |
|------|------|
| List spaces | `list_spaces` |
| Get messages | `get_messages` |
| Search messages | `search_messages` |
| Send message | `send_message` |
| Edit a message already sent | `send_message` with `message_name` |
| React to message | `create_reaction` |
| Download attachment | `download_chat_attachment` |

For parameters: [references/chat.md](references/chat.md)

### Google Apps Script

| Task | Tool |
|------|------|
| List projects | `list_script_projects` |
| Get project | `get_script_project` |
| Create project | `create_script_project` |
| Delete project | `delete_script_project` |
| Get file content | `get_script_content` |
| Update file content | `update_script_content` |
| Run function | `run_script_function` |
| Generate trigger code | `generate_trigger_code` |
| Manage deployments | `manage_deployment` / `list_deployments` |
| Versions | `create_version` / `get_version` / `list_versions` |
| Execution metrics | `get_script_metrics` |
| Process history | `list_script_processes` |

For parameters: [references/apps-script.md](references/apps-script.md)

### Google Custom Search

| Task | Tool |
|------|------|
| Web search | `search_custom` |
| Get search engine info | `get_search_engine_info` |

For parameters: [references/search.md](references/search.md)

### Auth

| Task | Tool |
|------|------|
| Start OAuth flow | `start_google_auth` |

Parameters: `user_google_email` (string, optional), `service_name` (string, required -- e.g. `"gmail"`, `"drive"`). Legacy OAuth 2.0 only -- disabled when OAuth 2.1 is enabled. In most cases, just call the tool you need and auth happens automatically.

## Common Workflows

### Daily / morning brief
Load [references/daily-brief.md](references/daily-brief.md) and follow it: resolve the day window in
the account's timezone, fetch events (all calendars, accepted + tentative + all-day), pull only the
mail that changes preparation or priority, link mail to meetings without guessing, then present the
brief in its fixed order. Nothing is drafted or created until the user approves it.

### Reply to an email
1. `search_gmail_messages` -- find the email
2. `get_gmail_message_content` -- read it (get `message_id` and `thread_id`)
3. `send_gmail_message` -- reply using `thread_id`; omit reply headers to target the latest non-draft, non-trash message with an RFC `Message-ID`

### Find and share a file
1. `search_drive_files` -- find the file
2. `manage_drive_access` -- share it
3. `get_drive_shareable_link` -- get the link

### Read and update a spreadsheet
1. `get_spreadsheet_info` -- get sheet names
2. `read_sheet_values` -- read current data
3. `modify_sheet_values` -- write updated data
4. `read_sheet_values` -- verify the update

### Create a formatted document
1. `create_doc` -- create the doc
2. `modify_doc_text` -- add text with formatting
3. `insert_doc_elements` -- add tables, lists, page breaks
4. `update_paragraph_style` -- apply heading styles
5. `get_doc_as_markdown` -- verify the result

### Process email attachments
1. `search_gmail_messages` -- find the email
2. `get_gmail_message_content` -- get attachment metadata
3. `get_gmail_attachment_content` -- download the attachment

### Edit a Google Doc
1. `get_doc_as_markdown` -- read current content
2. `inspect_doc_structure` -- find insertion points and indices
3. `modify_doc_text` / `insert_doc_elements` -- make changes
4. `get_doc_as_markdown` -- verify the result

## Tips

- **Check parameters**: run `workspace-mcp --help` for server flags, and read the matching
  `references/<service>.md` for a tool's arguments. There is no `workspace-mcp --cli` mode.
- **Gmail queries**: [references/gmail-search-syntax.md](references/gmail-search-syntax.md) lists
  every supported operator (`is:unread`, `from:`, `newer_than:7d`, `has:attachment`,
  `filename:`, `larger:`, `in:anywhere`, `-from:`, `OR`, quoted phrases) with worked patterns.
- **Email-only user**: if the user needs *just* mail and Workspace OAuth is the blocker,
  `himalaya` is the lighter alternative (Gmail App Password, no Google Cloud project) -- see
  [references/pitfalls.md](references/pitfalls.md).
- **Calendar times**: recurring events must send wall-clock time + `timezone`, not a `+07:00`
  offset. The exact rule and the error it prevents are in [references/pitfalls.md](references/pitfalls.md).
- **Formatting Docs**: before building a document with headings, lists, or tables, load
  [references/docs-layout-workflow.md](references/docs-layout-workflow.md) -- the Docs API
  corrupts styles when content is inserted in one pass.

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
