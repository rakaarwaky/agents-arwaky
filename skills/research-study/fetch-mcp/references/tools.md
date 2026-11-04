# Tools — Fetch MCP

| Tool | Purpose | Primary Parameters |
|---|---|---|
| `fetch_readable` | **Preferred**: Extracts the core article using Mozilla Readability, stripping ads, headers, and footers | `url` (required), `max_length`, `proxy` |
| `fetch_markdown` | Fetches entire web page and converts HTML structure directly to Markdown | `url` (required), `max_length`, `proxy` |
| `fetch_txt` | Extracts plain text content, stripping all HTML tags and styling | `url` (required), `max_length`, `proxy` |
| `fetch_html` | Retrieves raw, unparsed HTML source code | `url` (required), `max_length`, `proxy` |
| `fetch_json` | Queries a REST endpoint and returns parsed JSON data | `url` (required), `headers`, `proxy` |
| `fetch_youtube_transcript` | Extracts captions/transcripts from a YouTube video URL | `url` (required), `lang` (default: `"en"`) |

## CLI Usage

The fetch-mcp submodule exposes an `mcp-fetch` CLI (from
`vendor/fetch-mcp/dist/cli.js`):

```bash
# Fetch and convert URL to readable article markdown
mcp-fetch readable "https://example.com/article"

# Fetch URL as raw HTML
mcp-fetch html "https://example.com/page"

# Fetch plain text with a length cap
mcp-fetch txt "https://example.com/page" --max-length 5000

# Paginated read of a large page
mcp-fetch markdown "https://example.com/long-page" --start-index 5000

# Fetch a REST endpoint as JSON
mcp-fetch json "https://api.example.com/data"

# Extract YouTube transcript
mcp-fetch youtube "https://www.youtube.com/watch?v=VIDEO_ID" --lang en
```

Available commands: `html`, `markdown`, `readable`, `txt`, `json`, `youtube`.
Flags: `--max-length <N>`, `--start-index <N>`, `--proxy <URL>`, `--lang <code>`.
