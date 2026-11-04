# Creating a profile (browser closed)

**Goal:** you can add a new profile dir + registry entries deterministically,
with all the correctness traps handled.

1. Back up `Local State` (`Local State.bwc-backup-<timestamp>`) before the
   first rewrite of a run; keep repeat-runs idempotent (second call = "exists",
   no second write).
2. Create the dir 0700 and seed `Preferences` 0600 with
   `profile.{name, avatar_index (match existing profiles, e.g. 26),
   creation_time (Chrome epoch: (unix_ts + 11644473600) * 1e6 microseconds),
   exit_type "Normal", managed false}`.
3. Add `info_cache[<dir>]` (name, `active_time` unix float,
   `metrics_bucket_index` = current `metrics.next_bucket_index`), append the
   dir to `profiles_order`, increment `next_bucket_index` and
   `profiles_created`.
4. Serialize `Local State` as compact JSON (`separators=(',',':')`) at 0600.

## Correctness traps

- Match existing profiles CASE-INSENSITIVELY (`profile 1` vs registered
  `Profile 1`) — Chromium does, and creating a sibling causes picker chaos.
- Resolve names against BOTH the `info_cache` folder key and its `name`
  attribute (the display name Brave's menu shows, e.g. key `Default` /
  display `arwaky90`). A user-written name equal to a display name must map
  to the existing folder; folder-only matching clones an empty twin under a
  name the user believes is taken.
- Validate the name before any filesystem/CLI use: reject `/`, `\`, `..`,
  and leading `-` (the dir name gets re-injected as a browser flag).
- Count a dir as a profile only when it holds a `Preferences` file — the
  user-data dir is littered with non-profile dirs (Crashpad, extension IDs).

## Testing without touching the live browser

- Point the user-data-dir override at an `mkdtemp` fake tree; synthesize
  "running" by binding and `listen()`ing a unix socket at the
  `SingletonSocket` path (that is what the guard probes), and "closed" by
  closing it. A stale `SingletonLock` pointing at an unrelated pid (even
  `hostname-2`) must read as closed.
- Assert permissions (0700 dir / 0600 prefs + Local State), backup contents
  (must be the PRE-edit state), dry-run writes zero bytes, and bootstrap from
  a never-existed dir.
- Type-check the new module at the repo's strictness (`mypy --strict`), and
  separate your errors from legacy debt with a baseline: `git stash -u`,
  re-run, `git stash pop`, compare counts.
- When the package computes paths at import time, ALL test modules must share
  one sandbox established in `tests/conftest.py` (imported before any test
  module). A per-module env-setup block loses to collection order: the first
  importing module wins and the others' isolation assertions fail against the
  live `$HOME` paths.

## Completion

- `Local State` contains the new `info_cache` entry, updated `profiles_order`
  and incremented `metrics.next_bucket_index`; the file is 0600 and compact
  JSON.
- The new dir is 0700 with a seeded `Preferences` 0600.
- A repeat run is a no-op ("exists", zero writes).
