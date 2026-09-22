"""Harness connect capability — MCP config + env entries + 9Router wiring.

FR-001 business action: for each resolved harness id, merge the generated MCP
servers into the provider's config, set the provider's env keys, and — when the
adapter declares custom-API support — bind the 9Router provider entry. Router
wiring is a clause of connect, not a separate action.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from modules.harness.src.contract_harness_protocol import (
    IHarnessAdapter,
    IHarnessConnector,
    IHarnessSkills,
)
from modules.harness.src.taxonomy_harness_constant import ALL_HARNESS_IDS
from modules.harness.src.taxonomy_harness_vo import (
    RouterCredentials,
    UnsupportedHarnessError,
)
from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_vo import data_home
from modules.shared.src.utility_config_engine import (
    arwaky_server_names,
    load_file,
    merge_mcp_servers,
    save_file,
    set_env_keys,
)

LOG_SUB = lambda msg: print(f"  -> {msg}")
LOG_OK = lambda msg: print(f"  ✓ {msg}")
LOG_SKIP = lambda msg: print(f"  ⟳ {msg}")
LOG_WARN = lambda msg: print(f"  ⚠ {msg}")
LOG_ERR = lambda msg: print(f"  ✗ {msg}", file=sys.stderr)

_PLACEHOLDER_KEYS = {"sk-your-9router-consumer-key-here", "<YOUR_API_KEY>", "change-me", ""}


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
class ConnectOpts:
    """FR-001 option bag; scope gates default off so everything runs."""

    force: bool = False
    dry_run: bool = False
    mcp_only: bool = False
    skills_only: bool = False
    env_only: bool = False
    router: bool = False
    copy_skills: bool = False
    adapters: dict[str, object] = field(default_factory=dict, repr=False)

    def adapter(self, harness_id: str):
        try:
            return self.adapters[harness_id]
        except KeyError:
            raise UnsupportedHarnessError(harness_id, ALL_HARNESS_IDS) from None


class BoundAdapter(IHarnessAdapter):
    """Capabilities-layer binding of a utility leaf to the adapter protocol (AES502)."""

    def __init__(self, leaf: object) -> None:
        self._leaf = leaf

    @property
    def id(self) -> str:
        return self._leaf.id

    @property
    def aliases(self) -> tuple[str, ...]:
        return self._leaf.aliases

    @property
    def display(self) -> str:
        return self._leaf.display

    @property
    def skill_link_verified(self) -> bool:
        return self._leaf.skill_link_verified

    @property
    def supports_mcp(self) -> bool:
        return self._leaf.supports_mcp

    @property
    def supports_env(self) -> bool:
        return self._leaf.supports_env

    @property
    def supports_custom_api(self) -> bool:
        return self._leaf.supports_custom_api

    @property
    def custom_api_kind(self) -> str:
        return self._leaf.custom_api_kind

    @property
    def router_provider_id(self) -> str:
        return self._leaf.router_provider_id

    @property
    def env_key(self) -> str:
        return self._leaf.env_key

    @property
    def mcp_key(self) -> str:
        return self._leaf.mcp_key

    @property
    def env_keys(self) -> tuple[str, ...]:
        return self._leaf.env_keys

    def home(self) -> Path:
        return self._leaf.home()

    def config_files(self) -> tuple[Path, ...]:
        return self._leaf.config_files()

    def env_files(self) -> tuple[Path, ...]:
        return self._leaf.env_files()

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return self._leaf.mcp_config_file(target_dir)

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        return self._leaf.mcp_targets()

    def skills_dir(self) -> Path:
        return self._leaf.skills_dir()

    def session_conf_files(self) -> tuple[Path, ...]:
        return self._leaf.session_conf_files()

    def credential_candidates(self) -> tuple[Path, ...]:
        return self._leaf.credential_candidates()


def _router_v1(url: str) -> str:
    base = url.rstrip("/")
    return base if base.endswith("/v1") else base + "/v1"


def get_9router_credentials(candidates) -> RouterCredentials:
    """Read NINEROUTER_URL/KEY from env candidates; fallback default URL."""
    router_url = f"http://127.0.0.1:{os.environ.get('NINEROUTER_PORT', '20128')}"
    router_key = ""
    for cand in candidates:
        cand = Path(cand)
        if not cand.is_file():
            continue
        try:
            text = cand.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.startswith("NINEROUTER_URL="):
                router_url = line.split("=", 1)[1].strip().strip('"\'')
            elif line.startswith("NINEROUTER_KEY="):
                router_key = line.split("=", 1)[1].strip().strip('"\'')
        # Break only for a non-placeholder key; later candidates may still apply.
        if router_key and router_key not in _PLACEHOLDER_KEYS:
            break
    return RouterCredentials(url=router_url, key=router_key)


def load_generated_servers() -> dict[str, dict]:
    """Read mcpServers from mcp_servers.generated.json (or default static map)."""
    gen = REPO_ROOT / "mcp_servers.generated.json"
    if gen.exists():
        try:
            data = json.loads(gen.read_text(encoding="utf-8"))
            servers = data.get("mcpServers", {})
            if servers:
                return servers
        except (OSError, ValueError) as exc:
            _log_warn(f"Could not read {gen} ({exc}); using default servers.")
    return {
        name: {"command": _FALLBACK_MCP_COMMANDS.get(name, f"{name}-mcp")}
        for name in arwaky_server_names(Path(REPO_ROOT))
    }


_FALLBACK_MCP_COMMANDS = {
    "codegraph": "codegraph-mcp",
    "vision": "vision-arwaky-mcp",
    "qwen-web": "qwen-web-mcp",
    "blender": "blender-mcp",
    "lint": "lint-arwaky-mcp",
    "workspace": "workspace-mcp",
    "mnemosyne": "mnemosyne-mcp",
}


def daemon_running(daemon_status_fn) -> bool:
    """9Router liveness probe via the daemon feature's status contract.

    Resolved from the daemon feature, never hardcoded: the endpoint is the
    manager's own status, so a moved gateway is picked up automatically.
    A probe failure (import / timeout) is treated as "unknown", so the
    wiring still lands — a down daemon is reported, not fatal.
    """
    if daemon_status_fn is None:
        return True
    try:
        running = daemon_status_fn()
    except Exception:
        return True
    return bool(running)


class HarnessConnector(IHarnessConnector):
    """Registry-keyed connect capability (composition root injects adapters).

    # Block 1: Constructor (adapter registry + config writer + daemon probe)
    # Block 2: Protocol ABC Method Implementation
    # Block 3: Dunder Methods, Factories & Helpers
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        adapters: dict[str, object],
        daemon_status_fn=None,
        skills: IHarnessSkills | None = None,
    ) -> None:
        self._adapters = adapters
        self._daemon_status_fn = daemon_status_fn
        self._skills = skills

    # -- Block 2: Protocol ABC Method Implementation ----------------------------
    def connect(self, harness_ids: tuple[str, ...], force: bool = False, dry_run: bool = False,
                mcp_only: bool = False, skills_only: bool = False, env_only: bool = False,
                router: bool = False, copy_skills: bool = False) -> int:
        """FR-001: MCP config + env entries + router wiring. Returns exit code."""
        opts = ConnectOpts(force=force, dry_run=dry_run, mcp_only=mcp_only,
                           skills_only=skills_only, env_only=env_only, router=router,
                           copy_skills=copy_skills, adapters=self._adapters)
        servers = load_generated_servers()
        failures = 0
        for harness_id in harness_ids:
            adapter = opts.adapter(harness_id)
            failures += self._connect_one(harness_id, adapter, opts, servers)
        return 1 if failures else 0

    # -- Block 3: Dunder Methods, Factories & Helpers ----------------------------
    def _connect_one(self, harness_id: str, adapter, opts: ConnectOpts, servers: dict) -> int:
        _log_header(f"Connecting to {adapter.display}...")
        failures = 0
        do_mcp = not opts.skills_only and not opts.env_only
        do_env = opts.env_only or (not opts.mcp_only and not opts.skills_only)
        do_router = opts.router and do_env
        # FR-003 clause: skills provisioning runs on connect unless the caller
        # scoped the run to mcp/env/router-only; copy_skills selects the
        # snapshot form instead of the default whole-root symlink.
        do_skills = not opts.mcp_only and not opts.env_only
        if adapter.supports_mcp and not adapter.supports_env:
            do_env = False
        if not adapter.supports_mcp and not adapter.supports_env:
            _log_skip(f"{harness_id} supports neither MCP nor env; skipped.")
            _log_ok(f"{adapter.display} connect complete.")
            return 0

        if do_mcp:
            failures += self._connect_mcp(harness_id, adapter, opts, servers)
        if do_skills:
            failures += self._connect_skills(harness_id, adapter, opts)
        if do_env:
            failures += self._connect_env(adapter, opts)
            if do_router:
                failures += self._connect_router(harness_id, adapter, opts)
        _log_ok(f"{adapter.display} connect complete.")
        return failures

    def _connect_skills(self, harness_id: str, adapter, opts: ConnectOpts) -> int:
        """FR-003 clause of connect: provision the pack into the harness."""
        if self._skills is None:
            _log_warn(f"{harness_id}: skills capability not injected; skill provisioning SKIPPED.")
            return 0
        return self._skills.provision_skills(
            (harness_id,), copy=opts.copy_skills,
            dry_run=opts.dry_run, force=opts.force,
        )

    def _connect_mcp(self, harness_id: str, adapter, opts: ConnectOpts, servers: dict) -> int:
        if opts.dry_run:
            for label, target_dir in adapter.mcp_targets():
                _log_sub(f"[DRY-RUN] Would merge MCP servers into {adapter.mcp_config_file(target_dir)}")
            return 0
        for label, target_dir in adapter.mcp_targets():
            cfg = adapter.mcp_config_file(target_dir)
            _log_sub(f"Target MCP Config: {cfg}")
            try:
                cfg.parent.mkdir(parents=True, exist_ok=True)
                if not cfg.exists():
                    cfg.write_text("", encoding="utf-8")
                merge_mcp_servers(cfg, servers, force=opts.force)
            except (OSError, ValueError, RuntimeError) as exc:
                _log_err(f"{harness_id}: MCP merge into {cfg} failed: {exc}")
                return 1
            _log_ok(f"{adapter.display} MCP servers configured in {cfg}")
            _mirror_mcp_links(harness_id, adapter, cfg, target_dir)
        return 0

    def _connect_env(self, adapter, opts: ConnectOpts) -> int:
        creds = get_9router_credentials(adapter.credential_candidates())
        url, key = creds.url, creds.key
        if not key or key in _PLACEHOLDER_KEYS:
            _log_warn(
                f"No active 9Router API Key found (empty/placeholder); env injection "
                f"SKIPPED for {adapter.id}. Run 'aa 9router' to configure."
            )
            return 0
        pairs = {"NINEROUTER_URL": url, "NINEROUTER_KEY": key}
        m_pairs = {"MNEMOSYNE_DATA_DIR": str(data_home() / "mnemosyne")}
        synced_session = False
        if not opts.dry_run:
            for envd in adapter.session_conf_files():
                if envd.is_file():
                    set_env_keys(envd, pairs)
                    synced_session = True
        if opts.dry_run:
            _log_sub(f"[DRY-RUN] Would inject env into {adapter.id}")
            return 0
        failures = 0
        for e in adapter.env_files():
            try:
                set_env_keys(e, pairs)
                set_env_keys(e, m_pairs)
            except (OSError, ValueError) as exc:
                _log_err(f"{adapter.id}: env write to {e} failed: {exc}")
                failures += 1
        if failures:
            return failures
        _log_ok(f"Injected NINEROUTER_URL/KEY + MNEMOSYNE_DATA_DIR into {adapter.id} environment.")
        if synced_session:
            _log_ok("Synced ~/.config/environment.d/9router.conf (login-session key layer).")
        return 0

    def _connect_router(self, harness_id: str, adapter, opts: ConnectOpts) -> int:
        """9Router custom-API clause of connect (FR-001/FR-005, gated by flag)."""
        if not adapter.supports_custom_api:
            _log_skip(
                f"{harness_id}: adapter lacks custom-API support; router wiring SKIPPED."
            )
            return 0
        creds = get_9router_credentials(adapter.credential_candidates())
        url, key = creds.url, creds.key
        if not daemon_running(self._daemon_status_fn):
            _log_warn(
                "9Router daemon not running; router wiring still applied. "
                "Start it with 'aa 9router start'."
            )
        kind = getattr(adapter, "custom_api_kind", "")
        if kind == "config-toml":
            return _connect_router_toml(adapter, url, key, opts)
        if kind == "settings-jsonc":
            return _connect_router_settings(adapter, url, key, opts)
        if kind == "router-env":
            _log_skip(f"{adapter.id}: custom-API is env-only (NINEROUTER_URL/KEY); no config-file provider entry to write.")
            return 0
        _log_skip(f"{adapter.id}: unknown custom-API kind '{kind}'; router wiring SKIPPED.")
        return 0


