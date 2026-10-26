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

For the `query` syntax, read [references/gmail-search-syntax.md](references/gmail-search-syntax.md) before composing Gmail searches.

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

### Google Calendar

| Task | Tool |
|------|------|
| List calendars | `list_calendars` |
| Get events | `get_events` |
| Create/update/delete event | `manage_event` |
| Check availability | `query_freebusy` |

Read [references/pitfalls.md](references/pitfalls.md) first for the recurring-event timezone rule and the secondary-calendar 404s.

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

For multi-step layout work (headings, lists, tables), also follow [references/docs-layout-workflow.md](references/docs-layout-workflow.md).

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

### Google Forms

| Task | Tool |
|------|------|
| Get form | `get_form` |
| Create form | `create_form` |
| Batch update form | `batch_update_form` |
| List responses | `list_form_responses` |
| Get one response | `get_form_response` |
| Publish settings | `set_publish_settings` |

### Google Tasks

| Task | Tool |
|------|------|
| List task lists | `list_task_lists` |
| Get task list | `get_task_list` |
| Manage task list (CRUD) | `manage_task_list` |
| List tasks | `list_tasks` |
| Get task | `get_task` |
| Manage task (CRUD/move) | `manage_task` |

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

### Google Custom Search

| Task | Tool |
|------|------|
| Web search | `search_custom` |
| Get search engine info | `get_search_engine_info` |

### Auth

| Task | Tool |
|------|------|
| Start OAuth flow | `start_google_auth` |

Parameters: `user_google_email` (string, optional), `service_name` (string, required -- e.g. `"gmail"`, `"drive"`). Legacy OAuth 2.0 only -- disabled when OAuth 2.1 is enabled. In most cases, just call the tool you need and auth happens automatically.

