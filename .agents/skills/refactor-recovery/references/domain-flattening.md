# Domain-package flattening (N domain folders -> one flat package root)

Companion direction to `flat-to-domain-migration.md` (split). This is collapse:
all `shared/<domain>/` subpackages become bare modules in `shared/`, and domain-specific
contracts/taxonomies may relocate into their owning feature modules.

## 1. Enumerate before touching anything

Run a three-way check first — a flatten commit frequently deletes files it did not
relocate, and consumers keep importing the old paths:

```bash
# what exists on disk now
find shared/ -name '*.py' | grep -v __pycache__ | sort
# which old 3-level paths are still referenced anywhere
grep -rn 'modules\.shared\.src\.<domain>\.' modules/ --include='*.py'
# what the rename commit actually did (R/A/D entries)
git show <flatten-commit> --name-status | grep 'shared'
```

The `--name-status` output of the flatten commit is the authoritative map:
`R100 old -> new` tells you where each file went; `D old` means it was deleted and must
be recovered or re-created. Do not guess new import paths — derive them from this map.

## 2. Recover deleted files from history

Untracked files (created during the refactor session, never committed) vanish with
`rm -rf <domain>/`. Recover from the last commit that had them:

```bash
git show <commit>:<old-path> > <new-flat-path>
```

Then rewrite the recovered file's own imports to the flat layout.
A quick probe: `git log --all --oneline -- <path>` to find the newest commit containing it.

## 3. Rewrite imports (Python, one pass, per mapping)

Map old -> new for every `<domain>.<module>` pair, then sweep:

```python
import pathlib, re, collections
FLAT = ["git","envfile","launcher","logging","manifest","paths","retry",
        "skill_names","tool","venv","version","xdg","common"]
stats = collections.Counter()
for f in pathlib.Path("modules").rglob("*.py"):
    if "__pycache__" in f.parts: continue
    s = f.read_text(); o = s
    for dom in FLAT:
        s = re.sub(r"modules\.shared\.src\." + dom + r"\.([a-z_][\w]*)",
                   r"modules.shared.src.\1", s)
    if s != o:
        f.write_text(s); stats[f] += 1
```

Print per-rewrite counters. A mapping that rewrites 0 hits means either the mapping is
already applied or the path pattern doesn't match — check which.

## 4. Package-level imports need a symbol split

`from <domain-pkg> import X, Y` breaks when the package is deleted, because the
re-export `__init__.py` is gone. Replace each with imports from the actual files:

```python
# old: from modules.shared.src.manifest import Tool, find_tool, load_tools
# new:
from modules.shared.src.taxonomy_common_vo import Tool
from modules.shared.src.utility_manifest_reader import find_tool, load_tools
```

Build the symbol->file map from the deleted package's last-known `__init__.py`
(`git show <commit>:<old-path>/__init__.py`), not from memory.

## 5. Feature-domain contracts may move into their feature module

A "decentralize contracts" commit often moves `shared/<feature-domain>/contract_*.py`
into `modules/<feature>/src/contract_*.py`. The flatten commit's `R` entries show this.
After flattening, consumers still importing `shared.<feature-domain>.<contract>` break —
repoint to `modules/<feature>/src/<contract>`.

## 6. Verify

- `python -m compileall modules/ -q` — zero syntax errors.
- Import smoke-test every feature package: `importlib.import_module(f"modules.{feat}.src")`.
- Run the project's quality gate (`aa check`).
- Grep for stale docstring/comment path mentions (`modules/shared/src/<domain>`)
  in `AGENTS.md`, `CONTRIBUTING.md`, and `.py` docstrings — fix those too.

## Pitfalls

- **A user-supplied flatten scope is a minimum, not the whole change.** The user said
  "flatten 13 domains" — but the actual commit also collapsed 9 feature-domain folders.
  Always check the commit's `--name-status`, not just the user's message.
- **`__init__.py` files that only re-export will break with a `ModuleNotFoundError`
  that names the missing sub-module, not the `__init__` itself.** When a package is
  flattened, every `__init__.py` that imports from its own sub-modules needs updating
  to import from the now-flat sibling files.
- **Re-export stubs prevent a second import-sweep pass.** If many consumers import a
  symbol from a file that moved, add a thin re-export at the old path:
  `from <new-path> import symbol; __all__ = ["symbol"]`. Delete the stub once consumers migrate.
