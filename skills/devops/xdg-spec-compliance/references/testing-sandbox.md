# Test it without touching the user's home

XDG constants are computed at import time, so the sandbox MUST be
applied before importing the package.

**Goal:** a test module that proves path resolution, permissions, and
fallbacks without ever writing under the real `$HOME`.

## Setup

Set the four `XDG_*` vars to a `mkdtemp` path at the top of the test
module, above the app imports (`# noqa: E402`).

## Assert

- Every resolved path `startswith(sandbox)`.
- Dirs `== 0o700`, `.env` `== 0o600`.
- Relative/tilde values warn + fall back.

Add a hard guard that fails if `$HOME/.local/share/<app>` is
*newly* created by the run (snapshot pre-existing dirs first — a user
with a real install must not get a false failure). That guard catches
its own regressions: it fired twice during authoring for import-time
writes.

## File logging

File logging that mkdirs at import defeats sandboxing: make the log
handler lazy (open at first emit) with a `NO_FILE_LOG` env kill-switch.

## Fake-green guards

`python -m unittest discover` needs `tests/__init__.py`, else it
reports `Ran 0 tests` with exit 0. `pytest` on a repo with no pytest
installed reports the same fake green — check `Ran N tests`.

## Completion

- The sandbox test suite passes with the real `$HOME` untouched.
- The hard guard fired at least once during authoring and the
  import-time write it caught is fixed.
