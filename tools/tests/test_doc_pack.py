"""Tests for lib/doc_pack.py — the machine checks behind the add-docs skill.

Each test asserts a rule the skill states in prose, and the clean-project fixture
doubles as proof the checks are satisfiable: a correct document set must produce no
errors at all.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

MASTER_BACKLOG = """# BACKLOG — demo workspace

| Feature | Tier | Spec | Backlog |
|---|---|---|---|
| `modules/alpha` | P0 | [FRD](modules/alpha/FRD.md) | [BACKLOG](modules/alpha/BACKLOG.md) |

State: In Progress
Health: On Track
Last Updated: 2026-09-16

## Current Condition

- Done: full suite green at `a1b2c3d`.
- Next Action: ALPHA-01 closes the scenario gap.

## State definitions

Idea, Refinement, Ready, In Progress, Blocked, In Review, QA, Done, Released, Deferred.

Feature Health: On Track, At Risk, Blocked, Ready for QA, Ready for Release, Released.

## Status policy

Status is verified, not self-reported. A verification names a commit hash.

## Feature roll-up

| Feature | Tier | State | Health | Next Action |
|---|---|---|---|---|
| `modules/alpha` | P0 | In Progress | On Track | ALPHA-01 |

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---|---|---|---|---|---|
| WS-01 | — | Add release notes tooling | P2 | Ready | nothing started | @dev | None | 2026-09-16 |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|---|---|---|
| Tests | Done | `pytest -q` → 12 passed at `a1b2c3d` |

## Deferred

None.

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-09-16 | workspace bootstrapped | @dev |

## Branches in flight

| Branch | Backlog IDs | State |
|---|---|---|
| `feat/alpha` | ALPHA-01 | open |

## Risk register

- **Risk:** scenario gap ships untested. **Mitigation:** ALPHA-01.
"""

FEATURE_BACKLOG = """# Feature Backlog: Alpha

FRD: [FRD.md](FRD.md)
State: In Progress
Health: On Track
Last Updated: 2026-09-16

## Current Condition

- Done: parser tests green at `a1b2c3d`.
- Next Action: ALPHA-01 records the scenario; this file still cannot assert the CLI path.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---|---|---|---|---|---|
| ALPHA-01 | FR-001 | Add run-twice determinism test | P0 | Ready | no test asserts it yet | @dev | None | 2026-09-16 |
| ALPHA-02 | FR-002 | Parse the header | P0 | Done | `pytest tests/test_alpha.py -q` → 4 passed at `a1b2c3d`; skips the CLI path | @dev | None | 2026-09-16 |

## Scenario evidence

| Scenario | Kind | Test file | Test name | Last verified |
|---|---|---|---|---|
| header parses | Automated | `tests/test_alpha.py` | `test_header` | `a1b2c3d` |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|---|---|---|
| Tests | Done | `pytest tests/test_alpha.py -q` → 4 passed at `a1b2c3d` |

## Deferred

None.

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-09-16 | rows opened | @dev |
"""

FRD = """# FRD — Alpha

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature

## System Overview

Alpha reads a file and reports its header.

## Functional Requirements

### FR-001: Determinism

- **Description**: parsing the same input twice yields the same result.
- **Input**: bytes
- **Output**: Header
- **Business Rules**: byte order is fixed.
- **Edge Cases**: empty input.
- **Error Handling**: raises ParseError.

### FR-002: Header parsing

- **Description**: reads the 8-byte header.
- **Input**: bytes
- **Output**: Header
- **Business Rules**: magic must match.
- **Edge Cases**: truncated input.
- **Error Handling**: raises ParseError.

## API Contract

| Operation | Input | Output | Description |
|---|---|---|---|
| `parse(data)` | bytes | Header | reads the header |

## Integration Points

- **Internal**: none.

## Non-functional Requirements (Detailed)

- Performance: 1 MB under 20 ms.

## Test Scenarios

- header parses

## Assumptions & Constraints

