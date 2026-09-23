"""Harness skills provisioning capability — makes the pack discoverable (FR-003).

Default is a whole-root symlink into the repo skill pack so edits land in the
repository and every agent shares them; `copy=True` restores per-skill
snapshots. Providers that scan only one level below a skills root get their
`skills.directories` derived from disk plus a SessionStart sync hook.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from modules.harness.src.contract_harness_protocol import IHarnessProtocol
from modules.harness.src.taxonomy_harness_constant import ALL_HARNESS_IDS
from modules.harness.src.taxonomy_harness_vo import ExitCode, UnsupportedHarnessError
from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_vo import iter_skill_files
from modules.shared.src.taxonomy_skill_vo import safe_skill_name


def _log_sub(msg: str) -> None:
    print(f"  -> {msg}")


def _log_ok(msg: str) -> None:
    print(f"  \u2713 {msg}")


def _log_skip(msg: str) -> None:
    print(f"  \u21bb {msg}")


def _log_warn(msg: str) -> None:
    print(f"  \u26a0 {msg}")


def _log_err(msg: str) -> None:
    print(f"  \u2717 {msg}", file=sys.stderr)


def _log_header(msg: str) -> None:
    print(f"==> {msg}")


def discover_skill_roots() -> list[Path]:
    """Directories that directly hold skill folders inside the pack.

    A harness scanning exactly ONE level below each skills root cannot see
    ``skills/<category>/<skill>/SKILL.md`` until ``skills/<category>`` is
    itself a registered root, so it is derived from disk every time.
    """
    files = iter_skill_files(REPO_ROOT / "skills")
    return sorted({sf.parent.parent for sf in files})


@dataclass
class SkillsOpts:
    copy: bool = False
    dry_run: bool = False
    force: bool = False
    adapters: dict[str, object] = field(default_factory=dict, repr=False)

    def adapter(self, harness_id: str):
        try:
            return self.adapters[harness_id]
        except KeyError:
            raise UnsupportedHarnessError(harness_id, ALL_HARNESS_IDS) from None


class HarnessSkills(IHarnessProtocol):
    """Registry-keyed skills provisioning (composition root injects adapters).

    # Block 1: Constructor
    # Block 2: Protocol ABC Method Implementation
    # Block 3: Dunder Methods, Factories & Helpers
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, adapters: dict[str, object]) -> None:
        self._adapters = adapters

    # -- Block 2: Protocol ABC Method Implementation ----------------------------
    def execute(self, op: str, targets: tuple[str, ...],
                flags: dict[str, bool] | None = None) -> ExitCode:
        """Dispatch the ``provision_skills`` op over *targets*; return exit code."""
        if op != "provision_skills":
            raise ValueError(f"HarnessSkills does not handle op {op!r}")
        flags = flags or {}
        return ExitCode(self.provision_skills(
            targets,
            copy=flags.get("copy", False),
            dry_run=flags.get("dry_run", False),
            force=flags.get("force", False),
        ))

    # -- Block 3: Dunder Methods, Factories & Helpers ----------------------------
    def provision_skills(self, harness_ids: tuple[str, ...], copy: bool = False,
                         dry_run: bool = False, force: bool = False) -> int:
        """FR-003: link or copy the pack into each harness's skill dir.

        A failed link/copy is reported per skill; the overall exit code is
        non-zero when anything failed. Returns 0 when all succeeded.
        """
        opts = SkillsOpts(copy=copy, dry_run=dry_run, force=force, adapters=self._adapters)
        pack_root = REPO_ROOT / "skills"
        if not pack_root.is_dir():
            _log_warn(f"Skill pack not found at {pack_root}; skipping all harnesses.")
            return 0
        skill_files = iter_skill_files(pack_root)
        if not skill_files:
            _log_warn(f"Skill pack at {pack_root} is empty; skipping all harnesses.")
            return 0
        failures = 0
        for harness_id in harness_ids:
            adapter = opts.adapter(harness_id)
            failures += self._provision_one(harness_id, adapter, opts, skill_files, pack_root)
        return 1 if failures else 0

    # -- Block 3: Dunder Methods, Factories & Helpers ----------------------------
    def _provision_one(self, harness_id, adapter, opts: SkillsOpts, skill_files, pack_root) -> int:
        _log_header(f"Provisioning skills into {adapter.display}...")
        skills_dir = adapter.skills_dir()
        if not skills_dir.exists():
            _log_skip(f"{harness_id} has no skill dir; skipped.")
            return 0
        link = adapter.skill_link_verified and not opts.copy
        if link:
            failures = _link_skills_root(skills_dir, pack_root, opts.force, opts.dry_run)
            if failures:
                return failures
            _log_ok(f"Skills root linked: {skills_dir} -> {pack_root}")
            if getattr(adapter, "one_level_skill_scan", False):
                _sync_skill_directories(adapter, opts.dry_run)
                _sync_skill_hook(adapter, opts.dry_run)
        else:
            failures = 0
            for sf in skill_files:
                if not _provision_skill(sf, skills_dir, opts.force, opts.dry_run):
                    failures += 1
            if failures:
                _log_err(f"{harness_id}: {failures} skill(s) failed to provision.")
            else:
                _log_ok(f"{adapter.display} skills provisioned.")
        return failures


