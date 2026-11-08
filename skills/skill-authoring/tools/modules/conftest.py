"""Bootstrap sys.path for the standalone skills-design CLI app.

The ``skills_design`` package lives under this dir; the repo root stays
on the path so the orchestrator-owned composition root
(``modules.root_cli_entry``) and the shared modules remain importable.
Each tree bootstraps only its own namespace root — no shared skill
package dir exists any more (AES702 independent packages).
"""
import sys
from pathlib import Path

_MOD_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _MOD_ROOT.parents[4]
# Add this tree's modules/ dir so root_cli_entry / shared / cli from this
# tree shadow the root modules/ packages when both paths are on sys.path.
for _ns in (_MOD_ROOT, _REPO_ROOT):
    _ns_str = str(_ns)
    if _ns.is_dir() and _ns_str not in sys.path:
        sys.path.insert(0, _ns_str)

# Extend shared.src.__path__ with ALL shared/src trees so
# shared.src.skills_design and shared.src.skills_traces resolve regardless
# of which conftest loads first or which ``shared`` package wins import.
try:
    import shared.src as _shared_src_pkg
    _src_dirs = [
        _REPO_ROOT / "modules" / "shared" / "src",
        _REPO_ROOT / "skills" / "skill-authoring" / "skill-design" / "tools" / "modules" / "shared" / "src",
        _REPO_ROOT / "skills" / "skill-authoring" / "skill-design" / "modules" / "shared" / "src",
    ]
    for _ext in _src_dirs:
        if _ext.is_dir() and str(_ext) not in _shared_src_pkg.__path__:
            _shared_src_pkg.__path__.append(str(_ext))
except ImportError:
    pass

# Extend cli.src.__path__ with ALL cli/src trees so both
# cli.src.surface_skills_command and cli.src.surface_skills_traces_command
# resolve regardless of which tree's ``cli`` package wins import.
try:
    import cli.src as _cli_src_pkg
    _cli_src_dirs = [
        _REPO_ROOT / "modules" / "cli" / "src",
        _REPO_ROOT / "skills" / "skill-authoring" / "skill-design" / "tools" / "modules" / "cli" / "src",
        _REPO_ROOT / "skills" / "skill-authoring" / "skill-design" / "modules" / "cli" / "src",
    ]
    for _ext in _cli_src_dirs:
        if _ext.is_dir() and str(_ext) not in _cli_src_pkg.__path__:
            _cli_src_pkg.__path__.append(str(_ext))
except ImportError:
    pass
