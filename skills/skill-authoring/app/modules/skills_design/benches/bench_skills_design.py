"""Benchmarks for skills_design — performance regression detection."""
from __future__ import annotations


def bench_bm25f_ranker_init(benchmark):
    """BENCH-DESIGN-001: Benchmark SkillsBm25fRanker initialization."""
    from skills_design.src.capabilities_skills_discover import SkillsBm25fRanker

    benchmark(SkillsBm25fRanker)


def bench_discover_init(benchmark):
    """BENCH-DESIGN-002: Benchmark SkillsDiscover initialization."""
    from skills_design.src.capabilities_skills_catalog import SkillsCatalog
    from skills_design.src.capabilities_skills_discover import (
        SkillsBm25fRanker,
        SkillsDiscover,
    )

    def _create():
        discover = SkillsDiscover(SkillsCatalog(), SkillsBm25fRanker())
        return discover

    benchmark(_create)


def bench_catalog_init(benchmark):
    """BENCH-DESIGN-003: Benchmark SkillsCatalog initialization."""
    from skills_design.src.capabilities_skills_catalog import SkillsCatalog

    benchmark(SkillsCatalog)
