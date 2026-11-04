---
name: gif-search
description: "Searches and downloads GIFs from Tenor via curl + jq using the Tenor API."
when-to-use: "Use when the user wants to search or download GIFs from Tenor — reaction GIFs, visual content for chat, or GIF metadata via the Tenor API with curl + jq."
argument-hint: "<query> [--limit N] [--media-filter gif|tinygif|mp4|tinymp4|webm] [--contentfilter off|low|medium|high] [--locale LOC]"
---

# GIF Search (Tenor API)

You search and download GIFs directly via the Tenor API using curl + jq. No extra tools needed; every command is one curl call piped to jq.

## Global Rules

- **Auth**: every call needs `key=${TENOR_API_KEY}`. Set the key in `${HERMES_HOME:-~/.hermes}/.env` (setup steps in `references/setup.md`).
- **Query encoding**: URL-encode the query — spaces as `+`, special chars as `%XX`.
- **Format choice**: for sending in chat, `tinygif` URLs are lighter; full-quality `gif` is the default otherwise (format table in `references/api.md`).

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Setup | [`references/setup.md`](references/setup.md) | Tenor API key acquisition and `TENOR_API_KEY` env setup; prerequisite CLIs. |
| Search / download / metadata | [`references/api.md`](references/api.md) | curl + jq recipes, API parameter table, and available media formats. |
