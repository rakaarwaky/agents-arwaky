"""Performance regression benchmark for the BM25F discovery ranker."""
from __future__ import annotations

import sys
import time
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "discovery" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from shared.src.common.taxonomy_common_vo import _Row
from shared.src.discovery.taxonomy_discovery_vo import (
    SkillsBm25fRanker,
    tokenize,
)


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
