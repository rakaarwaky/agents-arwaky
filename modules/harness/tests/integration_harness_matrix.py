"""End-to-end capability sweep over every supported harness adapter."""
from __future__ import annotations

from pathlib import Path


def test_supported_harnesses_connect_disconnect_and_skills_roundtrip(
    tmp_path: Path, monkeypatch
) -> None:
    """HRS-01/HRS-05: all canonical providers provision, disconnect, and no-op cleanly."""
    from modules.harness.src import capabilities_harness_connector as connector_module
    from modules.harness.src.capabilities_harness_disconnector import (
        HarnessDisconnector,
    )
    from modules.harness.src.capabilities_harness_skills import HarnessSkills
    from modules.harness.src.root_harness_container import HARNESS_REGISTRY
    from modules.shared.src.common.taxonomy_common_constant import REPO_ROOT
    from modules.shared.src.common.utility_config_engine import get_mcp_map, load_file
    from modules.shared.src.harness.taxonomy_harness_constant import ALL_HARNESS_IDS

    home = tmp_path / "home"
    (home / ".hermes" / "profiles" / "profile-a").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    monkeypatch.delenv("GROK_HOME", raising=False)

    credentials = tmp_path / "no-credentials.env"
    for adapter in HARNESS_REGISTRY.values():
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidate=credentials: (candidate,),
        )

    servers = {"context7": {"command": "context7-mcp", "args": []}}
    monkeypatch.setattr(connector_module, "_load_generated_servers", lambda: servers)

    ids = tuple(ALL_HARNESS_IDS)
    assert set(HARNESS_REGISTRY) == set(ids)
    skills = HarnessSkills(HARNESS_REGISTRY)
    connector = connector_module.HarnessConnector(
        HARNESS_REGISTRY, skills=skills
    )
    disconnector = HarnessDisconnector(HARNESS_REGISTRY)

    # Disconnecting an untouched harness is a successful idempotent no-op.
    assert disconnector.disconnect(ids) == 0

    assert connector.connect(ids) == 0
    for harness_id in ids:
        adapter = HARNESS_REGISTRY[harness_id]
        for _label, target_dir in adapter.mcp_targets():
            config = adapter.mcp_config_file(target_dir)
            assert config.is_file(), f"{harness_id} did not create {config}"
            document, _fmt = load_file(config)
            mcp, _key = get_mcp_map(document)
            assert mcp is not None and "context7" in mcp

        targets = getattr(adapter, "skills_targets", None)
        skill_dirs = (
            [path for _label, path in targets()]
            if callable(targets)
            else [adapter.skills_dir()]
        )
        for skills_dir in skill_dirs:
            assert skills_dir.is_symlink(), f"{harness_id} skills were not linked: {skills_dir}"
            assert skills_dir.resolve() == (REPO_ROOT / "skills").resolve()

    # The dedicated skills capability is also safe to rerun for the full set.
    assert skills.provision_skills(ids) == 0
    assert disconnector.disconnect(ids) == 0

    for harness_id in ids:
        adapter = HARNESS_REGISTRY[harness_id]
        for _label, target_dir in adapter.mcp_targets():
            config = adapter.mcp_config_file(target_dir)
            document, _fmt = load_file(config)
            mcp, _key = get_mcp_map(document)
            assert mcp is None or "context7" not in mcp

        targets = getattr(adapter, "skills_targets", None)
        skill_dirs = (
            [path for _label, path in targets()]
            if callable(targets)
            else [adapter.skills_dir()]
        )
        assert all(not path.is_symlink() for path in skill_dirs)
