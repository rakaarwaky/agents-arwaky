"""Bootstrap sys.path for the standalone skills CLI apps (AES702 split modules).

Mirror of the sibling conftest under the other skill-authoring module dir
(skills/skill-authoring/skill-{design,traces}/modules/conftest.py) — keep the
two byte-identical so neither tree's tests diverge.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SKILL_NAMESPACE_ROOTS = [
    _REPO_ROOT / "skills" / "skill-authoring" / "skill-design" / "modules",
    _REPO_ROOT / "skills" / "skill-authoring" / "skill-traces" / "modules",
]
for _ns in (*_SKILL_NAMESPACE_ROOTS, _REPO_ROOT):
    _ns_str = str(_ns)
    if _ns.is_dir() and _ns_str not in sys.path:
        sys.path.insert(0, _ns_str)
