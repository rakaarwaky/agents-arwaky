# Add a custom OpenAI-compatible provider

A custom provider = one **provider node** (base URL + optional auth headers, stored under
prefix) + one **provider connection** (the API key) + optional **manual model overrides**
(so the models are routable without a discovery call). Three parts:

```bash
# 1. Authenticate a dashboard session (password comes from ~/.omniroute/.env DASHBOARD_PASSWORD).
COOKIE=/tmp/omni-cookies.txt
curl -s -c "$COOKIE" http://127.0.0.1:7777/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"<DASHBOARD_PASSWORD>"}'

# 2a. Create the node (name + prefix are required; pick a short unique prefix).
NODE_ID=$(curl -s -b "$COOKIE" http://127.0.0.1:7777/api/provider-nodes \
  -H 'Content-Type: application/json' \
  -d '{"name":"YJS","prefix":"yjs","apiType":"chat","baseUrl":"https://api.yjs.im/v1","type":"openai-compatible"}' \
  | jq -r .node.id)

# 2b. Attach the API key as a connection, defaulting to a model.
curl -s -b "$COOKIE" http://127.0.0.1:7777/api/providers \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"$NODE_ID\",\"name\":\"yjs.im\",\"apiKey\":\"sk-...\",\"defaultModel\":\"<model-id>\"}"

# 2c. Activate it.
CONN_ID=<connection id from 2b>
curl -s -b "$COOKIE" -X PUT "http://127.0.0.1:7777/api/providers/$CONN_ID" \
  -H 'Content-Type: application/json' -d '{"isActive":true}'

# 3. Add manual model overrides (skips live discovery; safe for free/limited endpoints).
for M in deepseek-v4-flash-0731 deepseek-v4-flash-vision; do
  curl -s -b "$COOKIE" http://127.0.0.1:7777/api/provider-models \
    -H 'Content-Type: application/json' \
    -d "{\"provider\":\"$NODE_ID\",\"modelId\":\"$M\",\"source\":\"manual\",
         \"apiFormat\":\"chat-completions\",\"supportedEndpoints\":[\"chat\"],
         \"max_input_tokens\":65536,\"max_output_tokens\":8192}"
done

# 4. Verify: models appear under the prefix; try one through the gateway.
curl http://127.0.0.1:7777/v1/models -H "Authorization: Bearer $OMNIROUTE_KEY" \
  | jq -r '.data[].id' | grep '^yjs/'
curl http://127.0.0.1:7777/v1/chat/completions \
  -H "Authorization: Bearer $OMNIROUTE_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"yjs/deepseek-v4-flash-0731","messages":[{"role":"user","content":"ok"}]}'
```

Notes:

- Node `baseUrl` must end with `/v1` (the OpenAI-compatible root). Custom HTTP headers can
  be passed on the node (`customHeaders`) instead of the connection's key.
- A bare inference key (`OMNIROUTE_KEY` with only `["self:usage"]` scope) cannot write to
  the management API. Use the dashboard password session, a `manage`-scope key, or the local
  CLI token.
- No daemon restart is needed after node/connection/model writes; the gateway picks them up
  on the next request.

## CLI equivalents

The CLI mirrors the management API, so when the `omniroute` shell wrapper works you can do:

```bash
omniroute providers add yjs --credential sk-... --default-model deepseek-v4-flash-0731
omniroute models add yjs deepseek-v4-flash-0731 --api-format chat-completions
omniroute models add yjs deepseek-v4-flash-vision --api-format chat-completions
omniroute providers test yjs
```

If the `omniroute` shell wrapper errors out (`ModuleNotFoundError: surface_daemon_command`
on some installs), call the real entry directly:

```bash
node "$(npm root -g)/omniroute/bin/omniroute.mjs" <subcommand> ...
```

On this machine that resolves to
`node /home/raka/.local/share/nodejs/node-v24.11.0-linux-x64/lib/node_modules/omniroute/bin/omniroute.mjs`.
The CLI's management calls also 401 without a `manage`-scope key, so fall back to the
dashboard-password `curl` flow above.