- Input is seekable.
"""

PRD = """# PRD — demo

## Problem Statement

Developers cannot tell which document answers which question.

## Goals & Success Metrics

- Goal 1: five documents, zero duplicated claims.

## User Personas

- **Engineer**: needs the spec, not the status.

## Scope

- In scope: document placement.
- Out of scope: rendering.

## Feature Requirements (Prioritized)

### P0 — Must Have

- Placement table with acceptance criteria.

## Non-functional Requirements (High-level)

- Performance: readable in 30 seconds.

## Open Questions / Risks

- None open.
"""

README = """# demo

> One-liner.

## Prerequisites

- Python 3.10+

## Quick Start

`pip install -e . && python -m demo`

## Architecture

Three documents and a checker.

## Project Structure

`modules/alpha/FRD.md`

## Available Scripts

`pytest -q` = Run tests

## Configuration

`DEMO_HOME` names a directory.

## Testing

`pytest -q`

## Contributing

Branch, then PR.

## License

MIT
"""

AGENTS = """# demo

## Precedence

1. Safety.
2. Session approval.
3. PRD/FRD.
4. This file.

## Security

Explicit approval before force push, deletes, publish, or secrets.

## Commands

```bash
pytest -q                                    # matches ci.yml verify
ruff check tools/                            # matches ci.yml verify
```

## Definition of Done

- `pytest -q` passes.

## Related Documents

