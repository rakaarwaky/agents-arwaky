# Google Workspace Common Workflows

## Daily / morning brief

Load [daily-brief.md](daily-brief.md) and follow it: resolve the day window in
the account's timezone, fetch events (all calendars, accepted + tentative + all-day), pull only the
mail that changes preparation or priority, link mail to meetings without guessing, then present the
brief in its fixed order. Nothing is drafted or created until the user approves it.

## Reply to an email

1. `search_gmail_messages` -- find the email
2. `get_gmail_message_content` -- read it (get `message_id` and `thread_id`)
3. `send_gmail_message` -- reply using `thread_id`; omit reply headers to target the latest non-draft, non-trash message with an RFC `Message-ID`

## Find and share a file

1. `search_drive_files` -- find the file
2. `manage_drive_access` -- share it
3. `get_drive_shareable_link` -- get the link

## Read and update a spreadsheet

1. `get_spreadsheet_info` -- get sheet names
2. `read_sheet_values` -- read current data
3. `modify_sheet_values` -- write updated data
4. `read_sheet_values` -- verify the update

## Create a formatted document

1. `create_doc` -- create the doc
2. `modify_doc_text` -- add text with formatting
3. `insert_doc_elements` -- add tables, lists, page breaks
4. `update_paragraph_style` -- apply heading styles
5. `get_doc_as_markdown` -- verify the result

## Process email attachments

1. `search_gmail_messages` -- find the email
2. `get_gmail_message_content` -- get attachment metadata
3. `get_gmail_attachment_content` -- download the attachment

## Edit a Google Doc

1. `get_doc_as_markdown` -- read current content
2. `inspect_doc_structure` -- find insertion points and indices
3. `modify_doc_text` / `insert_doc_elements` -- make changes
4. `get_doc_as_markdown` -- verify the result

## Tips

- **Check parameters**: run `workspace-mcp --help` for server flags, and read the matching
  `<service>.md` for a tool's arguments. There is no `workspace-mcp --cli` mode.
- **Gmail queries**: [gmail-search-syntax.md](gmail-search-syntax.md) lists
  every supported operator (`is:unread`, `from:`, `newer_than:7d`, `has:attachment`,
  `filename:`, `larger:`, `in:anywhere`, `-from:`, `OR`, quoted phrases) with worked patterns.
- **Email-only user**: if the user needs *just* mail and Workspace OAuth is the blocker,
  `himalaya` is the lighter alternative (Gmail App Password, no Google Cloud project) -- see
  [pitfalls.md](pitfalls.md).
- **Calendar times**: recurring events must send wall-clock time + `timezone`, not a `+07:00`
  offset. The exact rule and the error it prevents are in [pitfalls.md](pitfalls.md).
- **Formatting Docs**: before building a document with headings, lists, or tables, load
  [docs-layout-workflow.md](docs-layout-workflow.md) -- the Docs API
  corrupts styles when content is inserted in one pass.
