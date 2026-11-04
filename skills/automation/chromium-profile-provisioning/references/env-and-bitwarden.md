# Env-var format and Bitwarden CLI companion

**Goal:** you can wire one `NAME|user|pass|url` env into both vault items and
browser profiles without drift, and set up the `bw` CLI the vault half needs.

## Single source of truth for the env format

When one `NAME|user|pass|url` env var feeds two subsystems (vault items AND
browser profiles), parse it in exactly one module and alias the old helper to
it — two hand-rolled parsers drift the moment the format changes.

The trailing `url` field is vault-side only: it becomes the item's
`login.uris[].uri` autofill match (Google accounts:
`https://accounts.google.com` — Bitwarden's default base-domain match then
covers mail/drive subdomains). Profile creation ignores it.

Never load such a file with `set -a; source .env` — the `|` separators are
shell pipes and the lines explode. Parse it with python-dotenv
(`dotenv_values` / `load_dotenv`) instead.

## Bitwarden CLI (`bw`) companion setup

The vault half of the flow needs `bw`, which the browser automation does not
bundle:

- Install PINNED: `npm install -g @bitwarden/cli@<latest-release>` — version
  2026.4.0 is flagged malicious by npm threat intelligence, so an unpinned
  resolve can land on it; check `npm view @bitwarden/cli versions` and pick
  the newest non-flagged release.
- If `npm prefix -g` is a node outside PATH (e.g. editor-bundled node), the
  binary installs invisible to `command -v bw`. Symlink it:
  `ln -sf "$(npm prefix -g)/bin/bw" ~/.local/bin/bw`.
- Non-interactive login without exposing the password in argv:
  `bw login <email> --passwordenv BWC_PASSWORD` (export the var first).

## Completion

- Exactly one parser module owns the `NAME|user|pass|url` format; the old
  helper is aliased to it.
- `command -v bw` resolves to a pinned, non-flagged release.
