# Notion `ntn` CLI Reference (Path A)

Notion's official CLI. Shorter syntax than the raw HTTP path, one-line file uploads, and the only path that supports Workers. macOS + Linux only as of May 2026 (Windows support "coming soon"). **Default when installed.**

## Setup

### Get an integration token (required for both paths)

1. Create an integration at https://notion.so/my-integrations
2. Copy the API key (starts with `ntn_` or `secret_`)
3. Store in `${HERMES_HOME:-~/.hermes}/.env`:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. **Share target pages/databases with the integration** in Notion: page menu `...` → `Connect to` → your integration name. Without this, the API returns 404 for that page even though it exists.

### Install `ntn`

```bash
# Recommended
curl -fsSL https://ntn.dev | bash

# Or via npm (needs Node 22+, npm 10+)
npm install --global ntn

ntn --version    # verify
```

**Skip `ntn login` — use the integration token instead.** This works headlessly, no browser needed:

```bash
export NOTION_API_TOKEN=$NOTION_API_KEY      # ntn reads NOTION_API_TOKEN
export NOTION_KEYRING=0                       # don't try to use the OS keychain
```

Add those exports to your shell profile (or to `${HERMES_HOME:-~/.hermes}/.env`) so every session inherits them.

### Choose path at runtime

```bash
if command -v ntn >/dev/null 2>&1; then
  # use ntn
else
  # fall back to curl — see http-path.md
fi
```

Windows users: skip the `ntn` install entirely until native support ships — Path B (`references/http-path.md`) works fine. If you want CLI ergonomics now, install `ntn` inside WSL2.

## API Basics

`Notion-Version: 2025-09-03` is required on all HTTP requests. `ntn` handles this for you. In this version, what users call "databases" are called **data sources** in the API.

## Raw API calls (shorthand for curl)

```bash
ntn api v1/users                                  # GET
# POST with inline body
ntn api v1/pages parent[page_id]=abc123 \
  properties[title][0][text][content]="Notes"
ntn api v1/pages/abc123 -X PATCH archived:=true   # PATCH; := is non-string (bool/num/null)
```

Syntax notes:
- `key=value` — string fields
- `key[nested]=value` — nested object fields
- `key:=value` — typed assignment (booleans, numbers, null, arrays)

## Search

```bash
ntn api v1/search query="page title"
```

## Read page metadata

```bash
ntn api v1/pages/{page_id}
```

## Read page as Markdown (agent-friendly)

```bash
ntn api v1/pages/{page_id}/markdown
```

## Read page content as blocks

```bash
ntn api v1/blocks/{page_id}/children
```

## Create page from Markdown

```bash
ntn api v1/pages \
  parent[page_id]=xxx \
  properties[title][0][text][content]="Notes from meeting" \
  markdown="# Agenda

- Q3 roadmap
- Hiring"
```

## Patch a page with Markdown

```bash
ntn api v1/pages/{page_id}/markdown -X PATCH \
  markdown="## Update

Shipped the prototype."
```

## Query a database (data source)

```bash
ntn api v1/data_sources/{data_source_id}/query -X POST \
  filter[property]=Status filter[select][equals]=Active
```

For complex queries with `sorts`, multiple filter clauses, or compound logic, pipe JSON in:

```bash
echo '{"filter": {"property": "Status", "select": {"equals": "Active"}}, "sorts": [{"property": "Date", "direction": "descending"}]}' | \
  ntn api v1/data_sources/{data_source_id}/query -X POST --json -
```

## File uploads (one-liner — biggest CLI win)

```bash
ntn files create < photo.png
ntn files create --external-url https://example.com/photo.png
ntn files list
```

Compare to the 3-step HTTP flow in `references/http-path.md` (create upload → PUT bytes → reference).

## Useful env vars

| Var | Effect |
|---|---|
| `NOTION_API_TOKEN` | Auth token (overrides keychain) — set this to your integration token |
| `NOTION_KEYRING=0` | File-based creds at `~/.config/notion/auth.json` instead of OS keychain |
| `NOTION_WORKSPACE_ID` | Skip the workspace picker prompt |

## Choosing the Right Path

| Task | mac / Linux | Windows |
|---|---|---|
| Read/write pages, search, query databases | `ntn api ...` | curl |
| Read a page for an agent to summarize | `ntn api v1/pages/{id}/markdown` | curl `/markdown` endpoint |
| Upload a file | `ntn files create < file` | 3-step HTTP flow |
| One-off API exploration | `ntn api ...` | curl |
| Build a sync / webhook / agent tool hosted by Notion | `ntn workers ...` | WSL2 + `ntn workers ...` |

## Notes

- Page/database IDs are UUIDs (with or without dashes — both accepted).
- Rate limit: ~3 requests/second average. The CLI doesn't bypass this.
- The API cannot set database **view** filters — that's UI-only.
- Use `"is_inline": true` when creating data sources to embed them in a page.
- Always pass `-s` to curl to suppress progress bars (cleaner agent output).
- Pipe JSON through `jq` when reading: `... | jq '.results[0].properties'`.
- Notion also ships an MCP server now (`Notion MCP`, ~91% more token-efficient on DB ops than the previous version) — wire it via Hermes' MCP support if you want streaming Notion access from inside a session, but the paths above are enough for most one-shot tasks.