def _mirror_mcp_links(harness_id: str, adapter, cfg: Path, target_dir: Path) -> None:
    """Antigravity only: mirror mcp_config.json into the sub-tool homes."""
    mirror = getattr(adapter, "mirror_dirs", ())
    if not mirror:
        return
    home = target_dir
    for sub in mirror:
        d = home.parent / sub
        if not d.is_dir():
            continue
        try:
            (d / "mcp_config.json").unlink(missing_ok=True)
            (d / "mcp_config.json").symlink_to(cfg)
        except OSError:
            pass


def _connect_router_toml(adapter, url: str, key: str, opts: ConnectOpts) -> int:
    """Bind the 9Router provider in a TOML harness config (Grok Build shape)."""
    cfg_file = adapter.mcp_config_file()
    if not cfg_file.exists():
        _log_warn(f"{cfg_file} not found; provider sync SKIPPED.")
        return 0

    try:
        data, fmt = load_file(cfg_file)
    except (OSError, ValueError) as exc:
        _log_warn(f"Could not read {cfg_file} ({exc}); provider sync SKIPPED.")
        return 0
    provider_id = adapter.router_provider_id
    v1 = _router_v1(url)
    data.setdefault("models", {})["default"] = provider_id
    data["model"] = {provider_id: {
        "model": provider_id,
        "base_url": v1,
        "name": provider_id,
        # Reference the key via env, never inline it into the config file.
        "env_key": adapter.env_key,
        "api_backend": "responses",
    }}
    if opts.dry_run:
        _log_sub(f"[DRY-RUN] Would bind 9Router provider '{provider_id}' at {v1} in {cfg_file}")
        return 0
    if not save_file(cfg_file, data, fmt):
        _log_err(f"{adapter.id}: failed to write provider entry in {cfg_file}")
        return 1
    _log_ok(f"9Router provider '{provider_id}' bound to {adapter.env_key} at {v1}.")
    return _probe_router(v1, key, provider_id, adapter.id)


