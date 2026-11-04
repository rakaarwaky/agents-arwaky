"""Bootstrap sys.path for the standalone skills-traces CLI app.

The ``skills_traces`` package lives under this dir; the repo root stays
on the path so the orchestrator-owned composition root
(``modules.root_cli_entry``) and the shared modules remain importable.
Each tree bootstraps only its own namespace root — no shared skill
package dir exists any more (AES702 independent packages).
"""
import sys
from pathlib import Path

_MOD_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _MOD_ROOT.parents[3]
_NS_ROOTS = [
    _MOD_ROOT,    # modules/       -> shared, cli, skills_traces namespace packages
    _REPO_ROOT,   # repo root      -> top-level packages
]
for _ns in _NS_ROOTS:
    _ns_str = str(_ns)
    if _ns.is_dir() and _ns_str not in sys.path:
        sys.path.insert(0, _ns_str)
