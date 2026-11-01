"""Guard and parser tests for the skills CLI surface.

Covers the nine ``if X is None`` error guards that replaced the old
``assert`` statements (bandit B101), the equals-form ``--skills-root=``
branch of ``_split_root``, and the default-flag behaviour of the
authoring parser.
"""

from __future__ import annotations

import pytest

from modules.cli.src.surface_skills_command import (
    _authoring_parser,
    _render_archive,
    _render_catalog,
    _render_merge_plan,
    _render_move,
    _render_new_category,
    _render_repair,
    _render_validate,
    _render_weed,
    _split_root,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsOp,
    SkillsRequest,
    SkillsResult,
)


def _result() -> SkillsResult:
    """A successful result with every payload field None — trips each guard."""
    return SkillsResult(ok=True, op=SkillsOp.LIST, root=None)


def _request(flags: dict[str, str] | None = None, json: bool = False) -> SkillsRequest:
    return SkillsRequest(op=SkillsOp.LIST, flags=flags or {}, json=json)


_RENDERERS = {
    "validate": _render_validate,
    "catalog_check": _render_catalog,
    "catalog": _render_catalog,
    "weed": _render_weed,
    "repair": _render_repair,
    "move": _render_move,
    "archive": _render_archive,
    "new_category": _render_new_category,
    "merge_plan": _render_merge_plan,
}


@pytest.mark.parametrize(
    ("sub", "flags", "payload_attr", "stderr_fragment"),
    [
        ("validate", {}, "report", "Internal error: no validation report produced"),
        (
            "catalog_check",
            {"check": "1"},
            "check",
            "Internal error: no catalog check result produced",
        ),
        (
            "catalog",
            {"check": "0"},
            "catalog",
            "Internal error: no catalog report produced",
        ),
        ("weed", {}, "plan", "Internal error: no weed plan produced"),
        ("repair", {}, "plan", "Internal error: no repair plan produced"),
        ("move", {}, "plan", "Internal error: no move plan produced"),
        ("archive", {}, "plan", "Internal error: no archive plan produced"),
        (
            "new_category",
            {},
            "new_category",
            "Internal error: no new-category plan produced",
        ),
        ("merge_plan", {}, "merge", "Internal error: no merge plan produced"),
    ],
)
def test_guard_returns_internal_error(
    sub: str, flags: dict[str, str], payload_attr: str, stderr_fragment: str, capsys
) -> None:
    """Every renderer guards a None payload with an internal error, not an assert.

    The guard must (a) return exit code 1 and (b) emit the exact static
    ``err()`` message on stderr — no variable names leak like the old
    assert tracebacks did.
    """
    result = _result()
    assert getattr(result, payload_attr) is None
    request = _request(flags)

    code = _RENDERERS[sub](result, request)
    _out, err_ = capsys.readouterr()
    assert code == 1
    assert stderr_fragment in err_


def test_split_root_equals_form() -> None:
    """``--skills-root=VALUE`` (equals form) is parsed without consuming a second arg."""
    root, rest = _split_root(["--skills-root=custom", "list", "--limit", "5"])
    assert root is not None
    # resolve_skills_root() returns an absolute path; pin the basename
    assert root.name == "custom"
    assert rest == ["list", "--limit", "5"]


def test_split_root_space_form_unchanged() -> None:
    """The space form still consumes the value token."""
    root, rest = _split_root(["list", "--skills-root", "custom"])
    assert root is not None
    assert root.name == "custom"
    assert rest == ["list"]


def test_authoring_parser_defaults() -> None:
    """Default-flag case: ``discover`` with no explicit ``--limit``/``--json``/``--skills-root``."""
    parser = _authoring_parser()
    ns = parser.parse_args(["discover", "fetch"])
    assert ns.command == "discover"
    assert ns.query == "fetch"
    # flag defaults pinned by the parser, not inferred from usage
    assert ns.limit == 20
    assert ns.json is False
    assert ns.skills_root is None
