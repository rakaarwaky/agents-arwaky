---
name: xdg-spec-compliance
description: Audit and fix XDG Base Directory compliance in a repo.
metadata:
  tags:
    - linux
    - xdg
    - packaging
    - security
    - python
    - bash
---

# XDG Base Directory Compliance

Authoritative text: https://specifications.freedesktop.org/basedir/latest/ (v0.8).
Quote it rather than reasoning from memory — three rules are routinely guessed wrong.

## Audit order (cheapest signal first)

1. `grep -rn -E 'XDG_|expanduser|Path\.home|/home/|\.local/share|\.config/' --include='*.py' --include='*.sh' .`
   — find every resolved path and every bypass of the base dirs.
2. Check the LOG/state location specifically. Logs belong in `$XDG_STATE_HOME`
   (`.local/state`), not DATA or CACHE. Projects that get this right are usually
   already competent; the remaining bugs are permission/precedence ones.
3. Check who WRITES and who READS each constant: `for n in DEFAULT_OUTPUT DEFAULT_CACHE; do grep -rln $n pkg; done`.
   Provisioned-but-never-written directories mean the permission question is moot — say so instead of theorizing.
4. Reproduce before claiming. Relative/tilde env values and mkdir umask inheritance
   are invisible to reading alone:
   `XDG_DATA_HOME=rel/dir XDG_CONFIG_HOME='~/' python -c 'from pkg.provisioner import ...'`
   then `git status --porcelain` to see what got dumped in the repo.
   Clean up any junk the probe created and re-check `git status` is clean.

## The rules projects break

- **Absolute only.** Spec: a relative value is *invalid and must be ignored* (fall
  back to the default). Use `Path(raw).is_absolute()` — do NOT `expanduser()` first:
  a literal `~/` that survives into the env was never shell-expanded, and
  `Path('~/x').expanduser()` is absolute, so expanding it silently writes
  `$HOME/x/bwc`. Reject it and warn.
- **Empty/unset both mean "use default"** — `(env.get(v) or "").strip()`.
- **Auto-created dirs are 0700.** `mkdir(parents=True)` inherits umask (0775 on
  desktops), so `~/.local/state/app` and its `app.log` end up group/world
  readable. chmod the leaf AND every ancestor this call newly creates; leave
  pre-existing shared ancestors (e.g. `~/.cache`) untouched.
- **Secret files 0600.** `shutil.copy2`/`cp` PRESERVE the source mode, so
  `cp .env ~/.config/app/.env` from a 664 sample makes a world-readable master
  password. Use `os.open(..., 0o600)` in Python and `install -m 600` in Bash.
- **Precedence.** Shell env > `$XDG_CONFIG_HOME/app/.env` > project-local `.env`.
  dotenv's `override=False` achieves this by loading LEAST important first.
  `override=True` on the XDG file is wrong — it clobbers explicit env vars.
- **Vendor subdir** (`$XDG_DATA_HOME/app`) is mandatory, but reading ANOTHER
  app's files needs the RAW base (Brave lives at `$XDG_CONFIG_HOME/BraveSoftware`,
  not `.../yourapp`). Export both. Linux browser data may be native,
  flatpak (`~/.var/app/...`), or snap — probe all, first hit wins.
- **`$XDG_RUNTIME_DIR`** (0700, tmpfs) for sockets/pipes; not for logs or large files.

## Bash installer

Validate absoluteness per var with a helper (same reject-relative rule), chmod 700
the tree it creates, and install with `pip install .` into a private venv rather
than `cp -rn` from a dev venv's site-packages — the copy silently ships whatever
the dev machine happened to have and drops undeclared deps. `[project.scripts]`
makes the entry points; do not hand-roll them in the installer too.

## Test it without touching the user's home

XDG constants are computed at import time, so the sandbox MUST be applied before
importing the package: set the four `XDG_*` vars to a `mkdtemp` path at the top
of the test module, above the app imports (`# noqa: E402`).

Assert: every resolved path `startswith(sandbox)`, dirs `== 0o700`, `.env`
`== 0o600`, relative/tilde values warn + fall back. Add a hard guard that fails
if `$HOME/.local/share/<app>` is *newly* created by the run (snapshot pre-existing
dirs first — a user with a real install must not get a false failure). That guard
catches its own regressions: it fired twice during authoring for import-time writes.

File logging that mkdirs at import defeats sandboxing: make the log handler lazy
(open at first emit) with a `NO_FILE_LOG` env kill-switch.

Verify discovery is not silently green: `python -m unittest discover` needs
`tests/__init__.py`, else it reports `Ran 0 tests` with exit 0. `pytest` on a
repo with no pytest installed reports the same fake green — check `Ran N tests`.

## Destructive provisioning

Workspace provisioners replacing a stale regular directory with a symlink should
rename it to `<name>.stale-<timestamp>` beside the link, not `rmtree` it. Keep
the rename idempotent: if a timestamped copy already exists, delete the stale
source instead of stacking backups.

Symlinking config/cache into the workspace (`.bwc/config -> $XDG_CONFIG_HOME/app`)
is convenient but means `tar -h` / `rsync -L` of the repo exfiltrates real
credentials — document it at the symlink-creating function.
