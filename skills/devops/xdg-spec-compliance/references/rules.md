# The rules projects break

Authoritative text:
https://specifications.freedesktop.org/basedir/latest/ (v0.8). Quote
it rather than reasoning from memory — three rules are routinely
guessed wrong.

**Goal:** every resolved path in the repo satisfies all seven rules.

## Absolute only

A relative value is *invalid and must be ignored* (fall back to the
default). Use `Path(raw).is_absolute()` — do NOT `expanduser()`
first: a literal `~/` that survives into the env was never
shell-expanded, and `Path('~/x').expanduser()` is absolute, so
expanding it silently writes `$HOME/x/bwc`. Reject it and warn.

## Empty/unset both mean "use default"

`(env.get(v) or "").strip()`.

## Auto-created dirs are 0700

`mkdir(parents=True)` inherits umask (0775 on desktops), so
`~/.local/state/app` and its `app.log` end up group/world readable.
chmod the leaf AND every ancestor this call newly creates; leave
pre-existing shared ancestors (e.g. `~/.cache`) untouched.

## Secret files 0600

`shutil.copy2`/`cp` PRESERVE the source mode, so `cp .env
~/.config/app/.env` from a 664 sample makes a world-readable master
password. Use `os.open(..., 0o600)` in Python and `install -m 600` in
Bash.

## Precedence

Shell env > `$XDG_CONFIG_HOME/app/.env` > project-local `.env`.
dotenv's `override=False` achieves this by loading LEAST important
first. `override=True` on the XDG file is wrong — it clobbers explicit
env vars.

## Vendor subdir

`$XDG_DATA_HOME/app` is mandatory, but reading ANOTHER app's files
needs the RAW base (Brave lives at `$XDG_CONFIG_HOME/BraveSoftware`,
not `.../yourapp`). Export both. Linux browser data may be native,
flatpak (`~/.var/app/...`), or snap — probe all, first hit wins.

## `$XDG_RUNTIME_DIR`

0700, tmpfs — for sockets/pipes; not for logs or large files.

## Completion

- Every resolved path passes all seven rules.
- The spec URL is cited in the report for each rule applied.
