---
name: fetch-mcp
description: Use when the user pastes a link to read or learn from. Converts URLs to readable Markdown articles, plain text, raw HTML, structured JSON, and YouTube transcripts. Covers docs pages, blogs, and REST endpoints without a browser.
when-to-use: Use when the user drops a bare URL and says to read it, learn how it works, or asks how to use the linked docs or tool in their project (observed phrasing: learn their duplication logic and see if we can adapt it; gimana carapakai in ike peorject saya; apakah saya bisa instal ini); when converting noisy pages to clean Markdown articles; when fetching structured JSON from REST API endpoints; or when extracting captions or transcripts from YouTube videos.
argument-hint: "mcp-fetch <command> <url> [--max-length N] [--start-index N] [--proxy <URL>] [--lang <code>]"
metadata:
  tags: []
---

# Fetch MCP Server

Fetch MCP is a specialized web extraction and content scraping server that converts arbitrary URLs into clean, token-efficient formats (Markdown, plain text, extracted readable articles, JSON, and YouTube video transcripts).

## When to Use This Skill

Activate this skill when:

- Reading content from external web pages, blogs, or documentation URLs.
- Converting noisy web pages with advertisements and boilerplate into clean Markdown articles.
- Fetching structured JSON payloads from REST API endpoints without invoking heavy browsers.
- Extracting captions or transcripts from YouTube videos for summarization or analysis.

## Tools Overview

| Tool | Purpose | Primary Parameters |
|---|---|---|
| `fetch_readable` | **Preferred**: Extracts the core article using Mozilla Readability, stripping ads, headers, and footers | `url` (required), `max_length`, `proxy` |
| `fetch_markdown` | Fetches entire web page and converts HTML structure directly to Markdown | `url` (required), `max_length`, `proxy` |
| `fetch_txt` | Extracts plain text content, stripping all HTML tags and styling | `url` (required), `max_length`, `proxy` |
| `fetch_html` | Retrieves raw, unparsed HTML source code | `url` (required), `max_length`, `proxy` |
| `fetch_json` | Queries a REST endpoint and returns parsed JSON data | `url` (required), `headers`, `proxy` |
| `fetch_youtube_transcript` | Extracts captions/transcripts from a YouTube video URL | `url` (required), `lang` (default: "en") |

## Common Parameters

- `url` (string, required): Full target URL (including `http://` or `https://`).
- `max_length` (number, optional): Maximum characters returned to prevent context overflow (default: `5000`).
- `start_index` (number, optional): Offset character index for paginated reading of large pages.
- `headers` (object, optional): Custom HTTP request headers (e.g. `User-Agent`, `Authorization`).
- `proxy` (string, optional): HTTP/HTTPS proxy URL if required.

## CLI Usage

The fetch-mcp submodule exposes an `mcp-fetch` CLI (from `vendor/fetch-mcp/dist/cli.js`):

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
