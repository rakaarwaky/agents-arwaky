# Registry semantics and user-data dir locations

**Goal:** you can state what makes a profile real, probe the user-data dir on any
install kind, and know the liveness gate that protects registry edits.

## What "a profile exists" actually means

A profile is real only when BOTH agree:

- a directory (e.g. `Profile 9`) under the user-data dir,
- its registration in `Local State` → `profile.info_cache` (plus
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

- Linux native: `$XDG_CONFIG_HOME/BraveSoftware/Brave-Browser`
- Flatpak: `~/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser`
- Snap: `~/.snap/brave/.config/BraveSoftware/Brave-Browser`
- macOS: `~/Library/Application Support/BraveSoftware/Brave-Browser`
- Windows: `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data` (note the
  extra `User Data` level)

Always export an env override for the user-data dir (`<APP>_BRAVE_USER_DATA_DIR`
style, absolute-path required). It is what makes the destructive path testable
against a fake tree and lets multi-install machines pin one browser.

## Hard gate: edit only a provably-closed browser

A running Chromium rewrites `Local State` (and Preferences) when it exits —
registry edits made underneath it are silently lost, and you may read it
mid-write. Detect via the `SingletonSocket` AF_UNIX listener at the user-data
dir root (Chromium unlinks it on clean shutdown): connect succeeds → running →
refuse; `ECONNREFUSED` or absent → closed, safe. Do NOT decide liveness from
the `SingletonLock` symlink's pid (`<hostname>-<pid>`) via `os.kill`: under
flatpak the recorded pid is sandbox-internal (often 1-3) and `os.kill` on it
raises EPERM, which reads as "alive" forever and wedges the guard on a dead
browser. A pid ≤ 3 is never the browser. Foreign hostname, unreadable socket,
or Windows (`Lockfile` is an exclusive handle, not a symlink) → UNKNOWN →
refuse too, unless the caller passes an explicit `--yes`/`assume_not_running`
escape hatch. Verify the refusal itself against the real running browser
(exit != 0, then assert nothing new appeared in the tree) instead of testing
only the happy path.

## Completion

- The user-data dir is resolved via the probe order above and the env override
  is exported.
- The `SingletonSocket` probe has run and the browser is provably closed before
  any registry write.
