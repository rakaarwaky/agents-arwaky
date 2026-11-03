"""Shared fixtures/helpers for the skills feature tests (not a test module)."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from modules.cli.src.surface_skills_command import cmd_skills
from modules.cli.src.surface_skills_traces_command import cmd_traces
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.skills.src.root_skills_container import default_aggregate

_TRAFIX_SESSION = {
    "id": "sess-001",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-02T00:00:00+00:00",
    "session_kind": "interactive",
    "head_branch": "main",
    "generated_title": "test session",
}

_TRAFIX_TURN = {
    "type": "user",
    "content": "<user_query>turn one two three</user_query>",
    "synthetic_reason": None,
}


def make_grok_home(
    tmp_path: Path, *, cwd: str = "proj", with_skills: bool = False
) -> Path:
    """A minimal GROK_HOME fixture: one interactive session, plus optionally
    one user skill and a slash-mru entry (for usage/phrases coverage)."""
    grok_home = tmp_path / "grok"
    sessions = grok_home / "sessions" / "user" / "sess-001"
    sessions.mkdir(parents=True)
    project = str(tmp_path / cwd)
    (sessions / "summary.json").write_text(
        json.dumps(
            {
                **_TRAFIX_SESSION,
                "info": {"cwd": project, "git_root_dir": project},
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    (sessions / "chat_history.jsonl").write_text(
        json.dumps(_TRAFIX_TURN) + "\n", encoding="utf-8"
    )
    if with_skills:
        skill_dir = grok_home / "skills" / "cat" / "lint"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: lint\ndescription: lints\n---\n", encoding="utf-8"
        )
        (grok_home / "slash-mru.json").write_text(
            json.dumps({"by_command": {"lint": {}}}), encoding="utf-8"
        )
    (grok_home / "learn").mkdir(parents=True)
    return grok_home


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

    The surface no longer accepts ``--skills-root``; instead this helper
    builds the aggregate with ``default_root=root`` so every capability
    resolves the crafted tree. Returns ``(exit_code, stdout, stderr)``.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cmd_skills(list(args), default_aggregate(default_root=root))
    return code, stdout.getvalue(), stderr.getvalue()


def run_trace_surface(grok_home: Path, *args: str) -> tuple[int, str, str]:
    """Drive a trace verb in-process against a fixture GROK_HOME.

    The traces capability is no longer routed from the main CLI surface
    (``cmd_skills``); this helper drives the extracted traces surface
    module (``cmd_traces``) directly, stripping the leading ``"traces"``
    token the old CLI surface consumed. Returns ``(exit_code, stdout,
    stderr)``.
    """
    if args and args[0] == "traces":
        args = args[1:]
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cmd_traces(list(args), default_aggregate())
    return code, stdout.getvalue(), stderr.getvalue()


def as_root(root: Path) -> SkillsRoot:
    """Type a crafted root for direct capability calls."""
    return SkillsRoot(root)
