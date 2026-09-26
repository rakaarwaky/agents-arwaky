# Models & Pricing

> Source: https://docs.x.ai/developers/models.md · https://docs.x.ai/developers/pricing.md
> Knowledge cut-off for grok-4.6: February 1, 2026.

## Text Model Pricing (per 1M tokens, USD)

| Model | Context | Input | Cached input | Output |
|---|---|---|---|---|
| grok-4.6 (< 200k prompt) | 500k | $2.00 | $0.50 | $6.00 |
| grok-4.6 (≥ 200k prompt) | 500k | $4.00 | $1.00 | $12.00 |
| grok-4.5 (< 200k prompt) | 500k | $2.00 | $0.30 | $6.00 |
| grok-4.5 (≥ 200k prompt) | 500k | $4.00 | $0.60 | $12.00 |
| grok-4.3 (< 200k prompt) | 1M | $1.25 | $0.20 | $2.50 |
| grok-4.3 (≥ 200k prompt) | 1M | $2.50 | $0.40 | $5.00 |
| grok-4.20-0309-reasoning | 1M | $1.25–$2.50 | $0.20–$0.40 | $2.50–$5.00 |
| grok-4.20-0309-non-reasoning | 1M | $1.25–$2.50 | $0.20–$0.40 | $2.50–$5.00 |
| grok-build-0.1 (< 200k prompt) | 256k | $1.00 | $0.20 | $2.00 |
| grok-build-0.1 (≥ 200k prompt) | 256k | $2.00 | $0.40 | $4.00 |
| grok-4.20-multi-agent-0309 | 1M | $1.25–$2.50 | $0.20–$0.40 | $2.50–$5.00 |

Long-context pricing: when a request's prompt reaches the listed threshold, ALL tokens
in that request are billed at the higher rate.

## Model aliases

- `<modelname>` → latest stable version (auto-updates).
- `<modelname>-latest` → latest version, including unreleased features.
- `<modelname>-<date>` → pinned to a specific release; never updated.

Recommended: use the bare alias or `-latest` unless a workflow demands pinning.

## Which model for what

- Code + general: `grok-4.6` (flagship, 500k context).
- Coding agent (Grok Build): `grok-build-0.1` (256k context, cheaper).
- Images: `grok-imagine-image-2.0` ($0.04/image), `grok-imagine-image-quality` ($0.05).
- Video: `grok-imagine-video-1.5` ($0.080/sec), `grok-imagine-video` ($0.050/sec).
- Voice: `grok-voice-think-fast-2.0` — $0.08/min ($4.80/hr) audio + $0.004/text input.
- STT: $0.10/hr REST, $0.20/hr streaming. TTS: $15.00/1M chars.

## Key model behaviours

- No realtime knowledge without enabling `web_search` / `x_search` tools.
- Chat models: no role-order limitation — `system`/`user`/`assistant` can be mixed freely.
- `logprobs` / `top_logprobs` silently ignored on `grok-4.20`+ models.
- Image input: max 20 MiB per image; no limit on count; jpg/jpeg/png; any text/image order.
- Batch API: not all models support it — check each model page.
- `max_output_tokens` defaults to 128,000; set explicitly for long generations.

## Tool invocation pricing (per 1k calls)

| Tool | Tool name | Cost/1k |
|---|---|---|
| Web Search | `web_search` | $5 |
| X Search | `x_search` | $5 (from 2026-09-21: $5/1k posts, $10/1k user profiles) |
| Code Execution | `code_execution`, `code_interpreter` | $5 |
| Image Generation | `image_generation` | Imagine API rates |
| File Attachments | `attachment_search` | $10 |
| Collections Search (RAG) | `collections_search`, `file_search` | $2.50 |
| Image Understanding | `view_image` | token-based (no tool-call fee) |
| X Video Understanding | `view_x_video` | token-based |
| Remote MCP Tools | set by MCP server | token-based |

Note: `code_interpreter` and `file_search` are not supported in the gRPC API.
