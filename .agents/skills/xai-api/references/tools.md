# Server-Side Tools

> Source: https://docs.x.ai/developers/tools/{overview,function-calling,web-search,x-search,code-execution,collections-search,remote-mcp,citations,streaming-and-sync,tool-usage-details,advanced-usage}.md

All tools are server-side: xAI executes them, you pay per call + tokens. Tool names
differ slightly between the xAI SDK and the OpenAI-compatible Responses API.

## Function Calling

Define a custom tool with `name`, `description`, JSON-schema `parameters`; model returns
a `tool_call`, you execute it locally and return the result.

```python
# xAI SDK
from xai_sdk import Client
from xai_sdk.chat import user, tool, tool_result
client = Client(api_key=os.getenv("XAI_API_KEY"))
tools = [tool(name="get_temperature", description="...",
              parameters={"type":"object", "properties":{...}, "required":["location"]})]
chat = client.chat.create(model="grok-4.6", tools=tools)
chat.append(user("What is the temperature in San Francisco?"))
response = chat.sample()
if response.tool_calls:
    chat.append(response)
    for tc in response.tool_calls:
        args = json.loads(tc.function.arguments)
        result = get_temperature(**args)
        chat.append(tool_result(json.dumps(result)))
    response = chat.sample()
```

Responses API (OpenAI SDK) equivalent: pass `tools=[{"type":"function", "name":..., "parameters":...}]`.
When the model returns a `function_call` item, continue with:
`input=[{"type":"function_call_output", "call_id": item.call_id, "output": json.dumps(result)}]` + `previous_response_id=response.id`.

With streaming, the function call is returned whole in a single chunk, not streamed.
Pydantic models can build tool schemas directly.

## Web Search

`web_search` — search the web + browse pages in real-time.

Params: `allowed_domains` (max 5), `excluded_domains` (max 5) — **cannot combine both in one request**;
`enable_image_understanding`, `enable_image_search`.

```python
# xAI SDK
from xai_sdk.tools import web_search
chat = client.chat.create(model="grok-4.6", tools=[web_search(allowed_domains=["docs.x.ai"])])
```

Responses API: `tools=[{"type":"web_search", "filters":{"allowed_domains":["..."]}}]`.
Citations: `response.citations` (xAI SDK) / `sources` (Vercel AI SDK).

## X Search

`x_search` — search X posts, user profiles, and threads. Same param shape as web search.

## Code Execution

`code_execution` / `code_interpreter` — run Python in a sandboxed environment.
`code_interpreter` unsupported in the gRPC API.

## Collections Search (RAG)

`collections_search` / `file_search` — query uploaded document collections.
Collections API: `POST /v1/collections`, search within a collection, metadata filters.

## Remote MCP Tools

Connect to external MCP servers; xAI proxies the calls. Billed token-based, not per-call.

## In-Depth Topics

- `citations` — how citations are attached to search-derived content.
- `streaming-and-sync` — `include=["verbose_streaming"]` surfaces tool-call progress events live.
- `tool-usage-details` — `response.server_side_tool_usage` shows per-tool invocation counts.
- `advanced-usage` — combining tools, parallel calls (`parallel_tool_calls`), max agentic turns.

## SDK Quick Map

| Capability | xAI SDK | OpenAI Responses API | Vercel AI SDK |
|---|---|---|---|
| Function calling | `tool(...)` | `tools=[{type:"function"}]` | `tool({description, inputSchema, execute})` |
| Web Search | `web_search()` | `{type:"web_search"}` | `xai.tools.webSearch()` |
| X Search | `x_search()` | `{type:"x_search"}` | `xai.tools.xSearch()` |
| Code Execution | `code_execution()` | `{type:"code_execution"}` | — |

## Auth

All REST calls: `Authorization: Bearer $XAI_API_KEY` against `https://api.x.ai/v1`.
For the Grok CLI: `grok login` or set `XAI_API_KEY` (headless/CI: `--device-auth` or env var).
