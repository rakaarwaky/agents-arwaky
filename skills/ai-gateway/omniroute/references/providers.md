# Provider keys

Most providers need no key — the free-tier catalogue is what makes the gateway useful out of
the box. Add keys with `omniroute setup` (walks through it and stores them in the database),
or via the dashboard at `http://127.0.0.1:7777`. Both write to `storage.sqlite`, so they need
no edit to `~/.omniroute/.env`.

`STORAGE_ENCRYPTION_KEY` encrypts stored credentials at rest. **Never change it** once
credentials exist; see `references/setup.md` for the full warning.

To add a custom OpenAI-compatible provider, see [`references/custom-provider.md`](references/custom-provider.md).

## Manage the daemon

```bash
aa omniroute status            # process, systemd, ports, API readiness
aa omniroute restart           # needed after any env edit
aa omniroute logs              # journalctl tail
aa omniroute models            # /v1/models through the gateway
aa omniroute service-install   # 24/7 systemd user unit + enable-linger
```

Also upstream, for settings the `aa` verbs do not cover:

```bash
omniroute doctor              # environment + config diagnostics
omniroute keys                # mint/revoke API keys
omniroute cost                # spend report
omniroute status              # upstream's own view
```
