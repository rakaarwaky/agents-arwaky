"""Machine checks for the document invariants the ``add-docs`` skill states in prose.
Moved as-is from tools/lib/doc_pack.py; shared vocabularies now live in
modules.shared.src.taxonomy_common_constant.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    BACKLOG_COLUMNS,
    DOC_NAMES,
    ERROR,
    EVIDENCED_STATES,
    HEALTH_VOCAB,
    SPEC_DOCS,
    STATE_VOCAB,
    WARN,
)
from modules.shared.src.taxonomy_common_vo import DocFinding, Table
from modules.shared.src.taxonomy_common_vo import Section as _Section
from modules.shared.src.utility_paths_resolver import repo_root

# (ERROR/WARN imported from taxonomy_common_constant)

#: Build/vendored trees that never carry this project's documents.
_SKIP_PARTS = {
    ".git", ".hg", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv",
    "__pycache__", "build", "dist", "node_modules", "site-packages", "target", "venv",
    ".worktree", ".worktrees",
}
#: Submodule trees are upstream-owned, so a finding there is noise nobody may act on.
#: ``include_subtrees=True`` opts back in.
_OWNERSHIP_SKIP_DIRS = {"vendor", "internal"}


#: Findings that stay gating even on files the pack merely hosts (upstream ``SKILL.md``
#: copies): a broken pointer is a broken pointer whoever wrote the file.
_ALWAYS_GATING = {"dead-link"}

#: Sections that may exist only in the root master, per references/HOW-TO-MAKE-ROADMAP.md.
MASTER_ONLY_SECTIONS = (
    "State definitions", "Status policy", "Feature roll-up",
    "Branches in flight", "Risk register",
)

#: Headings that hold the runnable commands. Both the section contract and the CI-drift
#: check use this list, so a repo may head that section either way and still be gated.
_COMMANDS_HEADINGS = ("Commands", "Command Reference", "Available Commands",
                      "Available Scripts", "Quick Reference Playbook")

#: Section contract, mirroring references/HOW-TO-MAKE-{prd,roadmap,frd,readme,backlog,agents}.md.
REQUIRED_SECTIONS = {
    "PRD.md": ("Problem Statement", "Goals", "User Personas", "Scope",
               "Feature Requirements", "Non-functional", "Open Questions"),
    "ROADMAP.md": ("Current Condition", "State Definitions", "Status Policy",
                   "Feature Roll-up",
                   "Branches in Flight", "Risk Register"),
    "FRD.md": ("Reference", "System Overview", "Functional Requirements",
               "API Contract", "Integration Points", "Non-functional",
               "Test Scenarios", "Assumptions", "Glossary"),
    "README.md": ("Prerequisites", "Quick Start", "Architecture", "Project Structure",
                  "Available Scripts", "Configuration", "Testing", "Contributing", "License"),
    "AGENTS.md": ("Precedence", "Security", "Commands", "Definition of Done",
                  "Related Documents"),
    "BACKLOG.md": ("Current Condition", "Backlog", "Scenario Evidence", "Blockers",
                   "Dependencies", "Release Readiness", "Deferred", "Change Log"),
}
#: Canonical contract section -> heading fragments that satisfy it. Repos head the same
#: obligation differently, so the check is on the information being present, not on one
#: spelling. The templates in the add-docs references still show the canonical name first.
_SECTION_ALIASES = {
    "Available Scripts": ("Available Scripts", "Available Commands", "Commands",
                          "Developer Workflows", "Orchestrator CLI"),
    "Branches in Flight": ("Branches in Flight", "Branches", "In Flight"),
    "Commands": _COMMANDS_HEADINGS,
    "Configuration": ("Configuration", "Config", "Environment"),
    "Current Condition": ("Current Condition", "Current Status", "Condition"),
    "Definition of Done": ("Definition of Done", "Quality Gates", "Done Criteria",
                           "Verification"),
    "Feature Roll-up": ("Feature Roll-up", "Feature Rollup", "Roll-up", "Rollup"),
    "Glossary": ("Glossary", "Terms", "Definitions"),
    "Open Questions": ("Open Questions", "Open Questions / Risks", "Risks",
                       "Open Questions and Risks"),
    "Precedence": ("Precedence", "Priority Order", "When Documents Disagree"),
    "Project Structure": ("Project Structure", "Repository Structure", "Repo Layout",
                          "Directory Layout", "Architecture Map"),
    "Quick Start": ("Quick Start", "Quickstart", "Getting Started", "Installation"),
    "Related Documents": ("Related Documents", "Reference Paths", "See Also"),
    "Risk Register": ("Risk Register", "Risks"),
    "Scenario Evidence": ("Scenario Evidence", "Evidence"),
    "Security": ("Security", "Guardrails", "Safety"),
    "State Definitions": ("State Definitions", "States", "State Vocabulary"),
    "Status Policy": ("Status Policy", "Verification Policy"),
    "Testing": ("Testing", "Test Suite", "Tests"),
    "Contributing": ("Contributing", "How to Contribute", "Contributor Guide"),
}
#: Sections a harness may legitimately not need, whatever the contract table says.
_SOFT_SECTIONS = {"README.md", "AGENTS.md"}

_COMMITS = re.compile(r"\b[0-9a-f]{7,40}\b")
_CODE_SPAN = re.compile(r"`[^`\n]+`")
_FR_ID = re.compile(r"\bFR-(?:[A-Za-z0-9]+-)?\d+\b")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.MULTILINE)
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")

#: HOW-TO-MAKE-FRD Rule 1: ``FR-<FEATURENAME>-<number>`` (name segment required).
_FR_HEADING = re.compile(r"^#{2,5}\s+(FR-([A-Za-z0-9]+)-(\d+)):\s+(\S.*)$")
#: Loose heading that still looks like an FR but violates Rule 1 / shape.
_FR_HEADING_LOOSE = re.compile(r"^#{2,5}\s+(FR-\S+)")
#: Rule 2 — every requirement states these six fields.
_FR_FIELDS = ("Description", "Input", "Output", "Business Rules", "Edge Cases", "Error Handling")
#: Rule 3 — API Contract column order is exact.
_API_COLUMNS = ("Method", "Input", "Output", "Error", "Event", "Description")
#: Template — Integration Points / Non-functional column contracts.
_INTEGRATION_COLUMNS = ("System", "Direction", "Purpose", "Failure mode")
_NFR_COLUMNS = ("Metric", "Target", "Measurement method")
#: Template section order (HOW-TO-MAKE-FRD § Template).
_FRD_SECTION_ORDER = (
    "Reference", "System Overview", "Functional Requirements",
    "API Contract", "Integration Points", "Non-functional",
    "Test Scenarios", "Assumptions", "Glossary",
)

#: Claims that belong in BACKLOG.md / ROADMAP.md, never in a spec.
_STATUS_LEAKS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*[-*]\s*\[[ xX]\]"), "a checkbox task item"),
    (re.compile(r"^\s*\**\s*status\s*\**\s*:", re.IGNORECASE), "a Status: field"),
    (re.compile(r"\b(?:implemented|unimplemented|partially implemented)\b", re.IGNORECASE),
     "implementation state"),
    (re.compile(r"\b(?:shipped|released|deployed) in v\w*\b", re.IGNORECASE), "release state"),
    (re.compile(r"^\s*(?:✅|❌|🟢|🔴|✔️|✖)"), "a status marker"),
    (re.compile(r"\b\d+\s*%\s*(?:complete|done)", re.IGNORECASE), "a progress percentage"),
)

#: HOW-TO-MAKE-FRD Rule 9 — stateless specs never name source files.
_SOURCE_EXT = re.compile(
    r"(?<![\w.-])(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_.<>{}*-]+\.(?:py|rs|ts|tsx)(?![\w-])"
)

#: Gate binaries a document is allowed to print, used for CI-command drift.
_GATE_COMMANDS = (
    "pytest", "ruff", "mypy", "bandit", "black", "cargo", "clippy", "npm", "pnpm",
    "yarn", "npx", "tsc", "shellcheck", "jq", "make",
)
_ADVISORY = re.compile(r"advisory|not gated|no ci|local only|local-only", re.IGNORECASE)

_ABSOLUTE_PATH = re.compile(
    r"(?<![\w.])/(?:home|users|mnt|volumes|root)/[a-z0-9_.-]+|\bc:\\users",
    re.IGNORECASE,
)
_SECRET_KEY = re.compile(
    r"\b(?:api[_-]?key|secret|token|password|passwd|credential)s?\b\s*[:=]\s*",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"""(?:(?P<q>["'])(?P<quoted>[^"'\s]{8,})(?P=q)|(?P<bare>[A-Za-z0-9_\-./+]{8,}))""",
    re.VERBOSE,
)
#: Values that name a lookup or an obvious stand-in rather than a real secret. Kept
#: case-sensitive so an all-caps env var name is exempt but `hunter2pass` is not.
_PLACEHOLDER_VALUE = re.compile(
    r"^(?:[A-Z][A-Z0-9_]{3,}|<.*>|\$\{?.*|os\.env.*|[Ee]xample.*|[Yy]our.*"
    r"|[Pp]laceholder.*|[Cc]hangeme.*|[Xx]+.*|[Dd]ummy.*|[Ss]ample.*)$"
)


# Dataclasses DocFinding/_Section/Table now live in the shared taxonomy layer
# (taxonomy_common_vo.py); imported at the top of this module.


# --- text helpers -------------------------------------------------------------
def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _norm(text: str) -> str:
    """Lowercase and strip punctuation/emoji, so heading matching tolerates decoration."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def blank_fenced(text: str) -> str:
    """Return *text* with fenced code bodies replaced by blank lines.

    Line count and numbering are preserved, so a caller can still report a line.

    Args:
        text: Markdown source.

    Returns:
        The same number of lines, with anything inside a ``` or ~~~ fence emptied.
    """
    out: list[str] = []
    fence = ""
    for line in text.splitlines():
        stripped = line.strip()
        if not fence:
            match = _FENCE.match(line)
            if match:
                fence = match.group(1)
                out.append("")
                continue
            out.append(line)
            continue
        if stripped.startswith(fence[0] * len(fence)) and set(stripped) <= {fence[0]}:
            fence = ""
        out.append("")
    return "\n".join(out)


def _lines(text: str) -> list[tuple[int, str]]:
    """1-based ``(line, content)`` pairs."""
    return list(enumerate(text.splitlines(), start=1))


def sections(path: Path) -> list[_Section]:
    """Every heading in *path* with its body and starting line."""
    text = _read(path)
    matches = list(_HEADING.finditer(text))
    found: list[_Section] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        found.append(_Section(
            level=len(match.group(1)),
            title=match.group(2),
            body=text[match.end():end],
            line=text.count("\n", 0, match.start()) + 1,
        ))
    return found


def find_section(path: Path, title: str) -> _Section | None:
    """The first section whose heading contains *title*, ignoring decoration."""
    wanted = _norm(title)
    for section in sections(path):
        if wanted and wanted in _norm(section.title):
            return section
    return None


def _missing_sections(text: str, doc: str) -> list[str]:
    """Required headings of *doc* that the text does not carry."""
    headings = _norm(" ".join(m.group(2) for m in _HEADING.finditer(text)))
    missing: list[str] = []
    for title in REQUIRED_SECTIONS.get(doc, ()):
        candidates = _SECTION_ALIASES.get(title, (title,))
        if not any(_norm(cand) in headings for cand in candidates):
            missing.append(title)
    return missing


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_tables(text: str) -> list[Table]:
    """Markdown tables in *text*; separator rows and tables inside fences are skipped.

    Args:
        text: Markdown source.

    Returns:
        :class:`Table` values in document order, with 1-based line numbers.
    """
    lines = blank_fenced(text).splitlines()
    tables: list[Table] = []
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|") or not lines[index + 1].lstrip().startswith("|"):
            index += 1
            continue
        if not re.fullmatch(r"\|?[\s:|-]+\|?", lines[index + 1].strip()):
            index += 1
            continue
        header = _cells(lines[index])
        rows: list[tuple[int, list[str]]] = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            rows.append((cursor + 1, _cells(lines[cursor])))
            cursor += 1
        tables.append(Table(header, rows, index + 1))
        index = cursor
    return tables


def md_links(text: str) -> list[tuple[str, int]]:
    """``(target, line)`` for every markdown link outside a fenced block."""
    out: list[tuple[str, int]] = []
    for number, line in _lines(blank_fenced(text)):
        for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            out.append((match.group(1), number))
    return out


def _is_resolvable(target: str) -> bool:
    """Whether *target* is a real relative path rather than an anchor, URL or placeholder."""
    if target.startswith(("#", "/", "http://", "https://", "mailto:", "tel:")):
        return False
    return not any(bad in target for bad in ("<", ">", "*", "...", "$", "{", "%"))


# --- placement and status invariants -----------------------------------------
def root_master(root: Path) -> Path | None:
    """The root file that owns shared policy.

    ``ROADMAP.md`` is the standard (references/HOW-TO-MAKE-ROADMAP.md); a legacy root
    ``BACKLOG.md`` is accepted during migration and treated as the same master.

    Anchoring is workspace-wide: when *root* sits inside the repository (a path-scoped
    audit such as ``modules/check``), the master resolves from the repo root so a
    feature's own ``BACKLOG.md`` is never mistaken for the workspace master. An audit
    outside the repository keeps anchoring at its own *root*.
    """
    anchor = root
    repo = Path(repo_root())
    try:
        root.resolve().relative_to(repo.resolve())
    except ValueError:
        pass
    else:
        anchor = repo
    for name in ("ROADMAP.md", "BACKLOG.md"):
        candidate = anchor / name
        if candidate.is_file():
            return candidate
    return None


def check_spec_status_leak(path: Path) -> list[DocFinding]:
    """Rule *Spec and status never share a file*; specs also stay stateless."""
    findings: list[DocFinding] = []
    for number, line in _lines(blank_fenced(_read(path))):
        for pattern, label in _STATUS_LEAKS:
            if pattern.search(line):
                findings.append(DocFinding(
                    "status-in-spec",
                    f"line {number} carries {label} ({line.strip()[:60]!r}) — specs promise, "
                    "backlogs report; move the claim to BACKLOG.md",
                    f"{path}:{number}",
                ))
                break
        if path.name in ("FRD.md", "PRD.md"):
            match = _SOURCE_EXT.search(line)
            if match:
                findings.append(DocFinding(
                    "spec-source-path",
                    f"line {number} names source file {match.group(0)!r} — specs are "
                    "stateless: refer to roles and behaviour, never .py/.rs/.ts files "
                    "(HOW-TO Rule 9)",
                    f"{path}:{number}",
                ))
    return findings


def _under_shared(path: Path) -> bool:
    """True when *path* lives under a directory named ``shared`` (kernel, not a feature)."""
    return "shared" in path.parts[:-1]


def check_spec_pairing(root: Path) -> list[DocFinding]:
    """Rule *every spec has a partner backlog, and one root master owns the definitions*.

    Also forbids feature docs under a ``shared/`` kernel folder
    (``feature-doc-in-shared``): shared is not a feature, so it has no pair
    (HOW-TO-MAKE-FRD § Scope).
    """
    findings: list[DocFinding] = []
    docs = iter_doc_files(root)
    master = root_master(root)
    for path in docs:
        if path.name in ("FRD.md", "BACKLOG.md") and _under_shared(path):
            findings.append(DocFinding(
                "feature-doc-in-shared",
                f"{path.name} under shared/ — kernel folders are not features and "
                "must not carry an FRD/BACKLOG pair (HOW-TO-MAKE-FRD § Scope)",
                str(path),
            ))
    specs = [
        path for path in docs
        if path.name in SPEC_DOCS and not (_under_shared(path) and path.name == "FRD.md")
    ]
    if specs and master is None:
        findings.append(DocFinding(
            "no-master-backlog",
            f"{len(specs)} spec file(s) but no root ROADMAP.md (or legacy root "
            "BACKLOG.md) to own the State/Health vocabulary and status policy",
            str(root / "ROADMAP.md"),
        ))
    for spec in specs:
        if _under_shared(spec):
            continue
        partner = spec.parent / "BACKLOG.md"
        if not partner.is_file():
            findings.append(DocFinding(
                "spec-without-backlog",
                f"{spec.name} has no BACKLOG.md beside it, so its status has nowhere to go",
                str(spec.parent),
            ))
        elif spec.name == "FRD.md" and "BACKLOG" not in blank_fenced(_read(spec)).upper():
            findings.append(DocFinding(
                "unlinked-spec",
                "FRD.md never links BACKLOG.md; the Reference section keeps spec and status "
                "from being read as one source",
                str(spec),
                severity=WARN,
            ))
    for backlog in (p for p in docs if p.name == "BACKLOG.md" and p != master):
        if _under_shared(backlog):
            continue
        if not any((backlog.parent / name).is_file() for name in SPEC_DOCS):
            findings.append(DocFinding(
                "backlog-without-spec",
                "feature BACKLOG.md has no spec beside it; a row needs a requirement to point at",
                str(backlog),
            ))
    return findings


def check_state_vocabulary(root: Path) -> list[DocFinding]:
    """Rule *definitions live once, in the root master file*."""
    findings: list[DocFinding] = []
    master = root_master(root)
    if master is not None:
        # The vocabulary may sit in any section (Health usually shares State definitions),
        # so the invariant is that each term is defined somewhere in the master file.
        prose = _norm(blank_fenced(_read(master)))
        for term in (*STATE_VOCAB, *HEALTH_VOCAB):
            if _norm(term) not in prose:
                findings.append(DocFinding(
                    "undefined-state-vocab",
                    f"root master never defines {term!r}; feature files cite this "
                    "vocabulary and cannot define it themselves",
                    str(master),
                    severity=WARN,
                ))
        for title in MASTER_ONLY_SECTIONS:
            if find_section(master, title) is None:
                findings.append(DocFinding(
                    "master-section-missing",
                    f"root master has no {title!r} section; this is the one place that "
                    "answers it workspace-wide, so no feature file may hold it instead",
                    str(master),
                    severity=WARN,
                ))
    for backlog in iter_doc_files(root):
        if backlog.name != "BACKLOG.md" or backlog == master:
            continue
        headings = _norm(" ".join(
            m.group(2) for m in _HEADING.finditer(blank_fenced(_read(backlog)))
        ))
        restated = [t for t in MASTER_ONLY_SECTIONS if _norm(t) in headings]
        if restated:
            findings.append(DocFinding(
                "state-vocab-restated",
                f"feature backlog carries its own {' and '.join(restated)} section; those live "
                "once, in the root master (ROADMAP.md)",
                str(backlog),
            ))
    return findings


def _state_is_known(state: str) -> bool:
    """Whether *state* is a documented value, allowing a parenthetical qualifier."""
    head = _norm(re.split(r"[(—(]", state)[0])
    return any(head == _norm(term) for term in STATE_VOCAB)


def check_backlog_rows(backlog: Path) -> list[DocFinding]:
    """Rules *the Backlog table keeps nine columns* and *every claim is re-runnable*."""
    findings: list[DocFinding] = []
    for table in parse_tables(_read(backlog)):
        lowered = [cell.lower() for cell in table.header]
        if "work item" not in lowered:
            continue
        if len(table.header) != len(BACKLOG_COLUMNS):
            findings.append(DocFinding(
                "backlog-columns",
                f"Backlog table at line {table.line} has {len(table.header)} columns, "
                f"expected {len(BACKLOG_COLUMNS)} ({' · '.join(BACKLOG_COLUMNS)})",
                f"{backlog}:{table.line}",
            ))
        state_at = lowered.index("state")
        condition_at = lowered.index("actual condition") if "actual condition" in lowered else None
        for line, row in table.rows:
            if len(row) != len(table.header):
                findings.append(DocFinding(
                    "backlog-row-width",
                    f"row has {len(row)} cells but the header has {len(table.header)}",
                    f"{backlog}:{line}",
                ))
                continue
            state = row[state_at].strip()
            if state and not _state_is_known(state):
                findings.append(DocFinding(
                    "unknown-state",
                    f"row state {state!r} is not in the master vocabulary; use one of "
                    f"{', '.join(STATE_VOCAB)} or add the term to ROADMAP.md",
                    f"{backlog}:{line}",
                ))
            if (state.title() in EVIDENCED_STATES and condition_at is not None
                    and not _row_has_evidence(row[condition_at])):
                findings.append(DocFinding(
                    "done-without-evidence",
                    f"row {row[0]!r} is {state!r} with no re-run command and commit hash in "
                    "Actual Condition; verified means someone ran it",
                    f"{backlog}:{line}",
                ))
    return findings


def _row_has_evidence(condition: str) -> bool:
    """Whether an ``Actual Condition`` cell cites both a command and a commit."""
    return bool(_CODE_SPAN.search(condition) and _COMMITS.search(condition))


def check_fr_ids(spec: Path, backlog: Path | None) -> list[DocFinding]:
    """Rules *requirement IDs are unique* and *a backlog may cite only what is specified*."""
    findings: list[DocFinding] = []
    text = blank_fenced(_read(spec))
    defined: dict[str, int] = {}
    for number, line in _lines(text):
        match = re.match(r"^#{2,5}\s+(FR-(?:[A-Za-z0-9]+-)?\d+)\b", line)
        if match:
            identifier = match.group(1)
            if identifier in defined:
                findings.append(DocFinding(
                    "duplicate-fr-id",
                    f"{identifier} is defined again (first at line {defined[identifier]}); "
                    "IDs are stable — retire one, never reuse or renumber",
                    f"{spec}:{number}",
                ))
            else:
                defined[identifier] = number
    if not defined:
        section = find_section(spec, "Functional Requirements")
        defined = {i: 0 for i in _FR_ID.findall(section.body if section else "")}
    if backlog is not None and backlog.is_file():
        cited = set(_FR_ID.findall(blank_fenced(_read(backlog))))
        for identifier in sorted(cited - set(defined)):
            findings.append(DocFinding(
                "orphan-fr-ref",
                f"{identifier} is cited in BACKLOG.md but never specified in {spec.name}; "
                "the row it grounds cannot be verified",
                str(backlog),
            ))
    return findings


def _table_shape(
    section: _Section | None,
    columns: tuple[str, ...],
    *,
    code: str,
    label: str,
    spec: Path,
    require_rows: bool = True,
) -> list[DocFinding]:
    """First table under *section* must carry *columns* (exact order) and optional rows."""
    if section is None:
        return []
    tables = parse_tables(section.body)
    if not tables:
        return [DocFinding(
            code,
            f"{label} has no markdown table; the template contract is a table with "
            f"columns {' | '.join(columns)}",
            str(spec),
        )]
    table = tables[0]
    header = tuple(cell.strip() for cell in table.header)
    wanted = tuple(columns)
    # Tolerate case only; order and spelling are the contract.
    if tuple(h.lower() for h in header) != tuple(w.lower() for w in wanted):
        return [DocFinding(
            code,
            f"{label} table columns are {' | '.join(header) or '(none)'!s}; "
            f"template requires exactly {' | '.join(wanted)}",
            f"{spec}:{table.line}",
        )]
    if require_rows and not table.rows:
        return [DocFinding(
            code,
            f"{label} table has a header but zero data rows; fill at least one row "
            "or the section is a placeholder",
            f"{spec}:{table.line}",
        )]
    return []


def _section_line_map(path: Path) -> dict[str, int]:
    """Normalized section title → first heading line, for order checks."""
    out: dict[str, int] = {}
    for section in sections(path):
        key = _norm(section.title)
        if key and key not in out:
            out[key] = section.line
    return out


def check_frd_template(path: Path) -> list[DocFinding]:
    """HOW-TO-MAKE-FRD template contract: IDs, FR fields, table shapes, section order.

    Enforces Rules 1–3, 5–7 and the template's section order / table headers on a
    single ``FRD.md``. Structural violations gate (ERROR); callers may still promote
    warnings with ``as_strict``.
    """
    findings: list[DocFinding] = []
    text = blank_fenced(_read(path))
    feature = path.parent.name

    # --- Rule 1: FR-<FEATURENAME>-<number>: <imperative name> -----------------
    fr_lines: list[tuple[int, str, re.Match[str] | None]] = []
    for number, line in _lines(text):
        if not _FR_HEADING_LOOSE.match(line):
            continue
        strict = _FR_HEADING.match(line)
        fr_lines.append((number, line, strict))
        if strict is None:
            findings.append(DocFinding(
                "fr-id-format",
                f"line {number} heading {line.strip()[:80]!r} must be "
                f"'### FR-{feature.upper()}-NNN: <short imperative name>' "
                "(HOW-TO Rule 1: FR-<FEATURENAME>-<number>)",
                f"{path}:{number}",
            ))
            continue
        _identifier, name, _num, title = strict.groups()
        if name.upper() != feature.upper().replace("-", ""):
            # Feature folder is the FEATURENAME segment (check → CHECK).
            expected = feature.upper().replace("-", "")
            if name.upper() != expected:
                findings.append(DocFinding(
                    "fr-id-format",
                    f"line {number} uses feature segment {name!r} but this FRD lives under "
                    f"{feature!r}; use FR-{expected}-{_num}",
                    f"{path}:{number}",
                ))
        if len(title.strip()) < 3:
            findings.append(DocFinding(
                "fr-id-format",
                f"line {number} FR heading needs a short imperative name after the colon",
                f"{path}:{number}",
            ))

    if not fr_lines:
        findings.append(DocFinding(
            "fr-id-format",
            "no '### FR-…' headings under Functional Requirements; "
            "each requirement is a heading per HOW-TO Rule 1",
            f"{path}",
        ))

    # --- Rule 2: six fields on every FR block ---------------------------------
    sections_list = sections(path)
    for index, section in enumerate(sections_list):
        # sections() stores title without leading #s — re-match raw title
        raw = f"### {section.title}"
        if not _FR_HEADING_LOOSE.match(raw):
            continue
        # Body ends at the next heading of any level (sections() already slices).
        # Collect fields only until a non-field bullet run ends after all found fields.
        body = section.body
        missing = [field for field in _FR_FIELDS if f"**{field}**" not in body]
        # Avoid flagging a trailing non-FR section that absorbed nothing: body of an FR
        # is everything until the next heading, which is correct for ### FR blocks.
        if section.level >= 3 and _FR_HEADING_LOOSE.match(raw) and missing:
            findings.append(DocFinding(
                "fr-fields-missing",
                f"{section.title.split(':', 1)[0].strip()} is missing "
                f"{', '.join(missing)}; HOW-TO Rule 2 requires Description, Input, "
                "Output, Business Rules, Edge Cases, Error Handling",
                f"{path}:{section.line}",
            ))

    # --- Rule 3 / template table shapes ---------------------------------------
    # API Contract is one section with two required tables: Protocol + Aggregate.
    for label in ("Protocol API", "Aggregate API"):
        section = find_section(path, label)
        if section is None:
            findings.append(DocFinding(
                "api-contract-shape",
                f"API Contract has no {label} subsection; the template splits the "
                "contract into Protocol API (leaf methods) and Aggregate API "
                "(orchestrator / capability aggregate exports) (HOW-TO Rule 3)",
                str(path),
            ))
            continue
        findings.extend(_table_shape(
            section, _API_COLUMNS,
            code="api-contract-shape", label=label, spec=path,
        ))
    findings.extend(_table_shape(
        find_section(path, "Integration Points"), _INTEGRATION_COLUMNS,
        code="integration-shape", label="Integration Points", spec=path,
    ))
    # Rule 5: numbers live here — table present with Target + measurement.
    findings.extend(_table_shape(
        find_section(path, "Non-functional"), _NFR_COLUMNS,
        code="nfr-shape", label="Non-functional Requirements", spec=path,
    ))

    # --- Rule 7: Reference cross-links ----------------------------------------
    ref = find_section(path, "Reference")
    if ref is not None:
        if not re.search(r"\bPRD\b", ref.body, re.IGNORECASE):
            findings.append(DocFinding(
                "reference-crosslink",
                "Reference section must link the root PRD (HOW-TO Rule 7); "
                "promise and claim stay one hop apart",
                f"{path}:{ref.line}",
            ))
        if not re.search(r"BACKLOG", ref.body, re.IGNORECASE):
            findings.append(DocFinding(
                "reference-crosslink",
                "Reference section must link BACKLOG.md (HOW-TO Rule 7)",
                f"{path}:{ref.line}",
            ))

    # --- Template section order -----------------------------------------------
    order_index: list[tuple[int, str]] = []
    line_map = _section_line_map(path)
    for title in _FRD_SECTION_ORDER:
        key = _norm(title)
        line = None
        for found_key, found_line in line_map.items():
            if key in found_key or found_key in key:
                line = found_line
                break
        if line is None:
            continue  # missing section already reported by *-section-missing
        order_index.append((line, title))
    ordered = [title for _, title in sorted(order_index)]
    expected_present = [t for t in _FRD_SECTION_ORDER
                        if any(_norm(t) in k or k in _norm(t) for k in line_map)]
    if ordered != expected_present:
        findings.append(DocFinding(
            "section-order",
            f"FRD sections appear as {', '.join(ordered)}; template order is "
            f"{', '.join(expected_present)}",
            str(path),
        ))

    # --- Rule 6 / template: prose sections are non-empty ----------------------
    for title, code, hint in (
        ("Test Scenarios", "scenario-empty",
         "at least one '- scenario' bullet (Rule 4)"),
        ("Assumptions", "assumption-empty",
         "at least one '- assumption' bullet (Rule 6)"),
        ("Glossary", "glossary-empty",
         "at least one '- **Term**: definition' bullet"),
    ):
        section = find_section(path, title)
        if section is None:
            continue
        body = blank_fenced(section.body)
        bullets = [ln for ln in body.splitlines() if re.match(r"^\s*[-*]\s+\S", ln)]
        if not bullets:
            findings.append(DocFinding(
                code,
                f"{title} has no bullet items; the template requires {hint}",
                f"{path}:{section.line}",
            ))

    return findings


def check_scenarios(spec: Path, backlog: Path | None) -> list[DocFinding]:
    """Rule *the spec states each scenario; the backlog records whether anything asserts it*."""
    section = find_section(spec, "Test Scenarios")
    if section is None or backlog is None or not backlog.is_file():
        return []
    scenarios = [line for line in blank_fenced(section.body).splitlines()
                 if re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", line) and "<" not in line]
    if not scenarios:
        return []
    evidence = find_section(backlog, "Scenario evidence")
    if evidence is None:
        return [DocFinding(
            "scenario-without-evidence",
            f"{spec.name} states {len(scenarios)} test scenario(s) but BACKLOG.md has no "
            "Scenario evidence table; nothing records whether any of them are tested",
            str(backlog),
        )]
    rows = sum(len(table.rows) for table in parse_tables(evidence.body))
    if rows != len(scenarios):
        return [DocFinding(
            "scenario-evidence-count",
            f"{len(scenarios)} scenario(s) in the spec against {rows} evidence row(s); "
            "one row per scenario, in spec order, marked Automated/Proxy/Manual/Gap",
            str(backlog),
            severity=WARN,
        )]
    return []


# --- pointers, hygiene, budgets ---------------------------------------------
def check_links(path: Path, *, skill_local_only: bool = False) -> list[DocFinding]:
    """Rule *every pointer a document tells the reader to follow resolves*."""
    findings: list[DocFinding] = []
    for target, number in md_links(_read(path)):
        if not _is_resolvable(target):
            continue
        if skill_local_only and not target.startswith(("references/", "scripts/", "assets/")):
            continue
        bare = target.split("#", 1)[0]
        if not (path.parent / bare).exists():
            findings.append(DocFinding(
                "dead-link",
                f"line {number} links {target!r}, which does not resolve",
                f"{path}:{number}",
            ))
    return findings


def check_surface_links(skill_md: Path) -> list[DocFinding]:
    """Rule *a skill surfaces every file under* ``references/`` */*scripts/``*, so an
    agent is actually told to open it, and every skill-internal pointer resolves."""
    findings: list[DocFinding] = []
    raw = _read(skill_md)
    surfaced = {target for target, _ in md_links(raw)}
    skill_dir = skill_md.parent
    refs = skill_dir / "references"
    # SKILL.md's own local links are covered by check_links; the reference files it
    # hands agents to are not scanned anywhere else, so their pointers are checked here.
    for doc in sorted(refs.glob("*.md")) if refs.is_dir() else []:
        findings.extend(_check_internal_links(doc, skill_dir))
    for sub in ("references", "scripts", "assets"):
        folder = skill_md.parent / sub
        if not folder.is_dir():
            continue
        for asset in sorted(folder.rglob("*")):
            if not asset.is_file() or asset.suffix.lower() not in {".md", ".py", ".sh", ".json", ".txt"}:
                continue
            rel = str(asset.relative_to(skill_md.parent))
            # A script named in a command block is surfaced too, not only a markdown link.
            if rel in surfaced or asset.name in surfaced or asset.name in raw:
                continue
            findings.append(DocFinding(
                "unreferenced-file",
                f"{rel} is not linked from {skill_md.name}, so no agent is ever told to open it",
                str(asset),
                severity=WARN,
            ))
    return findings


def _check_internal_links(doc: Path, skill_dir: Path) -> list[DocFinding]:
    """Flag relative links from *doc* that aim inside *skill_dir* but land nowhere.

    A pointer out of the skill (another repo file, a URL) is not this rule's business —
    the skill pack hosts upstream copies whose external links are not ours to fix.

    Two shapes look alike and are not: a link written relative to the skill root instead
    of the file resolves for an agent whose working directory is the skill, so it is
    advisory; one that resolves from neither is a broken pointer nobody can follow.
    """
    findings: list[DocFinding] = []
    for target, number in md_links(_read(doc)):
        if not _is_resolvable(target):
            continue
        bare = target.split("#", 1)[0]
        if not bare:
            continue
        resolved = (doc.parent / bare).resolve()
        root = skill_dir.resolve()
        if not (root in resolved.parents or resolved == root):
            continue
        if resolved.exists():
            continue
        if (root / bare).exists():
            findings.append(DocFinding(
                "root-relative-link",
                f"{doc.name}:{number} links {target!r} from the skill root while the file sits "
                f"in {doc.parent.name}/; prefix it with '../' so a reader standing here can "
                "follow it",
                f"{doc}:{number}",
                severity=WARN,
            ))
            continue
        findings.append(DocFinding(
            "dead-link",
            f"{doc.name}:{number} links {target!r} inside the skill folder, which does not "
            "resolve; an agent following it reads nothing",
            f"{doc}:{number}",
        ))
    return findings


def check_hygiene(path: Path) -> list[DocFinding]:
    """Rules *no absolute personal path* and *no secret*, in any owned document."""
    findings: list[DocFinding] = []
    for number, line in _lines(blank_fenced(_read(path))):
        if _ABSOLUTE_PATH.search(line):
            findings.append(DocFinding(
                "absolute-path",
                f"line {number} hardcodes a machine path ({line.strip()[:60]!r}); use $HOME "
                "or a repo-relative path",
                f"{path}:{number}",
            ))
        secret = _secret_value(line)
        if secret:
            findings.append(DocFinding(
                "secret-in-docs",
                f"line {number} assigns a literal value ({secret[:24]!r}) to a credential-ish "
                "key; reference the variable name, never the value",
                f"{path}:{number}",
            ))
    return findings


def _secret_value(line: str) -> str:
    """The literal on the right of a credential-looking assignment, or an empty string."""
    key = _SECRET_KEY.search(line)
    if not key:
        return ""
    value = _SECRET_VALUE.match(line, key.end())
    if not value:
        return ""
    text = value.group("quoted") or value.group("bare") or ""
    return "" if _PLACEHOLDER_VALUE.match(text) else text


def _ci_text(root: Path) -> str:
    workflows = root / ".github" / "workflows"
    return "\n".join(_read(f) for f in sorted(workflows.glob("*.yml"))) if workflows.is_dir() else ""


def check_command_drift(agents_md: Path, ci_text: str) -> list[DocFinding]:
    """Rule *AGENTS.md commands match CI exactly or are labelled advisory*.

    Only the commands section — whatever it is headed as, see ``_COMMANDS_HEADINGS`` — is
    gated: every other command in the file is teaching, not a gate an agent will be
    judged on.
    """
    if not ci_text:
        return []
    findings: list[DocFinding] = []
    in_commands = False
    commands_level = 0
    fence = ""
    for number, line in _lines(_read(agents_md)):
        heading = _HEADING_LINE.match(line) if not fence else None
        if heading:
            level = len(heading.group(1))
            title = _norm(heading.group(2))
            if any(_norm(alias) in title for alias in _COMMANDS_HEADINGS):
                in_commands, commands_level = True, level
            elif in_commands and level <= commands_level:
                in_commands = False
        marker = _FENCE.match(line)
        if marker:
            if not fence:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = ""
            continue
        stripped = line.strip()
        if not fence or not in_commands or not stripped or stripped.startswith("#"):
            continue
        if _ADVISORY.search(stripped):
            continue
        for gate in _GATE_COMMANDS:
            if re.search(rf"(?<![\w-]){re.escape(gate)}(?![\w-])", stripped) and not re.search(
                    rf"(?<![\w-]){re.escape(gate)}(?![\w-])", ci_text):
                findings.append(DocFinding(
                    "ci-command-drift",
                    f"line {number} prints {gate!r} but no CI job runs it; agents will either "
                    "report false breakage or skip the gate — match CI or label it advisory",
                    f"{agents_md}:{number}",
                ))
    return findings


def check_length_budget(path: Path) -> list[DocFinding]:
    """Rule *each document stays inside the size its audience can read*."""
    # Flat line budget for every document type: 50-line floor (catches gutted
    # docs), 500-line cap (catches bloat). Line counts, not words: a wide
    # table row is one line regardless of how many cells it holds.
    budgets = {
        "PRD.md": ("lines", 50, 500),
        "ROADMAP.md": ("lines", 50, 500),
        "README.md": ("lines", 50, 500),
        "BACKLOG.md": ("lines", 50, 500),
        "AGENTS.md": ("lines", 50, 500),
        "FRD.md": ("lines", 50, 500),
    }
    budget = budgets.get(path.name)
    if not budget:
        return []
    unit, low, high = budget
    text = _read(path)
    count = len(text.splitlines()) if unit == "lines" else len(text.split())
    if count > high:
        return [DocFinding(
            "doc-length",
            f"{count} {unit} is over the {high}-{unit} budget for {path.name}; compress in "
            "place rather than splitting a section the reader must choose to open",
            str(path),
            severity=WARN,
        )]
    if count < low:
        return [DocFinding(
            "doc-thin",
            f"{count} {unit} is under the {low}-{unit} floor for {path.name}; sections are "
            "probably missing rather than concise",
            str(path),
            severity=WARN,
        )]
    return []


# --- orchestration ------------------------------------------------------------
def iter_doc_files(root: Path, *, include_subtrees: bool = False) -> list[Path]:
    """Every document whose invariants this module enforces, under *root*.

    Args:
        root: Directory to walk.
        include_subtrees: Also descend into ``vendor/`` and ``internal/``, which are
            upstream submodules in this ecosystem and skipped by default.

    Returns:
        Sorted ``PRD.md``/``ROADMAP.md``/``FRD.md``/``README.md``/``AGENTS.md``/
        ``BACKLOG.md``/``SKILL.md`` paths, ignoring build and dependency trees.
    """
    names = frozenset((*DOC_NAMES, "SKILL.md"))
    found: list[Path] = []
    # One walk that prunes as it goes: a rglob per name would descend into .git and every
    # node_modules tree, which costs more than all the parsing combined.
    for dirpath, dirnames, filenames in os.walk(root):
        parts = Path(dirpath).relative_to(root).parts
        if parts and parts[0] in _OWNERSHIP_SKIP_DIRS and not include_subtrees:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in _SKIP_PARTS]
        found.extend(Path(dirpath) / name for name in filenames if name in names)
    return sorted(found)


def _owns_finding(path: Path) -> bool:
    """Whether findings on *path* are gating or only advisory."""
    return path.name in DOC_NAMES


def audit_docs(root: Path, *, include_subtrees: bool = False) -> list[DocFinding]:
    """Check *root* against every document invariant; an empty list means clean.

    Args:
        root: Project root holding the root-level documents plus the per-feature
            ``FRD.md``/``BACKLOG.md`` pairs.
        include_subtrees: Include vendored/submodule trees in the walk.

    Returns:
        Findings sorted by path, code and message, warnings included.
    """
    findings: list[DocFinding] = []
    docs = iter_doc_files(root, include_subtrees=include_subtrees)
    ci_text = _ci_text(root)

    for path in docs:
        gating = _owns_finding(path)
        raw: list[DocFinding] = []
        raw.extend(check_links(path, skill_local_only=not gating))
        if gating:
            raw.extend(check_hygiene(path))
            raw.extend(check_length_budget(path))
        for title in _missing_sections(blank_fenced(_read(path)), path.name):
            # Scenario Evidence is a feature-backlog obligation (HOW-TO-MAKE-BACKLOG);
            # a root master BACKLOG follows the ROADMAP contract instead.
            if path.name == "BACKLOG.md" and path.parent == root and title == "Scenario Evidence":
                continue
            raw.append(DocFinding(
                f"{path.name[:-3].lower()}-section-missing",
                f"no {title!r} section; the section contract marks it required",
                str(path),
                severity=WARN if path.name in _SOFT_SECTIONS or not gating else ERROR,
            ))
        if path.name == "FRD.md":
            raw.extend(check_spec_status_leak(path))
            raw.extend(check_fr_ids(path, path.parent / "BACKLOG.md"))
            raw.extend(check_scenarios(path, path.parent / "BACKLOG.md"))
            raw.extend(check_frd_template(path))
        elif path.name == "PRD.md":
            raw.extend(check_spec_status_leak(path))
        elif path.name in ("BACKLOG.md", "ROADMAP.md"):
            raw.extend(check_backlog_rows(path))
        if path.name == "AGENTS.md":
            raw.extend(check_command_drift(path, ci_text))
        if path.name == "SKILL.md":
            raw.extend(check_surface_links(path))
        if not gating:
            # The pack ships upstream SKILL.md copies: only their own local pointers are
            # ours to enforce, so everything else about them stays advisory.
            raw = [
                f if f.code in _ALWAYS_GATING else DocFinding(f.code, f.message, f.path, WARN)
                for f in raw
            ]
        findings.extend(raw)

    findings.extend(check_spec_pairing(root))
    findings.extend(check_state_vocabulary(root))
    # Strict is the only mode: every finding gates; there is no advisory tier.
    return as_strict(sorted(set(findings), key=lambda f: (f.path, f.code, f.message)))


def errors_only(findings: list[DocFinding]) -> list[DocFinding]:
    """The findings that must be fixed before the documents can be trusted."""
    return [finding for finding in findings if finding.is_error]


def warnings_only(findings: list[DocFinding]) -> list[DocFinding]:
    """The findings a project may legitimately decline."""
    return [finding for finding in findings if not finding.is_error]


def as_strict(findings: list[DocFinding]) -> list[DocFinding]:
    """Promote every warning to an error, for the gate of a document-heavy repo."""
    return [
        finding if finding.is_error else DocFinding(finding.code, finding.message, finding.path, ERROR)
        for finding in findings
    ]
