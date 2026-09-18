"""Hermes Agent harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

from modules.harness.src.capabilities_harness_shared import (  # type: ignore[import-not-found]
    REPO_ROOT,
    provision_skill_to_dir,
    resolve_skill_link,
    link_skills_root,
    disconnect_hermes_instance,
    engine_merge_mcp,
    get_all_skill_files,
    hermes_home,
    hermes_targets,
    inject_9router_env,
    load_generated_servers,
    log_header,
    log_ok,
    log_sub,
)
from modules.shared.src.harness.contract_harness_protocol import IHarnessConnector

HARNESS_ID = "hermes"
ALIASES = ("--hermes", "hermes")
ENV_TARGET = "hermes"
# Symlink provisioning gate: Verified: Hermes walks skills with followlinks and its atomic writes land inside the linked dir.
SKILL_LINK_VERIFIED = True


def connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills=False):
    log_header("Connecting to Hermes Agent (MCP & env: all profiles · Skills: default only)...")
    h = hermes_home()
    servers = load_generated_servers()
    if not skills_only and not env_only:
        for label, target_dir in hermes_targets(h):
            log_sub(f"Target MCP Config: {target_dir / 'config.yaml'}")
            if dry_run:
                log_sub(f"[DRY-RUN] Would merge MCP servers into {target_dir / 'config.yaml'}")
                continue
            target_dir.mkdir(parents=True, exist_ok=True)
            engine_merge_mcp(target_dir / "config.yaml", servers, force)
            log_ok(f"Hermes MCP servers configured in {target_dir / 'config.yaml'}")
    if not mcp_only and not env_only:
        # Skills: the harness skills ROOT becomes a symlink to the pack, so
        # managing skills happens in exactly one place (agents-arwaky/skills/)
        # and every linked harness sees additions/removals/edits instantly.
        # Per-skill linking is the fallback for --copy-skills=False harnesses
        # that we do not root-link. Hermes profile skills live under the root
        # link only for the DEFAULT profile; named profiles stay curated copies
        # (Raka's rule) and are untouched here.
        link = resolve_skill_link(SKILL_LINK_VERIFIED, copy_skills)
        skills_root = h / "skills"
        if link:
            log_sub(f"Target Skills: {skills_root} -> {REPO_ROOT / 'skills'} "
                    f"(whole-root symlink; manage the pack once)")
            link_skills_root(skills_root, REPO_ROOT / "skills", force, dry_run)
        else:
            # Skills are provisioned ONLY into the main/default profile.
            # Named profiles under ~/.hermes/profiles/* are task-specific
            # specialists and must not carry the generalist skill pack.
            log_sub(f"Target Skills: {skills_root} (default profile only, copied)")
            for sf in get_all_skill_files():
                provision_skill_to_dir(sf, skills_root, force, dry_run, link=False)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env(ENV_TARGET, dry_run)
    log_ok("Hermes connect complete.")


def disconnect(dry_run):
    log_header("Disconnecting from Hermes Agent (Main & Multi-Profiles)...")
    h = hermes_home()
    disconnect_hermes_instance(h, "Main Profile", dry_run)
    profiles = h / "profiles"
    if profiles.is_dir():
        for pdir in sorted(profiles.iterdir()):
            if pdir.is_dir():
                disconnect_hermes_instance(pdir, f"Profile: {pdir.name}", dry_run)
    log_ok("Hermes disconnect complete.")


class HermesConnector(IHarnessConnector):
    """Module-level connect/disconnect bound to the IHarnessConnector contract."""

    def connect(self, force: bool, dry_run: bool, mcp_only: bool, skills_only: bool, env_only: bool, copy_skills: bool = False) -> None:
        connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills)

    def disconnect(self, force: bool, dry_run: bool) -> None:
        disconnect(dry_run)


def register() -> dict:
    """Register this harness adapter in the global registry."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "connect": connect,
        "disconnect": disconnect,
    }
