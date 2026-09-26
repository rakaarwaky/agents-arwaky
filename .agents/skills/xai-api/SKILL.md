---
name: xai-api
description: "Grok API and Grok Build CLI reference." # 39 chars — safe
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags:
      - xAI
      - Grok
      - API
      - Coding Agent
      - 9Router
---

# xAI / Grok API & Grok Build CLI

Reference skill covering the xAI Grok API (https://api.x.ai/v1) and the Grok Build CLI (`grok` binary). Use it when working with Grok models, the Responses API, server-side tools, or when delegating coding to the `grok` headless CLI. Source: https://docs.x.ai — every page is also available as markdown by appending `.md` to the URL (e.g. `https://docs.x.ai/developers/models.md`).

## When to Use

- Choosing a Grok model or checking pricing for a specific model.
- Calling the xAI REST API (Responses, Chat Completions, Images, Voice).
- Using server-side tools: function calling, web search, X search, code execution, structured outputs.
- Driving the `grok` CLI headlessly for coding tasks (delegation pattern).
- Configuring 9Router / custom providers with xAI models.
- Checking rate limits or prompt caching behaviour.

## Quick Reference

| What | Where |
|------|-------|
| Models + pricing | `references/models-pricing.md` |
| Responses API | `references/responses-api.md` |
| Function calling + tools | `references/tools.md` |
| Structured outputs | `references/structured-outputs.md` |
| Rate limits + tiers | `references/rate-limits.md` |
| Grok Build CLI (headless) | `references/grok-build-cli.md` |
| Grok Build features (sessions, worktrees, permissions) | `references/grok-build-features.md` |

## Key Facts (always in context)

- Base URL: `https://api.x.ai/v1`. Auth: `Authorization: Bearer $XAI_API_KEY`.
- Flagship model: `grok-4.6` (500k context, $2.00/$6.00 per 1M in/out tokens <200k prompt).
- Grok Build model: `grok-build-0.1` (256k context, $1.00/$2.00 per 1M tokens <200k prompt).
- The Grok CLI binary is `grok` (installed at `~/.local/bin/grok`, config at `~/.grok/`).
- Headless coding: `grok -p "<brief>" --output-format json --always-approve` — the `-p` flag DOES exist (verified in docs); earlier local `--help` output was misleading.
- 9Router proxies xAI models via `base_url: http://localhost:20128/v1`.

## Load on demand

Use `skill_view(name='xai-api', file_path='references/<file>')` to load a chapter when needed:

- `references/models-pricing.md` — full model table, pricing tiers, model aliases, context limits.
- `references/responses-api.md` — POST /v1/responses request body fields, response shape, conversation continuation.
- `references/tools.md` — function calling, web search, X search, code execution, collections search, remote MCP; tool pricing.
- `references/structured-outputs.md` — JSON schema support, response_format, Pydantic/Zod usage, constraint limits.
- `references/rate-limits.md` — tier thresholds, per-model RPS/TPM tables, 429 handling.
- `references/grok-build-cli.md` — `grok` subcommands, headless flags, ACP, session management.
- `references/grok-build-features.md` — sessions, worktrees, permissions, sandbox, subagents, hooks, MCP servers.

## Pitfalls

- `logprobs` / `top_logprobs` are silently ignored on `grok-4.20`+ models.
- Long-context pricing: requests with ≥200k prompt tokens are billed at the higher rate for ALL tokens, not just the overflow.
- `allowed_domains` and `excluded_domains` cannot be set together in one Web Search request.
- `max_output_tokens` defaults to 128,000 — set it explicitly for long generations.
- `previous_response_id` + `instructions` are mutually exclusive; the previous response's system prompt is used instead.
- Batch API: not all models support it; check each model page.
- `grok` sessions live in `~/.grok/sessions/`; worktrees in `~/.grok/worktrees/` and persist after the session ends.
