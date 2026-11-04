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
# Add this tree's modules/ dir so root_cli_entry / shared / cli from this
# tree shadow the root modules/ packages when both paths are on sys.path.
for _ns in (_MOD_ROOT, _REPO_ROOT):
    _ns_str = str(_ns)
    if _ns.is_dir() and _ns_str not in sys.path:
        sys.path.insert(0, _ns_str)

# Extend the root ``shared`` package __path__ with BOTH skill trees' shared/src
# so ``shared.src.skills_traces`` and ``shared.src.skills_design`` resolve
# even when root modules/shared was imported first.
try:
    import shared as _shared_pkg
    _design_shared = _REPO_ROOT / "skills" / "skill-authoring" / "skill-design" / "modules" / "shared" / "src"
    _traces_shared = _MOD_ROOT / "shared" / "src"
    for _ext in (_design_shared, _traces_shared):
        if _ext.is_dir() and str(_ext) not in _shared_pkg.__path__:
            _shared_pkg.__path__.append(str(_ext))
except ImportError:
    pass
