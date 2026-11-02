# Setup

```bash
export OMNIROUTE_URL="http://127.0.0.1:7777"      # dashboard and API share one port
export OMNIROUTE_KEY="sk-..."                      # from the dashboard, or `omniroute keys`
```

All requests: `${OMNIROUTE_URL}/v1/...` with header `Authorization: Bearer ${OMNIROUTE_KEY}`.

Verify: `curl $OMNIROUTE_URL/v1/models -H "Authorization: Bearer $OMNIROUTE_KEY"`

## Config lives in `~/.omniroute/.env`

OmniRoute owns its own working directory — `~/.omniroute/` holds `.env`, `storage.sqlite`,
and `logs/`. This is **not** the repo's `~/.config/<tool>/` layout, and it is deliberate:
upstream reads `.env` from its working directory, so pointing the unit anywhere else
silently loses the settings.

`STORAGE_ENCRYPTION_KEY` in that file encrypts every provider credential in
`storage.sqlite`. **Never rotate it and never let a tool regenerate it** — the database
becomes unreadable while still looking healthy. Edit the file by hand; the `aa` verbs never
write to it.

Override the port with `OMNIROUTE_PORT`, or edit `PORT` in `~/.omniroute/.env` and restart.
