"""Shared test fixtures and helpers for the skills_design tests.

Pack-tree builders (``make_pack``, ``crafted_tree``, ``clean_tree``,
``as_root``) and the design-side CLI driving helper (``run_surface``)
are self-contained here. The traces test tree keeps its own trace
fixtures; the two packages are fully independent (AES702).
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

from shared.src.skills_design.taxonomy_skills_vo import SkillsRoot

from skills_design.src.root_skills_container import default_aggregate
from cli.src.surface_skills_command import cmd_skills


def make_pack(tmp_path: Path) -> Path:
    """A miniature two-category pack with one name-mismatch skill."""
    return crafted_tree(tmp_path)


def crafted_tree(tmp_path: Path) -> Path:
    """A small, deterministic skills root with one known validation issue."""
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
        "---\nname: wrong-name\ndescription: Drafts docs.\n---\n\n# doc-drafts\n",
        encoding="utf-8",
    )

    (root / "notes" / "note-taker").mkdir()
    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: Takes notes.\n---\n\n# note-taker\n",
        encoding="utf-8",
    )

    return root


def clean_tree(tmp_path: Path) -> Path:
    """A one-skill, issue-free tree for exit-0/parity cases."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text(
        "---\ndescription: Cat\n---\n", encoding="utf-8"
    )
    (root / "cat" / "alpha").mkdir()
    (root / "cat" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: Does alpha.\n---\n\n# alpha\n",
        encoding="utf-8",
    )
    return root


def as_root(root: Path) -> SkillsRoot:
    """Type a crafted root for direct capability calls."""
    return SkillsRoot(root)


def run_surface(root: Path, *args: str) -> tuple[int, str, str]:
    """Drive ``cmd_skills`` in-process against a crafted root.

    The surface no longer accepts ``--skills-root``; instead this helper
    builds the aggregate with ``default_root=root`` so every capability
    resolves the crafted tree. Returns ``(exit_code, stdout, stderr)``.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cmd_skills(list(args), default_aggregate(default_root=root))
    return code, stdout.getvalue(), stderr.getvalue()
