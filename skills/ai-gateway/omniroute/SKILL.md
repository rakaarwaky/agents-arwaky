---
name: omniroute
description: OmniRoute AI gateway over OpenAI REST. Use when mentioning OmniRoute, OMNIROUTE_URL, providers.
metadata:
  tags: []
---

# OmniRoute

Local AI gateway exposing OpenAI-compatible REST. One endpoint, 359 providers
(150+ free), 1200+ models. Host-native — no container.

## Setup

```bash
export OMNIROUTE_URL="http://localhost:7777"
export OMNIROUTE_KEY="sk-..."          # from ~/.omniroute/storage.sqlite api_keys table, or dashboard
```

All requests: `${OMNIROUTE_URL}/v1/...` with header
`Authorization: Bearer ${OMNIROUTE_KEY}`.

Verify: `curl $OMNIROUTE_URL/v1/models` — an empty list is normal before
providers are configured.

## Discover models

```bash
curl -H "Authorization: Bearer $OMNIROUTE_KEY" $OMNIROUTE_URL/v1/models
```

Use `data[].id` as `model` field in requests. Combos appear with
`owned_by:"combo"`.

## Capability endpoints

| Capability | Path |
|---|---|
| Chat / code-gen | `/v1/chat/completions` |
| Image generation | `/v1/images` |
| Text-to-speech | `/v1/tts` |
| Speech-to-text | `/v1/stt` |
| Embeddings | `/v1/embeddings` |

## Errors

- 401 → set/refresh `OMNIROUTE_KEY`
- 400 `Invalid model format` → check `model` exists in `/v1/models`
- 503 `All accounts unavailable` → wait `retry-after` or add another
  provider account
