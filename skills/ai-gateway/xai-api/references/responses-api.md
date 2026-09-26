# Responses API

> Source: https://docs.x.ai/developers/rest-api-reference/inference/responses.md

Primary interface for text generation, reasoning, and tool use.

## POST /v1/responses

Request body fields:

| Field | Notes |
|---|---|
| `input` | Required. String or array of message objects (role + content). |
| `model` | Model name, e.g. `grok-4.6`. |
| `instructions` | Alternate system prompt. **Cannot be combined with `previous_response_id`** — the previous response's system prompt is used instead. |
| `previous_response_id` | Continue a prior conversation without resending context. Responses stored 30 days. |
| `max_output_tokens` | Includes output + reasoning tokens. Default 128,000. |
| `max_turns` | Max agentic tool-calling turns; ignored for non-agentic requests. |
| `reasoning.effort` | Constrains thinking depth. Supported values depend on model. |
| `reasoning_effort` | Non-standard alias; only read when `reasoning` field is unset. |
| `parallel_tool_calls` | Allow parallel tool calls. |
| `search_parameters` | `from_date`, `to_date` (ISO-8601) to bound web/X search results. |
| `prompt_cache_key` | Stable key for sticky routing / prompt-cache hits; plumbed to `x-grok-conv-id`. |
| `min_p` | Min-p sampling; disabled when unset. |
| `logprobs` | Silently ignored on `grok-4.20`+ models. |
| `include` | `reasoning.encrypted_content`, tool-output options. OpenAI `message.output_text.logprobs` accepted but ignored. |
| `background` | Unsupported. |
| `context_management` | Parsed but not yet executed. |
| `metadata` | Not supported; compatibility only. |

## Response shape

Response items include `type`:
- `message` — final text; content is an array of parts.
- `function_call` — `call_id`, `name`, `arguments` (JSON string).
- `reasoning` — internal thinking (encrypted or summary depending on `include`).
- `web_search_call`, `x_search_call` — server-side tool invocations.

Continue a conversation by passing `previous_response_id=response.id` on the next call.

## Quickstart (Python, OpenAI SDK)

```python
from openai import OpenAI
client = OpenAI(api_key="<XAI_API_KEY>", base_url="https://api.x.ai/v1")
resp = client.responses.create(
    model="grok-4.6",
    input=[{"role": "user", "content": "Fix this function and explain the bug: ..."}],
)
print(resp.output[0].content[0].text)
```

## Quickstart (xAI SDK)

```python
from xai_sdk import Client
from xai_sdk.chat import user
client = Client(api_key="<XAI_API_KEY>")
chat = client.chat.create(model="grok-4.6")
chat.append(user("..."))
response = chat.sample()
print(response.content)
```

## cURL

```bash
curl https://api.x.ai/v1/responses \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4.6", "input": "Fix this function: ..."}'
```

## Chat Completions (legacy)

Endpoint: `POST /v1/chat/completions`. Stateless, OpenAI-compatible. New integrations
should use the Responses API. Key differences:
- `deferred: true` returns a `request_id`; poll via `GET /v1/chat/deferred-completion/{request_id}`.
- `max_completion_tokens` replaces deprecated `max_tokens`.
- `presence_penalty` / `frequency_penalty` not supported on reasoning models.
