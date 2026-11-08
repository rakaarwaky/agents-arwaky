"""Performance regression benchmark for the BM25F discovery ranker."""
from __future__ import annotations

import sys
import time
from pathlib import Path

_MOD_ROOT = Path(__file__).resolve().parents[4]
for _ns in (_MOD_ROOT.parent, _MOD_ROOT):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from discovery.capabilities_discovery_finder import (
    SkillsBm25fRanker,
    tokenize,
)
from shared.src.design.taxonomy_skills_vo import _Row


def bench_rank_bm25f():
    """BENCH-DISCOVERY-001: time BM25F ranking over 100 synthetic rows."""
    rows = [
        _Row(
            skill=f"skill-{i:03d}",
            category=f"cat-{i % 10}",
            description=f"Description for skill {i} covering a broad topic {i % 3}.",
            path=f"cat-{i % 10}/skill-{i:03d}",
            when_to_use="",
        )
        for i in range(100)
    ]
    ranker = SkillsBm25fRanker()
    query_tokens = tokenize("broad topic description skill")
    start = time.perf_counter()
    for _ in range(50):
        ranker.rank(rows, query_tokens)
    elapsed = time.perf_counter() - start
    print(f"50 BM25F ranks over 100 rows: {elapsed*1000:.2f} ms total")


if __name__ == "__main__":
    bench_rank_bm25f()