_ASSET_DIRS = ("scripts", "references", "resources", "examples", "templates", "assets")


def _provision_skill(src: Path, dest_base: Path, force: bool, dry_run: bool) -> bool:
    """Provision one skill (SKILL.md + companion assets) as a snapshot copy."""
    if not src.is_file():
        _log_err(f"Source file not found: {src}")
        return False
    name = safe_skill_name(src)
    if not name:
        return False
    src_dir = src.parent
    dest_dir = dest_base / name
    if dry_run:
        _log_sub(f"[DRY-RUN] Would copy skill '{name}' -> {dest_dir}")
        return True
    if dest_dir.is_dir() and not dest_dir.is_symlink():
        if _copy_matches_pack(dest_dir, src_dir) or force:
            shutil.rmtree(dest_dir)
        else:
            _log_skip(f"Skill '{name}' already exists (use --force to overwrite)")
            return True
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_dir / "SKILL.md")
    for extra in _ASSET_DIRS:
        e = src_dir / extra
        if e.is_dir():
            shutil.rmtree(dest_dir / extra, ignore_errors=True)
            shutil.copytree(e, dest_dir / extra)
    _log_ok(f"Skill '{name}' provisioned")
    return True


def _copy_matches_pack(dest_dir: Path, src_dir: Path) -> bool:
    for f in src_dir.rglob("*"):
        if f.is_dir() or "__pycache__" in f.parts:
            continue
        peer = dest_dir / f.relative_to(src_dir)
        if not peer.is_file() or peer.read_bytes() != f.read_bytes():
            return False
    return True


def _link_skills_root(dest_root: Path, src_root: Path, force: bool, dry_run: bool) -> int:
    """Replace a harness's whole skills dir with ONE symlink to the pack.

    Migration safety (``force``): leftover real children are MOVED into the
    pack, never deleted; an identical per-skill symlink is just unlinked.
    Without ``force`` a non-empty dir aborts loudly.
    """
    failures = 0
    if dest_root.is_symlink():
        if dest_root.resolve() == src_root.resolve():
            _log_skip(f"Skills root already linked: {dest_root} -> {src_root}")
            return 0
        if not force:
            _log_err(f"Skills root {dest_root} links to {dest_root.resolve()}, "
                     f"not the pack. Use --force to replace it.")
            return 1
        if dry_run:
            _log_sub(f"[DRY-RUN] Would relink skills root {dest_root} -> {src_root}")
            return 0
        dest_root.unlink()
    elif dest_root.is_dir():
        leftovers, stale_links = [], []
        for child in sorted(dest_root.iterdir()):
            if child.is_symlink():
                try:
                    if child.resolve().is_relative_to(src_root):
                        stale_links.append(child)
                        continue
                except OSError:
                    pass
            leftovers.append(child)
        if leftovers and not force:
            _log_warn(f"{dest_root} holds {len(leftovers)} item(s) not in the pack "
                      f"(harness-native skills / state). Nothing was touched. "
                      f"Re-run with --force to MOVE them into {src_root} first.")
            return 1
        if dry_run:
            _log_sub(f"[DRY-RUN] Would move {len(leftovers)} item(s) into {src_root}, "
                     f"unlink {len(stale_links)} old link(s), then link {dest_root} -> {src_root}")
            return 0
        src_root.mkdir(parents=True, exist_ok=True)
        for child in leftovers:
            target = src_root / child.name
            if target.exists():
                if child.name.startswith("."):
                    _merge_dir_into(child, target)
                    shutil.rmtree(child, ignore_errors=True)
                    continue
                if _copy_matches_pack(child, target):
                    shutil.rmtree(child)
                    continue
                stamp = 1
                while (src_root / f"{child.name}.harness-{stamp}").exists():
                    stamp += 1
                target = src_root / f"{child.name}.harness-{stamp}"
                _log_warn(f"{child.name} differs from the pack; "
                          f"stored as {target.name} for review")
            shutil.move(str(child), str(target))
        for link in stale_links:
            link.unlink()
        dest_root.rmdir()
    else:
        if dry_run:
            _log_sub(f"[DRY-RUN] Would link skills root {dest_root} -> {src_root}")
            return 0
        dest_root.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest_root.symlink_to(src_root, target_is_directory=True)
    except OSError as exc:
        _log_err(f"Failed to link skills root {dest_root}: {exc}")
        failures = 1
    return failures


