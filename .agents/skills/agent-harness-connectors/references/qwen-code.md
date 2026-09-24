# Qwen Code (qwen / qwa) provider + auth wiring

Installed standalone at `~/.local/lib/qwen-code/` (launcher `~/.local/bin/qwen`),
not via npm global. Home dir `~/.qwen` (override with `QWEN_HOME`). Settings are
plain JSON (`$version: 4`) at `~/.qwen/settings.json`.

## Where its docs live locally (read these before guessing config keys)

`~/.local/lib/qwen-code/lib/bundled/qc-helper/docs/configuration/`
— `model-providers.md`, `settings.md`, `auth.md`. Grep them for the key in
question; the shipped docs match the installed version exactly, unlike the web.

## Auth resolution chain

`security.auth.selectedType` picks the protocol (`openai`, `anthropic`,
`gemini`, `vertex-ai`, `qwen-oauth`). A custom provider id must be mapped via
top-level `providerProtocol`, else its whole entry is skipped silently.
For a `modelProviders.openai[]` entry:

- `id` required; `envKey` optional and recommended (omitted → falls back to
  `OPENAI_API_KEY`).
- Credential comes from `process.env[envKey]` — **the key value is never read
  from the provider entry itself**.
- Models are matched by `id` + `baseUrl` within an authType. Duplicate pairs:
  first wins, later ones skipped with a warning.
- `env` in settings.json seeds process env, so a wizard-stored
  `QWEN_CUSTOM_API_KEY_OPENAI_<hashed-url>` entry competes with `~/.qwen/.env`.
- A variable already in the inherited process env wins over `~/.qwen/.env`
  (dotenv does not override): a stale `NINEROUTER_KEY` exported from
  `~/.config/environment.d/9router.conf` at login silently shadows the correct
  value in the file, so every fresh terminal 401s despite perfect config.

## Working 9Router binding

```json
{
  "model": { "name": "9router", "baseUrl": "http://127.0.0.1:20128/v1" },
  "modelProviders": { "openai": [ {
      "id": "my9router", "name": "9router",
      "baseUrl": "http://127.0.0.1:20128/v1",
      "envKey": "NINEROUTER_KEY" } ] },
  "security": { "auth": { "selectedType": "openai" } }
}
```

`NINEROUTER_KEY` comes from `~/.qwen/.env`, written by
`aa connect qwen`, which also rewrites the login-session layer
`~/.config/environment.d/9router.conf` so inherited exports cannot shadow it.
Keep NO `env` block in settings.json for that provider — if
the `/auth` Custom Provider wizard added one, remove it, or a rotated router key
will 401 while `.env` looks correct.

## Headless verification

```bash
cd ~ && qwen -p "sapa singkat" --yolo
```
Success = a normal reply, no `API Error: 401 Invalid API key`.
Expected harmless noise: the yolo/no-sandbox warning, and an MCP-failed-to-start
list (that is the command-name issue in the parent skill, not auth).

## Connector side

`tools/connect/qwencode_adapter.py` → `sync_router_provider()` runs after
`inject_9router_env()`: it binds the `my9router` entry to `NINEROUTER_KEY`,
normalizes `baseUrl` to `<router>/v1`, sets `model.name`/`model.baseUrl`, drops
any `QWEN_CUSTOM_API_KEY_*` inline shadow, then does a live
`POST /v1/chat/completions` probe with the effective key and logs pass/fail.
Treat a live-check failure in `aa connect qwen` output as the real signal, not
the surrounding "connect complete" line.

## Other harnesses (same class of work, less detail)

- Hermes: `~/.hermes/config.yaml` (YAML — go through `engine.py`), env at
  `~/.hermes/.env` plus every `~/.hermes/profiles/*/.env`.
- OpenCode: `$XDG_CONFIG_HOME/opencode/opencode.jsonc` (JSONC — comment
  preservation matters) and `~/.config/opencode/.env`.
- Antigravity: env files in `~/.gemini/config/`, `~/.gemini/antigravity-cli/`,
  `~/.gemini/antigravity/`.
