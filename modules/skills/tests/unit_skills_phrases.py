"""Unit tests for ``capabilities_skills_phrases.SkillsPhrases``.

Reads session records the tracker would have written into ``run_dir`` (a file
dependency — phrases does NOT import the tracker capability) and mines
repeated exact prompts, prompt stems, and repeated instruction lines.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.shared.src.skills.taxonomy_skills_authoring_vo import PhrasesReport
from modules.shared.src.skills.taxonomy_skills_vo import PhraseRow
from modules.skills.src.capabilities_skills_phrases import SkillsPhrases


def _write_record(run_dir: Path, session_id: str, turns: list[str], repeated_single_turn: bool = False) -> None:
    (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
    rec = {
        "id": session_id,
        "turns": turns,
        "repeated_single_turn": repeated_single_turn,
    }
    (run_dir / "sessions" / f"{session_id}.json").write_text(json.dumps(rec), encoding="utf-8")


def test_phrases_implements_protocol() -> None:
    """SkillsPhrases satisfies the IPhrasesProtocol contract."""
    import modules.shared.src.skills.contract_skills_protocol as cp  # noqa: WPS437

    assert isinstance(SkillsPhrases(), cp.IPhrasesProtocol)


def test_build_phrases_returns_phrases_report() -> None:
    """build_phrases returns a PhrasesReport VO."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        assert isinstance(report, PhrasesReport)
        assert report.exact_prompts == ()
        assert report.repeated_instruction_lines == ()


def test_repeated_exact_prompt_across_sessions() -> None:
    """the same exact prompt in 2+ distinct sessions is mined."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        prompt = "please refactor the login handler"
        for i in range(2):
            _write_record(run_dir, f"s{i}", [prompt])
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        assert report.exact_prompts == (
            PhraseRow(phrase=prompt, sessions=2, occurrences=2, session_ids=("s0", "s1")),
        )


def test_exact_prompt_below_threshold_is_dropped() -> None:
    """a prompt appearing in only 1 session is not reported."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        _write_record(run_dir, "s0", ["one-off prompt"])
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        assert report.exact_prompts == ()


def test_single_turn_automation_excluded() -> None:
    """a single identical prompt repeated 3+ times (repeated_single_turn) is excluded."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        prompt = "automated canary prompt"
        for i in range(3):
            _write_record(run_dir, f"s{i}", [prompt], repeated_single_turn=True)
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        assert report.exact_prompts == ()


def test_prompt_stems_mined() -> None:
    """first-12-words stems repeated across sessions are mined."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        stem = "please refactor the login handler and add tests"
        for i in range(3):
            _write_record(run_dir, f"s{i}", [stem + " extra words here"])
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        stems = [r.phrase for r in report.exact_prompts]
        assert any(stem in s for s in stems)


def test_repeated_instruction_lines() -> None:
    """a repeated instruction line (>=5 words, >=24 chars) across sessions is mined."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        line = "always run the linter before committing"
        for i in range(3):
            _write_record(run_dir, f"s{i}", [line])
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        lines = [r.phrase for r in report.repeated_instruction_lines]
        assert any(line in l for l in lines)


def test_short_turns_ignored() -> None:
    """turns shorter than 12 chars after normalization are skipped."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        for i in range(3):
            _write_record(run_dir, f"s{i}", ["hi"])
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        assert report.exact_prompts == ()
        assert report.repeated_instruction_lines == ()


def test_slash_only_turns_ignored() -> None:
    """slash-command-only turns are skipped."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d)
        for i in range(3):
            _write_record(run_dir, f"s{i}", ["/status"])
        report = SkillsPhrases().build_phrases("irrelevant", str(run_dir))
        assert report.exact_prompts == ()