def _merge_dir_into(src: Path, dest: Path) -> int:
    """Union-move every entry of src into dest; src (the live harness copy) wins."""
    moved = 0
    for child in sorted(src.iterdir()):
        target = dest / child.name
        if child.is_dir():
            if target.exists() and not target.is_dir():
                target.unlink()
            target.mkdir(parents=True, exist_ok=True)
            moved += _merge_dir_into(child, target)
            if not any(child.iterdir()):
                child.rmdir()
        else:
            if target.is_file():
                target.unlink()
            shutil.move(str(child), str(target))
            moved += 1
    return moved


# --- provider settings helpers (single-level skill scan) -----------------------

def _tilde(path: Path) -> str:
    """Render a path HOME-relative with a ~ prefix, the form settings.json uses."""
    home = Path.home()
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return path.as_posix()


def _in_pack(entry: str, pack_root: Path) -> bool:
    try:
        return Path(os.path.expanduser(entry.strip())).resolve().is_relative_to(pack_root)
    except OSError:
        return False


def _read_settings(settings_file: Path):
    try:
        raw = settings_file.read_text(encoding="utf-8") if settings_file.is_file() else ""
        settings = json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError) as exc:
        _log_warn(f"Could not read {settings_file} ({exc}); leaving it untouched.")
        return None, False
    if not isinstance(settings, dict):
        _log_warn(f"{settings_file} is not a JSON object; leaving it untouched.")
        return None, False
    return settings, True


def _write_settings(settings_file: Path, settings: dict) -> None:
    """Atomic write: sibling + rename so concurrent readers never see truncation."""
    tmp = settings_file.with_name(settings_file.name + ".tmp")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, settings_file)


def _sync_skill_directories(adapter, dry_run: bool) -> None:
    """Register every pack category folder as a skills root in settings.json.

    The list is rebuilt from disk every time instead of being appended to,
    so a renamed or deleted category is pruned on the next run. Entries that
    point outside the pack are the user's own roots and are preserved.
    """
    settings_file = adapter.mcp_config_file()
    roots = discover_skill_roots()
    pack_root = (REPO_ROOT / "skills").resolve()
    want = [_tilde(r) for r in roots]
    settings, usable = _read_settings(settings_file)
    if not usable:
        return
    skills = settings.setdefault("skills", {})
    if not isinstance(skills, dict):
        _log_warn("skills is not an object; skill directory sync SKIPPED.")
        return
    current = skills.get("directories")
    if current is not None and not isinstance(current, list):
        _log_warn("skills.directories is not a list; skill directory sync SKIPPED.")
        return
    current = [str(d) for d in (current or [])]
    foreign = [d for d in current if not _in_pack(d, pack_root)]
    if set(current) == set(foreign) | set(want):
        _log_skip(f"{len(want)} pack skill directories already registered in {settings_file}")
        return
    added = [d for d in want if d not in current]
    dropped = [d for d in current if _in_pack(d, pack_root) and d not in want]
    if dry_run:
        _log_sub(f"[DRY-RUN] Would register {len(want)} skill directories in "
                 f"{settings_file} (+{len(added)} new, -{len(dropped)} stale)")
        return
    skills["directories"] = foreign + want
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    _write_settings(settings_file, settings)
    _log_ok(f"Registered {len(want)} skill directories in {settings_file} "
            f"(+{len(added)} new, -{len(dropped)} stale).")
    if added or dropped:
        _log_sub("Restart any running session to pick the list up.")


def _sync_skill_hook(adapter, dry_run: bool) -> None:
    """Install or refresh the SessionStart hook that re-registers skill roots."""
    hook_name = getattr(adapter, "skill_sync_hook_name", None)
    if not hook_name:
        return
    commands = tuple(getattr(adapter, "skill_sync_commands", None) or ())
    if not commands:
        return
    command = commands[0]
    settings_file = adapter.mcp_config_file()
    settings, usable = _read_settings(settings_file)
    if not usable:
        return
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        _log_warn("hooks is not an object; skill sync hook SKIPPED.")
        return
    starts = hooks.setdefault("SessionStart", [])
    if not isinstance(starts, list):
        _log_warn("hooks.SessionStart is not a list; skill sync hook SKIPPED.")
        return
    for group in starts:
        if not isinstance(group, dict):
            continue
        owned = next((h for h in (group.get("hooks") or [])
                      if isinstance(h, dict) and h.get("name") == hook_name), None)
        if owned is None:
            continue
        if owned.get("command") == command:
            _log_skip(f"Skill sync hook already installed in {settings_file}")
            return
        if dry_run:
            _log_sub(f"[DRY-RUN] Would refresh the '{hook_name}' hook command in {settings_file}")
            return
        owned["command"] = command
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        _write_settings(settings_file, settings)
        _log_ok(f"Refreshed the '{hook_name}' hook command in {settings_file}.")
        return
    if dry_run:
        _log_sub(f"[DRY-RUN] Would install the '{hook_name}' SessionStart hook in {settings_file}")
        return
    starts.append({
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "name": hook_name,
            "command": command,
            "timeout": 30000,
        }],
    })
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    _write_settings(settings_file, settings)
    _log_ok(f"Installed the '{hook_name}' SessionStart hook in {settings_file}.")
