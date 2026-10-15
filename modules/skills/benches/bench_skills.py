"""Benchmarks for modules/skills — performance testing."""
from __future__ import annotations


def bench_skills_index_builder_init(benchmark):
    """BENCH-SKILLS-001: Benchmark SkillsIndexBuilder initialization."""
    from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder

    benchmark(SkillsIndexBuilder)


def bench_skills_list_skills(benchmark):
    """BENCH-SKILLS-002: Benchmark list_skills on the real pack."""
    from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder

    builder = SkillsIndexBuilder()

    def _list():
        return list(builder.list_skills())

    benchmark(_list)


def bench_skills_show_skill(benchmark):
    """BENCH-SKILLS-003: Benchmark show_skill on the real pack."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder

    builder = SkillsIndexBuilder()

    def _show():
        return builder.show_skill(SkillQuery("fetch-mcp"))

    benchmark(_show)