# Bash installer

The rules for a shell installer that provisions XDG dirs for the app.

**Goal:** an installer that cannot ship the dev machine's state and
cannot create a dir the user should not see.

## Rules

- Validate absoluteness per var with a helper (same reject-relative
  rule as `rules.md`).
- chmod 700 the tree it creates.
- Install with `pip install .` into a private venv rather than
  `cp -rn` from a dev venv's site-packages — the copy silently ships
  whatever the dev machine happened to have and drops undeclared
  deps.
- `[project.scripts]` makes the entry points; do not hand-roll them in
  the installer too.

## Completion

- A clean venv install of the package succeeds from the installer
  alone (no dev-machine state required).
- Every dir the installer creates is 0700.
