"""Harness disconnect capability — removes what connect wrote (FR-002).

MCP servers, env keys, and router references alike. Only generated artifacts
are removed — hand-written harness config is never touched.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from modules.config.src.capabilities_config_engine import (
    arwaky_server_names,
    load_file,
    remove_env_keys,
    remove_mcp_servers,
    save_file,
)
from modules.harness.src.contract_harness_protocol import IHarnessDisconnector
from modules.harness.src.taxonomy_harness_constant import ALL_HARNESS_IDS
from modules.harness.src.taxonomy_harness_vo import (
    RouterCredentials,
    UnsupportedHarnessError,
)
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
from modules.shared.src.taxonomy_skill_audit import iter_skill_files

LOG_SUB = lambda msg: print(f"  -> {msg}")
LOG_OK = lambda msg: print(f"  ✓ {msg}")
LOG_SKIP = lambda msg: print(f"  ⟳ {msg}")
LOG_WARN = lambda msg: print(f"  ⚠ {msg}")
LOG_ERR = lambda msg: print(f"  ✗ {msg}", file=sys.stderr)


def _log_header(msg: str) -> None:
    print(f"==> {msg}")


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


@dataclass
class DisconnectOpts:
    dry_run: bool = False
    adapters: dict[str, object] = field(default_factory=dict, repr=False)

    def adapter(self, harness_id: str):
        try:
            return self.adapters[harness_id]
        except KeyError:
            raise UnsupportedHarnessError(harness_id, ALL_HARNESS_IDS) from None


class HarnessDisconnector(IHarnessDisconnector):
    """Registry-keyed disconnect capability (composition root injects adapters).

    # Block 1: Constructor
    # Block 2: Protocol ABC Method Implementation
    # Block 3: Dunder Methods, Factories & Helpers
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, adapters: dict[str, object]) -> None:
        self._adapters = adapters

    # -- Block 2: Protocol ABC Method Implementation ----------------------------
    def disconnect(self, harness_ids: tuple[str, ...], dry_run: bool = False) -> int:
        """FR-002: remove MCP servers, env keys, and router references.

        Idempotent no-op when the harness was never connected. Returns exit code.
        """
        opts = DisconnectOpts(dry_run=dry_run, adapters=self._adapters)
        failures = 0
        for harness_id in harness_ids:
            adapter = opts.adapter(harness_id)
            failures += self._disconnect_one(harness_id, adapter, opts)
        return 1 if failures else 0

    # -- Block 3: Dunder Methods, Factories & Helpers ----------------------------
    def _disconnect_one(self, harness_id: str, adapter, opts: DisconnectOpts) -> int:
        _log_header(f"Disconnecting from {adapter.display}...")
        failures = 0
        servers = arwaky_server_names(Path(REPO_ROOT))
        for label, target_dir in adapter.mcp_targets():
            cfg = adapter.mcp_config_file(target_dir)
            if cfg.exists():
                if opts.dry_run:
                    _log_sub(f"[DRY-RUN] Would remove agents-arwaky MCP servers from {cfg}")
                else:
                    try:
                        removed = remove_mcp_servers(cfg, servers, opts.dry_run)
                    except (OSError, ValueError) as exc:
                        _log_err(f"{harness_id}: MCP removal from {cfg} failed: {exc}")
                        failures += 1
                        continue
                    if removed:
                        _log_ok(f"Removed agents-arwaky MCP servers from {cfg}")
                    else:
                        _log_skip(f"No agents-arwaky MCP servers found in {cfg}")
        _remove_skill_provisioned(adapter.skills_dir(), opts.dry_run)
        _remove_router_refs(harness_id, adapter, opts)
        for env_file in adapter.env_files():
            if env_file.exists():
                try:
                    removed = remove_env_keys(env_file, list(adapter.env_keys), opts.dry_run)
                except OSError as exc:
                    _log_err(f"{harness_id}: env removal from {env_file} failed (read-only?): {exc}")
                    failures += 1
                else:
                    if removed and not opts.dry_run:
                        _log_ok(f"Removed env keys {removed} from {env_file}")
                    elif opts.dry_run:
                        _log_sub(f"[DRY-RUN] Would remove env keys from {env_file}")
        _log_ok(f"{adapter.display} disconnect complete.")
        return failures


def _remove_skill_provisioned(dest_base: Path, dry_run: bool) -> None:
    """Remove provisioned skill copies under dest_base.

    Prune rule: only entries carrying `.arwaky-skill.json` provenance (pack
    copies) or symlinks pointing into the pack are touched — hand-written
    harness skills are never removed. Root-linked skills dirs are unlinked as
    a whole (the pack itself is left intact).
    """
    if not dest_base.exists():
        return
    if dest_base.is_symlink():
        if dry_run:
            _log_sub(f"[DRY-RUN] Would unlink skills root {dest_base}")
            return
        dest_base.unlink()
        _log_ok(f"Unlinked skills root {dest_base} (pack left intact)")
        return
    pack_root = (REPO_ROOT / "skills").resolve()
    removed = 0
    for skill_md in iter_skill_files(pack_root):
        name = skill_md.parent.name
        dest = dest_base / name
        if dest.is_symlink():
            if dry_run:
                _log_sub(f"[DRY-RUN] Would unlink skill '{name}' -> {dest.resolve()}")
                continue
            dest.unlink()
            _log_ok(f"Unlinked skill '{name}' from {dest_base} (pack source intact)")
            removed += 1
        elif dest.is_dir():
            # Only delete when the copy matches the pack (pure snapshot or
            # provenance-carrying) — a divergent hand-written skill stays.
            if _copy_matches_pack(dest, skill_md.parent):
                if dry_run:
                    _log_sub(f"[DRY-RUN] Would remove skill '{name}' from {dest_base}")
                    continue
                import shutil
                shutil.rmtree(dest)
                _log_ok(f"Removed skill '{name}' from {dest_base}")
                removed += 1
    if removed:
        _log_ok(f"{removed} skill(s) removed from {dest_base}")


