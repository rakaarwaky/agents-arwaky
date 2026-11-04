"""Shared test fixtures and helpers for the skills_traces tests.

Trace-specific helpers (``make_grok_home``, ``run_trace_surface``) are
defined here. This module is self-contained (AES702): trace helpers live here; no
cross-import from the sibling skills-design package.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from cli.src.surface_skills_traces_command import cmd_traces
from root_skills_container import default_aggregate

__all__ = [
    "make_grok_home",
    "run_trace_surface",
]

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
        "\n".join(
            json.dumps(turn)
            for turn in (
                _TRAFIX_TURN,
                {"type": "assistant", "content": "turn two"},
                {"type": "user", "content": "<user_query>turn three</user_query>"},
                {"type": "user", "content": "<user_query>turn four</user_query>"},
            )
        )
        + "\n",
        encoding="utf-8",
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
    if grok_home:
        action = args[0] if args else ""
        rest = args[1:]
        if action == "state" and rest:
            # state uses subparsers: state <sub_action> [flags]
            sub_action = rest[0]
            rest_flags = rest[1:]
            args = ["state", sub_action, "--grok-home", str(grok_home), *rest_flags]
        elif action:
            args = [action, "--grok-home", str(grok_home), *rest]
        else:
            args = ["--grok-home", str(grok_home)]
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cmd_traces(list(args), default_aggregate())
    return code, stdout.getvalue(), stderr.getvalue()
