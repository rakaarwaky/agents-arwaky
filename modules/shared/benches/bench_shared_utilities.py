"""Benchmarks for modules/shared — performance regression detection."""
from __future__ import annotations

import tempfile
from pathlib import Path


def bench_parse_env_file(benchmark):
    """BENCH-SHARED-001: parse_env_file performance."""
    from modules.shared.src.utility_envfile_parser import parse_env_file

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("KEY1=value1\n")
        f.write("KEY2=value2\n")
        f.write("KEY3=value3\n")
        f.flush()
        path = Path(f.name)

    benchmark(parse_env_file, path)
    path.unlink(missing_ok=True)


def bench_update_env_file(benchmark):
    """BENCH-SHARED-002: update_env_file performance."""
    from modules.shared.src.utility_envfile_parser import update_env_file

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("")
        f.flush()
        path = Path(f.name)

    def _update():
        update_env_file(path, "KEY", "value")

    benchmark(_update)
    path.unlink(missing_ok=True)


def bench_load_tools(benchmark):
    """BENCH-SHARED-003: load_tools performance."""
    from modules.shared.src.utility_manifest_reader import load_tools

    benchmark(load_tools)


def bench_find_tool(benchmark):
    """BENCH-SHARED-004: find_tool performance."""
    from modules.shared.src.utility_manifest_reader import find_tool

    benchmark(find_tool, "lint")


def bench_data_home(benchmark):
    """BENCH-SHARED-005: data_home performance."""
    from modules.shared.src.taxonomy_common_vo import data_home

    benchmark(data_home)


def bench_config_home(benchmark):
    """BENCH-SHARED-006: config_home performance."""
    from modules.shared.src.taxonomy_common_vo import config_home

    benchmark(config_home)


def bench_strip_jsonc_comments(benchmark):
    """BENCH-SHARED-007: strip_jsonc_comments performance."""
    from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

    sample = '{"key": "value"} // comment' * 100

    benchmark(strip_jsonc_comments, sample)


def bench_write_toml(benchmark):
    """BENCH-SHARED-008: write_toml performance."""
    from modules.shared.src.utility_toml_write import write_toml

    data = {
        "key": "value",
        "number": 42,
        "nested": {
            "a": 1,
            "b": 2,
        },
        "list": [1, 2, 3],
    }

    benchmark(write_toml, data)


def bench_extract_skill_name(benchmark):
    """BENCH-SHARED-009: extract_skill_name performance."""
    from modules.shared.src.taxonomy_skill_vo import extract_skill_name

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: test-skill\ndescription: test\n---\n\n# Skill\n")

        benchmark(extract_skill_name, skill_file)


def bench_sections(benchmark):
    """BENCH-SHARED-010: sections performance."""
    from modules.shared.src.utility_doc_pack import sections

    content = "\n".join(f"## Section {i}\n\nContent for section {i}" for i in range(100))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        path = Path(f.name)

    benchmark(sections, path)
    path.unlink(missing_ok=True)


def bench_audit_docs(benchmark):
    """BENCH-SHARED-011: audit_docs performance."""
    from modules.shared.src.utility_doc_pack import audit_docs

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        benchmark(audit_docs, path)


def bench_resolve_executable(benchmark):
    """BENCH-SHARED-012: resolve_executable performance."""
    from modules.shared.src.utility_tool_resolve import resolve_executable

    benchmark(resolve_executable, "python3")


def bench_normalize_tool_id(benchmark):
    """BENCH-SHARED-013: normalize_tool_id performance."""
    from modules.shared.src.utility_skill_registry import normalize_tool_id

    benchmark(normalize_tool_id, "lint")


def bench_get_registered_tool_ids(benchmark):
    """BENCH-SHARED-014: get_registered_tool_ids performance."""
    from modules.shared.src.utility_skill_registry import get_registered_tool_ids

    benchmark(get_registered_tool_ids)


def bench_parse_tables(benchmark):
    """BENCH-SHARED-015: parse_tables performance."""
    from modules.shared.src.utility_doc_pack import parse_tables

    content = """# Table Test

| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |

| C | D |
|---|---|
| 5 | 6 |
| 7 | 8 |
"""

    benchmark(parse_tables, content)