- [README.md](README.md): how to run it.
"""


def _clean_project(root: Path) -> Path:
    """Write a document set that satisfies every error-level invariant."""
    (root / "modules" / "alpha").mkdir(parents=True)
    (root / "PRD.md").write_text(PRD)
    (root / "README.md").write_text(README)
    (root / "AGENTS.md").write_text(AGENTS)
    (root / "BACKLOG.md").write_text(MASTER_BACKLOG)
    (root / "modules" / "alpha" / "FRD.md").write_text(FRD)
    (root / "modules" / "alpha" / "BACKLOG.md").write_text(FEATURE_BACKLOG)
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "jobs:\n  verify:\n    run:\n      - pytest -q\n      - ruff check tools/\n"
    )
    return root


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return _clean_project(tmp_path)


def _codes(findings) -> set[str]:
    return {finding.code for finding in findings}


class TestTextHelpers:
    def test_blank_fenced_preserves_line_numbers(self):
        from modules.shared.src.doc_pack.capabilities_doc_pack import blank_fenced
        text = "head\n\n```md\nStatus: inside\n```\n\nafter\n"
        blanked = blank_fenced(text)
        assert len(blanked.splitlines()) == len(text.splitlines())
        assert "Status: inside" not in blanked
        assert "after" in blanked

    def test_blank_fenced_handles_four_backtick_fence(self):
        from modules.shared.src.doc_pack.capabilities_doc_pack import blank_fenced
        text = "````markdown\n```bash\ncargo build\n```\n````\nvisible\n"
        assert "cargo build" not in blank_fenced(text)
        assert "visible" in blank_fenced(text)

    def test_parse_tables_reports_line_numbers(self):
        from modules.shared.src.doc_pack.capabilities_doc_pack import parse_tables
        tables = parse_tables("prose\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        assert len(tables) == 1
        assert tables[0].header == ["A", "B"]
        assert tables[0].rows == [(5, ["1", "2"])]

    def test_parse_tables_ignores_fenced_tables(self):
        from modules.shared.src.doc_pack.capabilities_doc_pack import parse_tables
        assert parse_tables("```md\n| A |\n|---|\n| 1 |\n```") == []

    def test_find_section_tolerates_decorated_headings(self):
        from modules.shared.src.doc_pack.capabilities_doc_pack import find_section
        path = tmp_path_of("## 🔧 Commands\n\nrun it\n")
        assert find_section(path, "Commands") is not None


def tmp_path_of(text: str) -> Path:
    import tempfile
    directory = Path(tempfile.mkdtemp())
    path = directory / "X.md"
    path.write_text(text)
    return path


class TestSpecStatusBoundary:
    def test_clean_project_has_no_errors(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        findings = errors_only(audit_docs(project))
        assert findings == [], [f"{f.code}: {f.message}" for f in findings]

    def test_status_line_in_spec_is_flagged(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        spec = project / "modules" / "alpha" / "FRD.md"
        spec.write_text(spec.read_text() + "\n- [x] FR-001 implemented\n")
        assert "status-in-spec" in _codes(errors_only(audit_docs(project)))

    def test_status_inside_a_fenced_template_is_not_flagged(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        spec = project / "modules" / "alpha" / "FRD.md"
        spec.write_text(spec.read_text() + "\n```md\nStatus: Done\n```\n")
        assert "status-in-spec" not in _codes(errors_only(audit_docs(project)))

    def test_spec_without_backlog_partner(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        (project / "modules" / "alpha" / "BACKLOG.md").unlink()
        codes = _codes(errors_only(audit_docs(project)))
        assert "spec-without-backlog" in codes
        assert "backlog-without-spec" not in codes

    def test_orphan_requirement_id_cited_by_backlog(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        spec = project / "modules" / "alpha" / "FRD.md"
        spec.write_text(spec.read_text().replace("### FR-002: Header parsing", "### FR-009: Header parsing"))
        codes = _codes(errors_only(audit_docs(project)))
        assert "orphan-fr-ref" in codes

    def test_duplicate_requirement_id(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        spec = project / "modules" / "alpha" / "FRD.md"
        spec.write_text(spec.read_text().replace("### FR-002: Header parsing", "### FR-001: Header parsing"))
        assert "duplicate-fr-id" in _codes(errors_only(audit_docs(project)))


class TestBacklogHonesty:
    def test_done_row_without_evidence(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        backlog.write_text(backlog.read_text().replace(
            "`pytest tests/test_alpha.py -q` → 4 passed at `a1b2c3d`; skips the CLI path",
            "tests pass",
        ))
        assert "done-without-evidence" in _codes(errors_only(audit_docs(project)))

    def test_done_row_with_counts_but_no_commit(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        backlog.write_text(backlog.read_text().replace("at `a1b2c3d`; skips the CLI path", "at HEAD"))
        assert "done-without-evidence" in _codes(errors_only(audit_docs(project)))

    def test_invented_state_word(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        backlog.write_text(backlog.read_text().replace("| P0 | Ready |", "| P0 | Mostly-done |"))
        assert "unknown-state" in _codes(errors_only(audit_docs(project)))

    def test_state_accepts_a_parenthetical_qualifier(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        backlog.write_text(backlog.read_text().replace("| P0 | Ready |", "| P0 | Ready (needs rebase) |"))
        assert "unknown-state" not in _codes(errors_only(audit_docs(project)))

    def test_wrong_column_count(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        text = backlog.read_text().replace(
            "| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |",
            "| ID | Work Item | Priority | State |",
        ).replace(
            "|---|---|---|---|---|---|---|---|---|", "|---|---|---|---|",
        )
        backlog.write_text(text)
        codes = _codes(errors_only(audit_docs(project)))
        assert "backlog-columns" in codes

    def test_state_definitions_must_live_once(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        backlog.write_text(backlog.read_text() + "\n## State definitions\n\nDone means finished.\n")
        assert "state-vocab-restated" in _codes(errors_only(audit_docs(project)))

    def test_missing_master_backlog(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        (project / "BACKLOG.md").unlink()
        assert "no-master-backlog" in _codes(errors_only(audit_docs(project)))

    def test_scenarios_need_evidence_rows(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        backlog = project / "modules" / "alpha" / "BACKLOG.md"
        backlog.write_text(backlog.read_text().replace("## Scenario evidence", "## Other evidence"))
        assert "scenario-without-evidence" in _codes(errors_only(audit_docs(project)))

    def test_scenario_count_drift_is_a_warning(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, warnings_only
        spec = project / "modules" / "alpha" / "FRD.md"
        spec.write_text(spec.read_text().replace("- header parses", "- header parses\n- empty input raises"))
        assert "scenario-evidence-count" in _codes(warnings_only(audit_docs(project)))


class TestPointersAndHygiene:
    def test_dead_link_in_root_doc(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        readme = project / "README.md"
        readme.write_text(readme.read_text() + "\nSee [the guide](docs/guide.md).\n")
        assert "dead-link" in _codes(errors_only(audit_docs(project)))

    def test_skill_links_outside_its_folder_are_advisory(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        skill = project / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\n---\n\n"
            "Read [the guide](../../docs/guide.md) and [refs](references/missing.md).\n"
        )
        errors = [f for f in errors_only(audit_docs(project)) if "SKILL.md" in f.path]
        assert [f.code for f in errors] == ["dead-link"]
        assert "references/missing.md" in errors[0].message

    def test_reference_file_not_surfaced(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, warnings_only
        refs = project / "skills" / "demo" / "references"
        refs.mkdir(parents=True)
        (project / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\n---\n\nnothing links the file\n"
        )
        (refs / "hidden.md").write_text("# hidden\n")
        assert "unreferenced-file" in _codes(warnings_only(audit_docs(project)))

    def test_dead_link_inside_a_reference_file_is_flagged(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        refs = project / "skills" / "demo" / "references"
        refs.mkdir(parents=True)
        (project / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\n---\n\nsee [templates](references/deep.md).\n"
        )
        (refs / "deep.md").write_text("Back to [invariants](../SKILL.md#nope) and [rules](rules.md).\n")
        hits = [f for f in errors_only(audit_docs(project)) if f.path.startswith(str(refs))]
        assert [f.code for f in hits] == ["dead-link"]
        assert "'rules.md'" in hits[0].message

    def test_link_written_from_the_skill_root_is_advisory(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only, warnings_only
        refs = project / "skills" / "demo" / "references"
        refs.mkdir(parents=True)
        (project / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\n---\n\nsee [deep](references/deep.md).\n"
        )
        (refs / "deep.md").write_text("Also [guide](references/guide.md).\n")
        (refs / "guide.md").write_text("# guide\n")
        findings = audit_docs(project)
        assert "root-relative-link" in _codes(warnings_only(findings))
        assert "dead-link" not in _codes(errors_only(findings))

    def test_reference_links_outside_the_skill_folder_are_not_gated(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        refs = project / "skills" / "demo" / "references"
        refs.mkdir(parents=True)
        (project / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\n---\n\nsee [templates](references/deep.md).\n"
        )
        (refs / "deep.md").write_text("See [the manifest](../../../tools/config/manifest.json).\n")
        assert not [f for f in errors_only(audit_docs(project)) if f.path.startswith(str(refs))]

    def test_absolute_personal_path(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        agents = project / "AGENTS.md"
        agents.write_text(agents.read_text() + "\nRun /home/dev/tool --check to verify.\n")
        assert "absolute-path" in _codes(errors_only(audit_docs(project)))

    def test_env_var_name_is_not_a_secret(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        readme = project / "README.md"
        readme.write_text(readme.read_text() + "\nSet API_KEY=os.environ value first.\n")
        assert "secret-in-docs" not in _codes(errors_only(audit_docs(project)))

    def test_literal_secret_is_flagged(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        readme = project / "README.md"
        readme.write_text(readme.read_text() + '\nSet api_key = "sk-live-9f3a7c21b0"\n')
        assert "secret-in-docs" in _codes(errors_only(audit_docs(project)))


class TestCiCommandDrift:
    def test_command_no_ci_runs_is_flagged(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        agents = project / "AGENTS.md"
        agents.write_text(agents.read_text().replace(
            "ruff check tools/                            # matches ci.yml verify",
            "mypy tools/",
        ))
        assert "ci-command-drift" in _codes(errors_only(audit_docs(project)))

    def test_labelled_advisory_line_is_allowed(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        agents = project / "AGENTS.md"
        agents.write_text(agents.read_text().replace("mypy tools/\n", "").replace(
            "pytest -q                                    # matches ci.yml verify",
            "mypy tools/                                  # advisory, no CI job",
        ))
        assert "ci-command-drift" not in _codes(errors_only(audit_docs(project)))

    def test_no_ci_directory_skips_the_check(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        for path in (project / ".github" / "workflows").glob("*.yml"):
            path.unlink()
        agents = project / "AGENTS.md"
        agents.write_text(agents.read_text().replace("ruff check tools/", "mypy tools/"))
        assert "ci-command-drift" not in _codes(errors_only(audit_docs(project)))

    def test_commands_outside_the_commands_section_are_not_gated(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        agents = project / "AGENTS.md"
        agents.write_text(agents.read_text() + "\n## Notes\n\n`mypy tools/` type-checks locally.\n")
        assert "ci-command-drift" not in _codes(errors_only(audit_docs(project)))

    def test_an_aliased_commands_heading_is_still_gated(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        agents = project / "AGENTS.md"
        text = agents.read_text().replace("## Commands", "## Quick Reference Playbook")
        text = text.replace("ruff check tools/", "mypy tools/")
        agents.write_text(text)
        assert "ci-command-drift" in _codes(errors_only(audit_docs(project)))
        # the section contract accepts the same heading, so Commands stops being reported
        assert "no 'Commands' section" not in "\n".join(
            f.message for f in audit_docs(project) if f.path.endswith("AGENTS.md")
        )


class TestSeverities:
    def test_missing_spec_section_is_an_error(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only
        prd = project / "PRD.md"
        prd.write_text(prd.read_text().replace("## User Personas", "## Audience"))
        assert "prd-section-missing" in _codes(errors_only(audit_docs(project)))

    def test_missing_readme_section_stays_a_warning(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only, warnings_only
        readme = project / "README.md"
        readme.write_text(readme.read_text().replace("## License", "## Legal"))
        assert "readme-section-missing" not in _codes(errors_only(audit_docs(project)))
        assert "readme-section-missing" in _codes(warnings_only(audit_docs(project)))

    def test_length_budget_is_a_warning(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, warnings_only
        # Under the 50-line floor for every doc type -> doc-thin.
        (project / "AGENTS.md").write_text("# demo\n\n## Commands\n\n`pytest -q`\n")
        assert "doc-thin" in _codes(warnings_only(audit_docs(project)))

    def test_prd_has_flat_line_budget(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, warnings_only
        # 300 lines: within [50, 500] -> no doc-length.
        (project / "PRD.md").write_text("\n".join(f"line {i}" for i in range(300)))
        assert "doc-length" not in _codes(warnings_only(audit_docs(project)))
        # 600 lines: over the flat 500 cap -> doc-length.
        (project / "PRD.md").write_text("\n".join(f"line {i}" for i in range(600)))
        assert "doc-length" in _codes(warnings_only(audit_docs(project)))

    def test_frd_has_same_flat_line_budget(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, warnings_only
        frd_codes = lambda: {
            f.code for f in warnings_only(audit_docs(project)) if f.path.endswith("FRD.md")
        }
        # 300 lines: within [50, 500] -> no doc-length.
        (project / "FRD.md").write_text("\n".join(f"line {i}" for i in range(300)))
        assert "doc-length" not in frd_codes()
        # 600 lines: over the flat 500 cap -> doc-length.
        (project / "FRD.md").write_text("\n".join(f"line {i}" for i in range(600)))
        assert "doc-length" in frd_codes()

    def test_as_strict_promotes_warnings(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import as_strict, audit_docs, errors_only, warnings_only
        (project / "AGENTS.md").write_text("# demo\n\n## Commands\n\n`pytest -q`\n")
        findings = audit_docs(project)
        assert len(errors_only(as_strict(findings))) > len(errors_only(findings))
        assert warnings_only(as_strict(findings)) == []

    def test_master_only_section_missing_is_a_warning(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only, warnings_only
        master = project / "BACKLOG.md"
        master.write_text(master.read_text().replace("## Feature roll-up", "## Roll-up of features"))
        assert "master-section-missing" in _codes(warnings_only(audit_docs(project)))
        assert "master-section-missing" not in _codes(errors_only(audit_docs(project)))

    def test_submodule_trees_are_skipped_by_default(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only, iter_doc_files
        (project / "vendor" / "upstream").mkdir(parents=True)
        (project / "vendor" / "upstream" / "FRD.md").write_text("# FRD — junk\n")
        assert not any("vendor" in path.parts for path in iter_doc_files(project))
        assert errors_only(audit_docs(project)) == []
        assert iter_doc_files(project, include_subtrees=True) != iter_doc_files(project)

    def test_tool_cache_dirs_are_skipped(self, project):
        from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, iter_doc_files
        cache = project / ".pytest_cache"
        cache.mkdir()
        (cache / "README.md").write_text("# pytest cache\n")
        assert not any(".pytest_cache" in path.parts for path in iter_doc_files(project))
        assert not any(".pytest_cache" in finding.path for finding in audit_docs(project))


class TestGuideMatchesTheGate:
    """The reference tables are the contract; the gate must enforce exactly that set."""

    REFS = Path(__file__).resolve().parents[2] / "skills" / "documentation" / "add-docs" / "references"

    @staticmethod
    def _contract_rows(text: str) -> list[tuple[str, str]]:
        from modules.shared.src.doc_pack.capabilities_doc_pack import parse_tables

        for table in parse_tables(text):
            header = " ".join(table.header).lower()
            if "section" in header and ("belongs here" in header or "belong here" in header):
                req = next((i for i, cell in enumerate(table.header) if "req" in cell.lower()), None)
                out = []
                for _, cells in table.rows:
                    name = cells[0]
                    flag = cells[req].lower() if req is not None else "yes"
                    out.append((name, "yes" if flag.startswith(("✓", "yes")) else "no"))
                return out
        raise AssertionError("no section-contract table found")

    @staticmethod
    def _same(a: str, b: str) -> bool:
        from modules.shared.src.doc_pack.capabilities_doc_pack import _norm

        x, y = _norm(a), _norm(b)
        return x == y or x in y or y in x

    @pytest.mark.parametrize("doc,ref", [
        ("PRD.md", "prd.md"), ("FRD.md", "frd.md"),
        ("README.md", "readme.md"), ("AGENTS.md", "agents-md.md"),
    ])
    def test_required_rows_equal_the_gate(self, doc, ref):
        from modules.shared.src.doc_pack.capabilities_doc_pack import REQUIRED_SECTIONS

        rows = self._contract_rows((self.REFS / ref).read_text(encoding="utf-8"))
        gated = [name for name, flag in rows if flag == "yes"]
        required = list(REQUIRED_SECTIONS[doc])
        assert len(gated) == len(required)
        for name in gated:
            assert any(self._same(name, req) for req in required), f"{ref}: {name!r} is gated by the guide only"
        for req in required:
            assert any(self._same(name, req) for name in gated), f"{doc}: {req!r} is gated by the checker only"

    def test_backlog_reference_carries_every_gated_section(self):
        from modules.shared.src.doc_pack.capabilities_doc_pack import MASTER_ONLY_SECTIONS, REQUIRED_SECTIONS

        text = (self.REFS / "backlog.md").read_text(encoding="utf-8")
        headings = [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("## ")]
        for name in REQUIRED_SECTIONS["BACKLOG.md"] + MASTER_ONLY_SECTIONS:
            assert any(name.lower() in h.lower() for h in headings), f"backlog.md template lacks {name!r}"
