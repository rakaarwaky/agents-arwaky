"""Machine checks for the document invariants the ``add-docs`` skill states in prose.

Shared vocabularies and markdown helpers live in taxonomy; pointer/hygiene/budget
checks live in ``utility_doc_hygiene`` (AES301 split). AES201: utility imports
taxonomy only — capabilities/surface compose both utilities.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    _ALWAYS_GATING,
    _API_COLUMNS,
    _CODE_SPAN,
    _COMMITS,
    _FR_FIELDS,
    _FR_HEADING,
    _FR_HEADING_LOOSE,
    _FR_ID,
    _FRD_SECTION_ORDER,
    _HEADING,
    _INTEGRATION_COLUMNS,
    _NFR_COLUMNS,
    _OWNERSHIP_SKIP_DIRS,
    _SECTION_ALIASES,
    _SKIP_PARTS,
    _SOFT_SECTIONS,
    _SOURCE_EXT,
    _STATUS_LEAKS,
    BACKLOG_COLUMNS,
    DOC_NAMES,
    ERROR,
    EVIDENCED_STATES,
    HEALTH_VOCAB,
    MASTER_ONLY_SECTIONS,
    REPO_ROOT,
    REQUIRED_SECTIONS,
    SPEC_DOCS,
    STATE_VOCAB,
    WARN,
)
from modules.shared.src.taxonomy_common_vo import (
    DocFinding,
    Table,
    blank_fenced,
)
from modules.shared.src.taxonomy_common_vo import Section as _Section
from modules.shared.src.taxonomy_common_vo import (
    norm_md_heading as _norm,
)
from modules.shared.src.taxonomy_common_vo import (
    numbered_lines as _lines,
)
from modules.shared.src.taxonomy_common_vo import (
    read_md_text as _read,
)


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
    repo = REPO_ROOT
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

    for path in docs:
        gating = _owns_finding(path)
        raw: list[DocFinding] = []
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
