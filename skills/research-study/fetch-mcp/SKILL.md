---
name: fetch-mcp
description: Scrapes web to markdown with transcripts. Use when extracting articles, HTML, YouTube text.
when-to-use: Use when reading content from external web pages, blogs, or documentation URLs; converting noisy pages to clean Markdown articles; fetching structured JSON from REST API endpoints; or extracting captions/transcripts from YouTube videos.
argument-hint: "mcp-fetch <command> <url> [--max-length N] [--start-index N] [--proxy <URL>] [--lang <code>]"
metadata:
  tags: []
---

# Fetch MCP Server

Fetch MCP is a specialized web extraction and content scraping server that
converts arbitrary URLs into clean, token-efficient formats (Markdown, plain
text, extracted readable articles, JSON, and YouTube video transcripts).

## Global rules

- **`fetch_readable` is preferred** for article content — it uses Mozilla
  Readability, stripping ads, headers, and footers. Use `fetch_markdown`
  when you need the full page structure, `fetch_txt` for raw plain text,
  `fetch_html` for unparsed source, and `fetch_json` for REST endpoints.
- **`max_length` defaults to 5 000.** Raise it only when the content
  genuinely needs more; use `start_index` to page through large documents
  rather than dumping everything at once.
- **YouTube transcripts** come from `fetch_youtube_transcript`; `lang`
  defaults to `"en"`.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Tools | [`references/tools.md`](references/tools.md) | Per-tool parameters and CLI examples for all six fetch commands (`html`, `markdown`, `readable`, `txt`, `json`, `youtube`). |
| Shared parameters | `url` (required), `max_length` (default 5000), `start_index` (pagination offset), `headers` (custom HTTP), `proxy` | Same parameter set across all tools except `fetch_youtube_transcript` (uses `lang` instead of `headers`). |
| CLI | `mcp-fetch <command> <url> [flags]` — available commands: `html`, `markdown`, `readable`, `txt`, `json`, `youtube`; flags: `--max-length <N>`, `--start-index <N>`, `--proxy <URL>`, `--lang <code>` | The `mcp-fetch` CLI wraps the MCP server (from `vendor/fetch-mcp/dist/cli.js`). |
