"""Guard and parser tests for the skills CLI surface.

Covers the internal-error guards that replaced the old ``assert``
statements (bandit B101) and the default-flag behaviour of the
authoring parser.
"""

from __future__ import annotations

import pytest

from skills_design.src.surface_skills_command import (
    _authoring_parser,
    _render_catalog,
    _render_lint,
)
from skills_design.src.taxonomy_skills_vo import (
    SkillsOp,
    SkillsRequest,
    SkillsResult,
)


def _result() -> SkillsResult:
    """A successful result with every payload field None — trips each guard."""
    return SkillsResult(ok=True, op=SkillsOp.LIST, root=None)


def _request(flags: dict[str, str] | None = None) -> SkillsRequest:
    return SkillsRequest(op=SkillsOp.LIST, flags=flags or {})


_RENDERERS = {
    "lint": _render_lint,
    "catalog": _render_catalog,
}


@pytest.mark.parametrize(
    ("sub", "flags", "payload_attr", "stderr_fragment"),
    [
        (
            "lint",
            {},
            "lint_report",
            "Internal error: no lint report produced",
        ),
    ],
)
def test_guard_returns_internal_error(
    sub: str,
    flags: dict[str, str],
    payload_attr: str,
    stderr_fragment: str,
    capsys,
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


def test_catalog_guard_no_report(capsys) -> None:
    """A None catalog report is an internal error (exit 1), not an assert."""
    result = SkillsResult(ok=True, op=SkillsOp.CATALOG, root=None)
    request = _request({"build": "1", "read": "0"})
    code = _render_catalog(result, request)
    _out, err_ = capsys.readouterr()
    assert code == 1
    assert "Internal error: no catalog report produced" in err_


def test_catalog_read_missing_file_exits_1(capsys) -> None:
    """A read with no catalog text exits 1 with a clear message."""
    result = SkillsResult(ok=True, op=SkillsOp.CATALOG, root=None)
    request = _request({"build": "0", "read": "1"})
    code = _render_catalog(result, request)
    _out, err_ = capsys.readouterr()
    assert code == 1
    assert "CATALOG.md not found" in err_


def test_authoring_parser_defaults() -> None:
    """Default-flag case: ``catalog`` with no explicit flags → both None (surface resolves to build+read)."""
    parser = _authoring_parser()
    ns = parser.parse_args(["catalog"])
    assert ns.command == "catalog"
    assert ns.build is None  # parser default; the surface resolves to True
    assert ns.read is None

    ns = parser.parse_args(["catalog", "--build"])
    assert ns.build is True
    assert ns.read is None

    ns = parser.parse_args(["catalog", "--read"])
    assert ns.build is None
    assert ns.read is True

    ns = parser.parse_args(["catalog", "--build", "--read"])
    assert ns.build is True
    assert ns.read is True


def test_lint_parser_category_flag() -> None:
    parser = _authoring_parser()
    ns = parser.parse_args(["lint", "--category", "notes"])
    assert ns.category == "notes"

    ns = parser.parse_args(["lint"])
    assert ns.category is None


def test_discover_parser_defaults() -> None:
    parser = _authoring_parser()
    ns = parser.parse_args(["discover", "fetch"])
    assert ns.command == "discover"
    assert ns.query == "fetch"
    assert ns.limit == 20