def _connect_router_settings(adapter, url: str, key: str, opts: ConnectOpts) -> int:
    """Bind the 9Router provider in a JSON settings file (Qwen Code shape)."""
    settings_file = adapter.mcp_config_file()
    provider_id = adapter.router_provider_id
    v1 = _router_v1(url)
    try:
        raw = settings_file.read_text(encoding="utf-8") if settings_file.is_file() else ""
        settings = json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError) as exc:
        _log_warn(f"Could not read {settings_file} ({exc}); provider sync SKIPPED.")
        return 0
    if not isinstance(settings, dict):
        _log_warn(f"{settings_file} is not a JSON object; provider sync SKIPPED.")
        return 0
    openai_list = settings.setdefault("modelProviders", {}).setdefault("openai", [])
    if not isinstance(openai_list, list):
        _log_warn("modelProviders.openai is not a list; provider sync SKIPPED.")
        return 0
    entry = next((m for m in openai_list
                  if isinstance(m, dict)
                  and (m.get("id") == provider_id or m.get("baseUrl") == v1)), None)
    if entry is None:
        entry = {"id": provider_id, "name": provider_id}
        openai_list.append(entry)
    model = entry.get("id", provider_id)
    selected = settings.get("security", {}).get("auth", {}).get("selectedType")
    changed = (entry.get("baseUrl") != v1 or entry.get("envKey") != adapter.env_key
               or selected != "openai" or settings.get("model", {}).get("name") != model)
    if opts.dry_run:
        _log_sub(
            f"[DRY-RUN] Would bind provider '{model}' in {settings_file} "
            f"to {adapter.env_key} (baseUrl {v1})" if changed
            else f"[DRY-RUN] Provider '{model}' already bound to {adapter.env_key}"
        )
        return 0
    entry["baseUrl"] = v1
    entry.setdefault("name", model)
    prev_env_key = entry.get("envKey")
    entry["envKey"] = adapter.env_key
    settings.setdefault("security", {}).setdefault("auth", {})["selectedType"] = "openai"
    m = settings.setdefault("model", {})
    m["name"] = model
    m["baseUrl"] = v1
    # The interactive /auth "Custom Provider" flow parks the key inline under
    # settings.env as QWEN_CUSTOM_API_KEY_<...>. Once this connector owns the
    # provider, drop that shadow copy so a rotated 9Router key cannot go stale.
    inline = settings.get("env")
    if (isinstance(inline, dict) and prev_env_key and prev_env_key != adapter.env_key
            and prev_env_key.startswith("QWEN_CUSTOM_API_KEY_") and prev_env_key in inline):
        del inline[prev_env_key]
        if not inline:
            settings.pop("env", None)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_file.with_name(settings_file.name + ".tmp")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, settings_file)
    _log_ok(f"Provider '{model}' bound to {adapter.env_key} at {v1}.")
    return _probe_router(v1, key, model, adapter.id)


def _probe_router(v1_url: str, key: str, model: str, adapter_id: str) -> int:
    """Live POST /chat/completions through the router; non-zero on auth failure.

    Secret (the key) is sent as a header only, never written into any config.
    """
    if not key or key in _PLACEHOLDER_KEYS:
        _log_warn(f"No active 9Router key to verify provider for {adapter_id}.")
        return 0
    req = urllib.request.Request(
        v1_url + "/chat/completions",
        data=json.dumps({"model": model,
                         "messages": [{"role": "user", "content": "ping"}],
                         "max_tokens": 1}).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            _log_ok(f"9Router live check passed (HTTP {resp.status}).")
            return 0
    except urllib.error.HTTPError as exc:
        _log_warn(f"9Router live check FAILED (HTTP {exc.code}). Check the key with 'aa 9router'.")
        return 0
    except (OSError, ValueError) as exc:
        _log_warn(f"9Router live check FAILED ({exc}).")
        return 0
