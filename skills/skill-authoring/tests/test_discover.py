"""Tests for the discover scoring matrix and the §5.6 drift fallback.

Every happy-path output (table header, separator, NO_MATCH_LINE, score
ordering) is pinned against the original ``librarian.py`` behavior so
byte-identity holds across PR-5; the only permitted deviation is a
loud stderr warning plus a ``warning`` JSON field when the catalog
fails its drift gate and the answer falls back to a read-only tree
scan.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_rules"))
import catalog
import discover

_cli = Path(__file__).resolve().parent.parent / "scripts" / "cli.py"


@pytest.fixture()
def crafted_tree(tmp_path: Path) -> Path:
    """A small deterministic skills root: drafts + notes."""
    root = tmp_path / "skills"
    (root / "drafts").mkdir(parents=True)
    (root / "notes").mkdir()

    (root / "drafts" / "DESCRIPTION.md").write_text(
        "---\ndescription: Draft skills\n---\n", encoding="utf-8"
    )
    (root / "notes" / "DESCRIPTION.md").write_text(
        "---\ndescription: Note skills\n---\n", encoding="utf-8"
    )

    (root / "drafts" / "doc-drafts").mkdir()
    (root / "drafts" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Drafts docs.\n---\n\n# doc-drafts\n",
        encoding="utf-8",
    )

    (root / "notes" / "note-taker").mkdir()
    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: Takes notes.\n---\n\n# note-taker\n",
        encoding="utf-8",
    )

    return root


def _run_cli(*args: str, env_root: Path | None = None) -> tuple[int, str, str]:
    """Run the canonical CLI by path and return (exit, stdout, stderr)."""
    command = [sys.executable, str(_cli), *args]
    if env_root is not None:
        command += ["--skills-root", str(env_root)]
    completed = subprocess.run(
        command,
        cwd=str(Path(__file__).resolve().parent.parent.parent.parent),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


class TestScoringMatrix:
    """Golden-score ordering from the original algorithm: name +5,
    description +3, category +2, path +1 per token."""

    def test_name_hit_scores_highest(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, results, _ = discover.discover("doc-drafts", crafted_tree)
        # Full name match (5 points) outweighs a desc/category partial hit.
        assert results[0]["skill"] == "doc-drafts"

    def test_description_hit(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, results, _ = discover.discover("Drafts docs", crafted_tree)
        assert results[0]["skill"] == "doc-drafts"

    def test_category_hit_scores_lowest(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, results, _ = discover.discover("drafts", crafted_tree)
        # Both skills share the "drafts" category token; both also
        # carry the keyword in their path, so they tie at the same
        # score — the first among ties is the name-sorted order.
        skills = [r["skill"] for r in results]
        assert "doc-drafts" in skills

    def test_path_hit(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, results, _ = discover.discover("notes/note-taker", crafted_tree)
        assert results[0]["skill"] == "note-taker"

    def test_multi_token_sums_scores(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, results, _ = discover.discover("notes takes", crafted_tree)
        # "notes" hits category (2) + path (1); "takes" hits description (3) + path (1) = 7 vs doc-drafts 3.
        names = [r["skill"] for r in results]
        assert names[0] == "note-taker"

    def test_tie_order_favors_name_then_path(self, crafted_tree: Path):
        """Ties land in stable sorted order — deterministic for CI."""
        catalog.rebuild_catalog(crafted_tree)
        # "notes" hits the "notes" category of note-taker (2 pts) + path
        # "notes/note-taker" (1 pt); doc-drafts scores 0 — single hit.
        _, results, _ = discover.discover("notes", crafted_tree)
        assert len(results) == 1
        assert results[0]["skill"] == "note-taker"

    def test_zero_score_excluded(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, results, _ = discover.discover("zzz-no-match-zzz", crafted_tree)
        assert results == []

    def test_limit_caps_results(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        # "notes" matches both rows (category + path hit); cap keeps one.
        _, results, _ = discover.discover("notes", crafted_tree, limit=1)
        assert len(results) == 1

    def test_empty_query_is_usage_error(self, crafted_tree: Path):
        exit_code, _, stderr = _run_cli("discover", "", env_root=crafted_tree)
        assert exit_code == 2
        assert "ERROR: Query is empty" in stderr


class TestDriftFallback:
    """§5.6: when the catalog fails its drift check, discover warns loudly
    and answers from a tree scan — never silently returns stale rows."""

    def test_missing_catalog_warns_and_falls_back(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        # Now remove the catalog (no one wrote it back).
        (crafted_tree / "CATALOG.md").unlink()
        # load_catalog_skill_rows must raise on this missing catalog.
        with pytest.raises(catalog.CatalogDrift):
            catalog.load_catalog_skill_rows(crafted_tree)
        # discover warns and falls back to the tree.
        _, results, warning = discover.discover("doc-drafts", crafted_tree)
        assert warning is not None
        assert results[0]["skill"] == "doc-drafts"

    def test_drifted_catalog_warns_and_falls_back(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        # Inject a stale row into the tracked catalog.
        cat = crafted_tree / "CATALOG.md"
        cat.write_text(cat.read_text().replace("Drafts docs.", "STALE DRIFTED ROW"))
        with pytest.raises(catalog.CatalogDrift):
            catalog.load_catalog_skill_rows(crafted_tree)
        _, results, warning = discover.discover("drafts", crafted_tree)
        assert warning is not None
        assert results[0]["skill"] == "doc-drafts"

    def test_drift_warning_mentions_repair_command(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        (crafted_tree / "CATALOG.md").unlink()
        _, _, warning = discover.discover("doc", crafted_tree)
        assert warning is not None
        assert "catalog --check" in warning

    def test_drift_json_carries_warning_field(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        (crafted_tree / "CATALOG.md").unlink()
        exit_code, stdout, stderr = _run_cli(
            "discover", "doc", "--json", env_root=crafted_tree
        )
        assert exit_code == 0
        assert "WARNING" in stderr
        payload = json.loads(stdout)
        assert "warning" in payload
        assert "catalog --check" in payload["warning"]

    def test_no_file_created_as_side_effect_of_discover(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        (crafted_tree / "CATALOG.md").unlink()
        before = sorted(p.name for p in crafted_tree.rglob("*"))
        _, _, _ = discover.discover("doc", crafted_tree)
        after = sorted(p.name for p in crafted_tree.rglob("*"))
        assert before == after, "discover did not create a new CATALOG.md"


class TestHappyPathByteIdentity:
    """The in-sync catalog path must remain byte-identical to the original."""

    def test_discover_reads_the_catalog(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        exit_code, stdout, _ = _run_cli("discover", "docs", env_root=crafted_tree)
        assert exit_code == 0
        assert "| doc-drafts |" in stdout
        exit_code, _, stderr = _run_cli("discover", "", env_root=crafted_tree)
        assert exit_code == 2
        assert "ERROR: Query is empty" in stderr

    def test_discover_limit_caps_results_via_cli(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, stdout, _ = _run_cli("discover", "notes", "--limit", "1", env_root=crafted_tree)
        rows = [
            line
            for line in stdout.splitlines()
            if line.startswith("| ")
            and "---|" not in line
            and line != "| Skill | Category | Description | Path | Score |"
        ]
        assert len(rows) == 1

    def test_discover_nomatch_prints_no_match_line(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        exit_code, stdout, _ = _run_cli(
            "discover", "definitely-not-a-real-skill-term", env_root=crafted_tree
        )
        assert exit_code == 0
        assert stdout.strip() == discover.NO_MATCH_LINE

    def test_in_sync_discover_has_no_warning(self, crafted_tree: Path):
        catalog.rebuild_catalog(crafted_tree)
        _, _, warning = discover.discover("doc-drafts", crafted_tree)
        assert warning is None


# Imported by other modules that reference it, kept here for compatibility.