def _copy_matches_pack(dest_dir: Path, src_dir: Path) -> bool:
    """True when a provisioned copy is still byte-identical to its pack source."""
    for f in src_dir.rglob("*"):
        if f.is_dir() or "__pycache__" in f.parts:
            continue
        peer = dest_dir / f.relative_to(src_dir)
        if not peer.is_file() or peer.read_bytes() != f.read_bytes():
            return False
    return True


def _remove_router_refs(harness_id: str, adapter, opts: DisconnectOpts) -> None:
    """Drop router provider entries installed by the connect capability.

    Router references are dropped alongside the env keys they were installed
    with (FR-002). Foreign providers in the same files are preserved.
    """
    if not adapter.supports_custom_api:
        return
    kind = getattr(adapter, "custom_api_kind", "")
    if kind == "router-env":
        return  # env-only router wiring; env keys are dropped by the env pass.
    if kind == "config-toml":
        cfg_file = adapter.mcp_config_file()
        if not cfg_file.exists():
            return
        try:
            data, fmt = load_file(cfg_file)
        except (OSError, ValueError) as exc:
            _log_warn(f"Could not read {cfg_file} ({exc}); router ref removal SKIPPED.")
            return
        provider_id = adapter.router_provider_id
        models = data.get("models")
        changed = False
        if isinstance(models, dict) and models.get("default") == provider_id:
            models.pop("default", None)
            changed = True
        model = data.get("model")
        if isinstance(model, dict) and provider_id in model:
            model.pop(provider_id, None)
            changed = True
        if not changed:
            _log_skip(f"No router references found in {cfg_file}")
            return
        if opts.dry_run:
            _log_sub(f"[DRY-RUN] Would remove router provider '{provider_id}' from {cfg_file}")
            return
        if not save_file(cfg_file, data, fmt):
            _log_err(f"{harness_id}: failed to remove router refs from {cfg_file}")
            return
        _log_ok(f"Removed router provider '{provider_id}' from {cfg_file}")
    elif kind == "settings-jsonc":
        settings_file = adapter.mcp_config_file()
        if not settings_file.is_file():
            return
        try:
            raw = settings_file.read_text(encoding="utf-8")
            settings = json.loads(raw) if raw.strip() else {}
        except (OSError, ValueError) as exc:
            _log_warn(f"Could not read {settings_file} ({exc}); router ref removal SKIPPED.")
            return
        if not isinstance(settings, dict):
            return
        provider_id = adapter.router_provider_id
        removed = 0
        openai = settings.get("modelProviders", {}).get("openai")
        if isinstance(openai, list):
            kept = [m for m in openai if not (isinstance(m, dict)
                                               and m.get("id") == provider_id)]
            removed += len(openai) - len(kept)
            if kept:
                settings["modelProviders"]["openai"] = kept
            else:
                settings["modelProviders"].pop("openai", None)
        auth = settings.get("security", {}).get("auth", {})
        if auth.get("selectedType") == "openai":
            auth.pop("selectedType", None)
        model = settings.get("model")
        if isinstance(model, dict) and model.get("name") == provider_id:
            model.pop("name", None)
            model.pop("baseUrl", None)
        skills = settings.get("skills")
        if isinstance(skills, dict):
            # Skill directories pointing into the pack are gone now.
            pack_root = (REPO_ROOT / "skills").resolve()
            dirs = skills.get("directories")
            if isinstance(dirs, list):
                kept_dirs = [d for d in dirs if not _in_pack(d, pack_root)]
                removed += len(dirs) - len(kept_dirs)
                if kept_dirs:
                    skills["directories"] = kept_dirs
                else:
                    skills.pop("directories", None)
                if not skills:
                    settings.pop("skills", None)
        hooks = settings.get("hooks")
        if isinstance(hooks, dict):
            starts = hooks.get("SessionStart")
            if isinstance(starts, list):
                kept_groups, hook_removed = [], 0
                for group in starts:
                    if not isinstance(group, dict):
                        kept_groups.append(group)
                        continue
                    others = [h for h in (group.get("hooks") or [])
                              if not (isinstance(h, dict) and h.get("name") == getattr(adapter, "skill_sync_hook_name", "arwaky-skill-sync"))]
                    hook_removed += len(group.get("hooks") or []) - len(others)
                    if others:
                        kept_groups.append({**group, "hooks": others})
                removed += hook_removed
                hooks["SessionStart"] = kept_groups
                if not kept_groups:
                    hooks.pop("SessionStart", None)
                if not hooks:
                    settings.pop("hooks", None)
        if not removed:
            _log_skip(f"No router/skill references found in {settings_file}")
            return
        if opts.dry_run:
            _log_sub(f"[DRY-RUN] Would remove router/skill references from {settings_file}")
            return
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = settings_file.with_name(settings_file.name + ".tmp")
        tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, settings_file)
        _log_ok(f"Removed {removed} router/skill reference(s) from {settings_file}")


def _in_pack(entry: str, pack_root: Path) -> bool:
    """True when a skills.directories entry points at the pack (any spelling)."""
    try:
        return Path(os.path.expanduser(entry.strip())).resolve().is_relative_to(pack_root)
    except OSError:
        return False
