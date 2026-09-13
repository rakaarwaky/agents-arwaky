---
name: fetch-mcp
description: Clean web scraping, article extraction, HTML-to-markdown conversion, and YouTube transcript retrieval for AI agents.
version: 1.0.0
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

## CLI & Orchestrator Usage

You can also run fetch commands directly via the `agents-arwaky` CLI:

```bash
# Fetch and convert URL to markdown
aa run fetch-mcp fetch_readable "https://example.com/article"

# Extract YouTube transcript
aa run fetch-mcp fetch_youtube_transcript "https://www.youtube.com/watch?v=VIDEO_ID"
```
