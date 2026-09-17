"""Skill pack provisioning capability — delegates to the shared skill_pack domain."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill.contract_skill_protocol import ISkillProvisioner
from modules.shared.src.skill.taxonomy_skill_vo import SkillProvisionResult
from modules.shared.src.skill_pack.capabilities_skill_pack import (
    PackFinding,
    audit_pack,
    get_all_skill_files,
    prune_provisioned,
    write_provenance,
)
from modules.shared.src.skill_names.utility_skill_names import (
    ensure_under,
    safe_child,
    safe_skill_name,
)


class SkillPackProvisioner(ISkillProvisioner):
    """Thin delegate over the shared skill_pack domain for a single tool.

    # Block 1: Constructor
    # Block 2: Install / prune
    # Block 3: Audit
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self) -> None:
        self._pack_root = repo_root() / "skills"

    # -- Block 2: Install / prune ----------------------------------------------------
    def install(self, tool_id: str, target_dir: Path, custom_dest: str = "", force: bool = False, link: bool = False, prune: bool = False) -> SkillProvisionResult:
        """Provision every pack skill into the target workspace."""
        if prune:
            base = Path(custom_dest) if custom_dest and not custom_dest.endswith(".md") else target_dir / ".agents" / "skills"
            prune_provisioned(base, self._pack_root)
        total = 0
        for skill_md in get_all_skill_files():
            name = safe_skill_name(skill_md)
            if not name:
                continue
            if custom_dest:
                base = Path(custom_dest)
            else:
                base = target_dir / ".agents" / "skills"
            dest_dir = base / name
            src_dir = skill_md.parent
            if link and dest_dir.is_symlink():
                if dest_dir.resolve() == src_dir.resolve():
                    continue
                dest_dir.unlink()
            if link and dest_dir.resolve() == src_dir.resolve():
                continue
            if link:
                base.mkdir(parents=True, exist_ok=True)
                if not dest_dir.exists():
                    dest_dir.symlink_to(src_dir, target_is_directory=True)
                total += 1
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_dir.joinpath("SKILL.md").write_text(
                skill_md.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )
            write_provenance(dest_dir, skill_md, self._pack_root)
            total += 1
        return SkillProvisionResult(True, tool_id, total, f"{total} skill(s) provisioned")

    def prune(self, target_dir: Path, custom_dest: str = "") -> SkillProvisionResult:
        base = Path(custom_dest) if custom_dest and not custom_dest.endswith(".md") else target_dir / ".agents" / "skills"
        removed = prune_provisioned(base, self._pack_root)
        return SkillProvisionResult(True, "pack", len(removed), f"removed {len(removed)} stale provisioned skill(s)")

    # -- Block 3: Audit --------------------------------------------------------------
    def audit(self) -> list[PackFinding]:
        """Pack loadability findings; empty means clean."""
        return audit_pack(self._pack_root)
