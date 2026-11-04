"""Benchmarks for skills/skill-authoring/skill-design/modules/skills_design — performance testing."""
from __future__ import annotations


def bench_skills_lister_init(benchmark):
    """BENCH-SKILLS-001: Benchmark SkillsLister initialization."""
    from skills_design.src.capabilities_skills_lister import SkillsLister

    benchmark(SkillsLister)


def bench_skills_list_skills(benchmark):
    """BENCH-SKILLS-002: Benchmark list_skills on the real pack."""
    from skills_design.src.capabilities_skills_lister import SkillsLister

    lister = SkillsLister()

    def _list():
        return list(lister.list_skills())

    benchmark(_list)


def bench_skills_read_skill(benchmark):
    """BENCH-SKILLS-003: Benchmark show_skill (reader) on the real pack."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from skills_design.src.capabilities_skills_reader import SkillsPackReader

    reader = SkillsPackReader()

    def _show():
        return reader.show_skill(SkillQuery("fetch-mcp"))

    benchmark(_show)