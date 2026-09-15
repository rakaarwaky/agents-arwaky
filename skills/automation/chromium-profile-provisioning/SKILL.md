---
name: chromium-profile-provisioning
description: Create or inspect Brave/Chromium profile dirs and prefs. Not driving pages.
metadata:
  tags: [browser, chromium, brave, automation, python]
---
# Provisioning Chromium/Brave browser profiles

## What "a profile exists" actually means

A profile is real only when BOTH agree:
  * a directory (e.g. `Profile 9`) under the user-data dir,
  * its registration in `Local State` → `profile.info_cache` (plus
    `profiles_order` for the picker and `metrics.next_bucket_index` so the
    per-profile metrics bucket stays unique).

Launching with `--profile-directory=<new>` auto-creates the directory, but the
`info_cache` entry lands only later, so discovery that reads `Local State`
stays blind to it. If the tool must see/create profiles deterministically, it
has to write the registry itself.

Before assuming an env var or flag creates browser profiles, grep its READERS:
`BWC_PROFILE_*`-style names are often just credential labels for another system
(e.g. vault items) and the browser-profile list flows the other way, read-only
from `Local State`.

## User-data dir locations (probe in order, first `Local State` hit wins)

  * Linux native: `$XDG_CONFIG_HOME/BraveSoftware/Brave-Browser`
  * Flatpak: `~/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser`
  * Snap: `~/.snap/brave/.config/BraveSoftware/Brave-Browser`
  * macOS: `~/Library/Application Support/BraveSoftware/Brave-Browser`
  * Windows: `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data` (note the
    extra `User Data` level)

Always export an env override for the user-data dir (`<APP>_BRAVE_USER_DATA_DIR`
style, absolute-path required). It is what makes the destructive path testable
against a fake tree and lets multi-install machines pin one browser.

## Hard gate: edit only a provably-closed browser

A running Chromium rewrites `Local State` (and Preferences) when it exits —
registry edits made underneath it are silently lost, and you may read it
mid-write. Detect via the `SingletonSocket` AF_UNIX listener at the user-data dir root
(Chromium unlinks it on clean shutdown): connect succeeds -> running ->
refuse; `ECONNREFUSED` or absent -> closed, safe. Do NOT decide liveness from
the `SingletonLock` symlink's pid (`<hostname>-<pid>`) via `os.kill`: under
flatpak the recorded pid is sandbox-internal (often 1-3) and `os.kill` on it
raises EPERM, which reads as "alive" forever and wedges the guard on a dead
browser. A pid <= 3 is never the browser. Foreign hostname, unreadable socket,
or Windows (`Lockfile` is an exclusive handle, not a symlink) -> UNKNOWN ->
refuse too, unless the caller passes an explicit `--yes`/`assume_not_running`
escape hatch.
Verify the refusal itself against the real running browser (exit != 0, then
assert nothing new appeared in the tree) instead of testing only the happy path.

## Creating a profile (browser closed)

1. Back up `Local State` (`Local State.bwc-backup-<timestamp>`) before the
   first rewrite of a run; keep repeat-runs idempotent (second call = "exists",
   no second write).
2. Create the dir 0700 and seed `Preferences` 0600 with
   `profile.{name, avatar_index (match existing profiles, e.g. 26),
   creation_time (Chrome epoch: (unix_ts + 11644473600) * 1e6 microseconds),
   exit_type "Normal", managed false}`.
3. Add `info_cache[<dir>]` (name, `active_time` unix float,
   `metrics_bucket_index` = current `metrics.next_bucket_index`), append the
   dir to `profiles_order`, increment `next_bucket_index` and `profiles_created`.
4. Serialize `Local State` as compact JSON (`separators=(',',':')`) at 0600.

Correctness traps:
  * Match existing profiles CASE-INSENSITIVELY (`profile 1` vs registered
    `Profile 1`) — Chromium does, and creating a sibling causes picker chaos.
  * Resolve names against BOTH the `info_cache` folder key and its `name`
    attribute (the display name Brave's menu shows, e.g. key `Default` /
    display `arwaky90`). A user-written name equal to a display name must map
    to the existing folder; folder-only matching clones an empty twin under a
    name the user believes is taken.
  * Validate the name before any filesystem/CLI use: reject `/`, `\`, `..`,
    and leading `-` (the dir name gets re-injected as a browser flag).
  * Count a dir as a profile only when it holds a `Preferences` file — the
    user-data dir is littered with non-profile dirs (Crashpad, extension IDs).

## Single source of truth for the env format

When one `NAME|user|pass|url` env var feeds two subsystems (vault items AND
browser profiles), parse it in exactly one module and alias the old helper to
it — two hand-rolled parsers drift the moment the format changes.

The trailing `url` field is vault-side only: it becomes the item's
`login.uris[].uri` autofill match (Google accounts: `https://accounts.google.com`
— Bitwarden's default base-domain match then covers mail/drive subdomains).
Profile creation ignores it.

Never load such a file with `set -a; source .env` — the `|` separators are shell
pipes and the lines explode. Parse it with python-dotenv (`dotenv_values` /
`load_dotenv`) instead.

## Testing without touching the live browser

  * Point the user-data-dir override at an `mkdtemp` fake tree; synthesize
    "running" by binding and `listen()`ing a unix socket at the
    `SingletonSocket` path (that is what the guard probes), and "closed" by
    closing it. A stale `SingletonLock` pointing at an unrelated pid (even
    `hostname-2`) must read as closed.
  * Assert permissions (0700 dir / 0600 prefs + Local State), backup contents
    (must be the PRE-edit state), dry-run writes zero bytes, and bootstrap from
    a never-existed dir.
  * Type-check the new module at the repo's strictness (`mypy --strict`), and
    separate your errors from legacy debt with a baseline: `git stash -u`,
    re-run, `git stash pop`, compare counts.
  * When the package computes paths at import time, ALL test modules must share
    one sandbox established in `tests/conftest.py` (imported before any test
    module). A per-module env-setup block loses to collection order: the first
    importing module wins and the others' isolation assertions fail against the
    live `$HOME` paths.

## Bitwarden CLI (`bw`) companion setup

The vault half of the flow needs `bw`, which the browser automation does not
bundle:

  * Install PINNED: `npm install -g @bitwarden/cli@<latest-release>` — version
    2026.4.0 is flagged malicious by npm threat intelligence, so an unpinned
    resolve can land on it; check `npm view @bitwarden/cli versions` and pick
    the newest non-flagged release.
  * If `npm prefix -g` is a node outside PATH (e.g. editor-bundled node), the
    binary installs invisible to `command -v bw`. Symlink it:
    `ln -sf "$(npm prefix -g)/bin/bw" ~/.local/bin/bw`.
  * Non-interactive login without exposing the password in argv:
    `bw login <email> --passwordenv BWC_PASSWORD` (export the var first).
