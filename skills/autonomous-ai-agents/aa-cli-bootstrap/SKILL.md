---
name: aa-cli-bootstrap
description: "Fix aa CLI bootstrap: path resolution and namespace init."
version: 1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
      - cli-bootstrap
      - aa-command
      - python-namespace
      - install-script
    related_skills:
      - orca
      - grok-build
      - skill-design
---

# aa-cli-bootstrap

Fix and verify the `aa` CLI bootstrap: resolve the repo modules tree from the installed binary, ensure Python package namespace resolution finds skill-design's self-contained `shared` package, and remove duplicated skills CLI code/tests left under `modules/` after the skills CLI moved to `skills/skill-authoring/skill-design/`.

## When to use

- Bare `aa status` / `aa skills list` / `aa tool list` fail with `ModuleNotFoundError: No module named 'modules'` without `AA_MODULES_DIR`.
- `aa skills list` fails because `shared` resolves to `modules/shared` (lacks `utility_skill_pack`) instead of skill-design's `skills/skill-authoring/skill-design/modules/shared/`.
- Skills CLI source or tests exist both under `modules/cli/` and `skills/skill-authoring/skill-design/modules/cli/` — remove the `modules/` copies, keep general command surfaces.

## Procedure

### 1. Fix modules path resolution (bare `aa` without AA_MODULES_DIR)

The installed binary at `~/.local/bin/aa` runs `_resolve_modules_dir()`, which walks up from `Path(__file__).resolve()` = `~/.local/bin`, outside the repo, never finding `modules/`.

Open `scripts/install.sh` and add a cwd walk-up fallback BEFORE the final fallback:

```python
# Fallback 1: walk up from this binary to find the repo modules tree.
here = Path(__file__).resolve()
for candidate in (here.parent, *here.parents):
    mod = candidate / _DEFAULT_MODULES
    if mod.is_dir():
        return mod
# Fallback 2: walk up from the current working directory (the repo root
# where the user runs aa) before giving up.
cwd = Path.cwd().resolve()
for candidate in (cwd, *cwd.parents):
    mod = candidate / _DEFAULT_MODULES
    if mod.is_dir():
        return mod
return here.parent / _DEFAULT_MODULES
```

Pitfall: Do not replace the binary walk — keep it as Fallback 1 for installs outside a repo. Add cwd walk as Fallback 2 so `aa` run from inside the repo resolves `modules/` even when `AA_MODULES_DIR` is unset.

Regenerate the binary: `bash scripts/install.sh` (reinstalls `~/.local/bin/aa`).

Verify bare from repo root:
- `unset AA_MODULES_DIR && aa status` → rc=0
- `unset AA_MODULES_DIR && aa skills list` → rc=0
- `unset AA_MODULES_DIR && aa tool list` → rc=0

### 2. Fix Python package namespace (__init__.py placement)

Python namespace resolution: a directory WITH `__init__.py` is a regular package and STOPS the search; a directory WITHOUT `__init__.py` is a namespace portion and the search continues. `shared` resolved to `_MODULES/shared` (repo modules, wrong, lacks `utility_skill_pack`) because skill-design's `shared/` had no `__init__.py`, so Python kept searching until it hit `_MODULES/shared/` which had one and stopped.

`root_cli_entry.py` inserts skill-design's modules before `_MODULES` on `sys.path` (skill-traces/modules, skill-design/modules, then `_MODULES`). So adding `__init__.py` to skill-design's copy makes Python stop there.

Add empty `__init__.py` files to all four package dirs under skill-design's modules tree:

```
skills/skill-authoring/skill-design/modules/shared/__init__.py
skills/skill-authoring/skill-design/modules/shared/src/__init__.py
skills/skill-authoring/skill-design/modules/cli/__init__.py
skills/skill-authoring/skill-design/modules/cli/src/__init__.py
```

Each file: a one-line docstring, e.g. `"""Skill-design shared kernel (AES utility layer) — colocated standalone copy."""`.

Verify: `unset AA_MODULES_DIR && aa skills list` → rc=0.

Pitfall: `__init__.py` on `modules/shared/` (repo modules) already exists and stops the search there if reached first — that's why skill-design's copy (earlier on sys.path) must have `__init__.py` so Python stops at the right one before reaching `_MODULES/shared/`.

### 3. Remove duplicated skills CLI from modules/ after relocation

The skills CLI source (`surface_skills_command.py`) already lives only under `skills/skill-authoring/skill-design/modules/cli/src/`. The `modules/cli/` tree holds general command surfaces (backup, config, daemon, doctor, harness, mcp, service, tools) that `aa` depends on — do NOT remove those.

Remove only skills-specific remnants under `modules/`:
- `modules/cli/tests/integration_skills_cli.py`
- `modules/cli/tests/unit_skills_surface.py`
- Their `__pycache__` artifacts (`rm -rv modules/cli/__pycache__ modules/cli/src/__pycache__ modules/cli/tests/__pycache__`)

Do NOT remove `modules/cli/src/surface_*.py` general command files or `modules/cli/tests/integration_cli.py` (covers config/daemon/tool surfaces `aa` needs).

Verify after removal:
- `python3 -m pytest modules/cli/tests/ -q` → all pass
- `unset AA_MODULES_DIR && aa skills list` → rc=0

### 4. Commit and push

Stage only intended files (check `git diff --cached --name-only` after each `git add` — never `git add -A` or bare `git commit -a` in this repo; parallel agents may pre-stage unrelated files). Commit, push to `rakaarwaky/move-skills-modules`, and open/update PR to `main`.

Pitfall: `git commit` (no -a) commits the ENTIRE index — unstage non-task files with `git reset HEAD -- <path>` before committing.

## Sources

- `scripts/install.sh` — `_resolve_modules_dir()` implementation and binary-walk fallback
- `modules/root_cli_entry.py` — `cmd_skills` dispatch, sys.path bootstrap inserting skills namespace roots
- `skills/skill-authoring/skill-design/modules/skills_design/src/root_skills_container.py` — imports `from shared.src.common.utility_skill_pack` (AES702 self-contained copy)
- `skills/skill-authoring/skill-design/modules/cli/src/surface_skills_command.py` — skills CLI surface source (colocated, not under modules/)
- `modules/cli/tests/integration_skills_cli.py` — removed skills-specific integration test (was duplicated under modules/)