"""Shared fixtures/helpers for the skills feature tests (not a test module)."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from modules.cli.src.surface_skills_command import cmd_skills
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.skills.src.root_skills_container import default_aggregate


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


def run_surface(root: Path, *args: str) -> tuple[int, str, str]:
    """Drive ``cmd_skills`` in-process against a crafted root.

    Returns ``(exit_code, stdout, stderr)`` so tests can assert the CLI
    contract without a subprocess.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cmd_skills(
            [*args, "--skills-root", str(root)], default_aggregate()
        )
    return code, stdout.getvalue(), stderr.getvalue()


def run_surface_json(root: Path, *args: str) -> tuple[int, dict]:
    """Drive one ``--json`` invocation and parse the payload."""
    code, out, _err = run_surface(root, *args, "--json")
    return code, json.loads(out)


def as_root(root: Path) -> SkillsRoot:
    """Type a crafted root for direct capability calls."""
    return SkillsRoot(root)
