"""Benchmarks for modules/config — performance regression detection."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path


def bench_config_writer_instantiation(benchmark):
    """BENCH-CONFIG-001: ConfigWriter instantiation performance."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    benchmark(ConfigWriter)


def bench_config_modifier_instantiation(benchmark):
    """BENCH-CONFIG-002: ConfigModifier instantiation performance."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    benchmark(ConfigModifier)


def bench_config_orchestrator_instantiation(benchmark):
    """BENCH-CONFIG-003: ConfigOrchestrator instantiation performance."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    def _create():
        writer = ConfigWriter()
        modifier = ConfigModifier()
        return ConfigOrchestrator(writer, modifier)

    benchmark(_create)


def bench_config_container_instantiation(benchmark):
    """BENCH-CONFIG-004: ConfigContainer instantiation performance."""
    from modules.config.src.root_config_container import ConfigContainer

    benchmark(ConfigContainer)


def bench_detect_format_json(benchmark):
    """BENCH-CONFIG-005: detect_format on JSON file."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"key": "value"}')
        f.flush()
        path = Path(f.name)

    benchmark(writer.detect_format, path)
    path.unlink(missing_ok=True)


def bench_detect_format_toml(benchmark):
    """BENCH-CONFIG-006: detect_format on TOML file."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[section]\nkey = "value"')
        f.flush()
        path = Path(f.name)

    benchmark(writer.detect_format, path)
    path.unlink(missing_ok=True)


def bench_load_json_file(benchmark):
    """BENCH-CONFIG-007: load_file on JSON."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"key": "value", "nested": {"a": 1, "b": 2}}))
        f.flush()
        path = Path(f.name)

    benchmark(writer.load_file, path)
    path.unlink(missing_ok=True)


def bench_load_toml_file(benchmark):
    """BENCH-CONFIG-008: load_file on TOML."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[section]\nkey = "value"\nnumber = 42\n')
        f.flush()
        path = Path(f.name)

    benchmark(writer.load_file, path)
    path.unlink(missing_ok=True)


def bench_save_json_file(benchmark):
    """BENCH-CONFIG-009: save_file on JSON."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    data = ConfigData({"key": "value"})
    fmt = ConfigFormat("json")

    def _save():
        writer.save_file(path, data, fmt)

    benchmark(_save)
    path.unlink(missing_ok=True)


def bench_list_mcp_servers_empty(benchmark):
    """BENCH-CONFIG-010: list_mcp_servers on empty config."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    modifier = ConfigModifier()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    benchmark(modifier.list_mcp_servers, path)
    path.unlink(missing_ok=True)


def bench_merge_servers(benchmark):
    """BENCH-CONFIG-011: merge_mcp_servers performance."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    modifier = ConfigModifier()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    servers = {f"server-{i}": {"url": f"http://server-{i}.local"} for i in range(10)}

    def _merge():
        return modifier.merge_mcp_servers(path, servers)

    benchmark(_merge)
    path.unlink(missing_ok=True)


def bench_set_env_keys(benchmark):
    """BENCH-CONFIG-012: set_env_keys performance."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    modifier = ConfigModifier()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('')
        f.flush()
        path = Path(f.name)

    pairs = {f"KEY_{i}": f"value_{i}" for i in range(20)}

    def _set():
        return modifier.set_env_keys(path, pairs)

    benchmark(_set)
    path.unlink(missing_ok=True)


def bench_orchestrator_inspect(benchmark):
    """BENCH-CONFIG-013: ConfigOrchestrator.inspect performance."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"mcpServers": {"server1": {"url": "http://test"}}}))
        f.flush()
        path = Path(f.name)

    benchmark(orch.inspect, path)
    path.unlink(missing_ok=True)


def bench_help_text(benchmark):
    """BENCH-CONFIG-014: ConfigOrchestrator.help performance."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)

    benchmark(orch.help)


def bench_execute_load(benchmark):
    """BENCH-CONFIG-015: execute('load') dispatcher performance."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"key": "value"}')
        f.flush()
        path = Path(f.name)

    benchmark(writer.execute, "load", path)
    path.unlink(missing_ok=True)


def bench_execute_save(benchmark):
    """BENCH-CONFIG-016: execute('save') dispatcher performance."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    def _save():
        return writer.execute("save", path, {"data": {"key": "value"}, "fmt": "json"})

    benchmark(_save)
    path.unlink(missing_ok=True)


def bench_normalize_jsonc(benchmark):
    """BENCH-CONFIG-017: normalize_jsonc performance."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    sample = '{"key": "value"} // comment' * 100

    benchmark(writer.normalize_jsonc, sample)


def bench_dumps_toml(benchmark):
    """BENCH-CONFIG-018: dumps_toml serialization performance."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    data = {
        "key": "value",
        "number": 42,
        "nested": {"a": 1, "b": 2},
        "list": [1, 2, 3],
    }

    benchmark(writer.dumps_toml, data)
