"""Machine checks for the document invariants the ``add-docs`` skill states in prose.

Prose cannot be re-run, so a repository drifts back the moment an agent forgets to grep.
Each check here is the direct translation of one rule in
``skills/documentation/add-docs/SKILL.md``, and each finding names the rule it enforces,
so the guide and the gate cannot quietly diverge.

Two severities. ``error`` means a claim sits in the wrong file, a pointer is broken, or a
status assertion has no re-runnable evidence behind it — all of which mislead the next
reader immediately. ``warn`` covers shape a project may legitimately vary on (section
wording, length budgets). ``aa docs check --strict`` promotes every warning.

Files the pack does not own (``SKILL.md`` copies of upstream tools) are only gated on
their own local pointers; everything else about them is reported as a warning.

Fenced code bodies are blanked before content checks: the skill's templates deliberately
contain ``Status:`` lines and checkboxes, and it is a document's prose that carries claims.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

ERROR = "error"
WARN = "warn"

#: Build/vendored trees that never carry this project's documents.
_SKIP_PARTS = {
    ".git", ".hg", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv",
    "__pycache__", "build", "dist", "node_modules", "site-packages", "target", "venv",
    ".worktree", ".worktrees",
}
#: Submodule trees are upstream-owned, so a finding there is noise nobody may act on.
#: ``include_subtrees=True`` opts back in.
_OWNERSHIP_SKIP_DIRS = {"vendor", "internal"}

SPEC_DOCS = ("PRD.md", "FRD.md")
DOC_NAMES = ("PRD.md", "FRD.md", "README.md", "AGENTS.md", "BACKLOG.md")
#: Documents this repo authors; findings on anything else are advisory.
OWNED_DOCS = (*DOC_NAMES, "SKILL.md")

#: The state vocabulary, which lives once in the root master backlog.
STATE_VOCAB = (
    "Idea", "Refinement", "Ready", "In Progress", "Blocked", "In Review",
    "QA", "Done", "Released", "Deferred",
)
HEALTH_VOCAB = (
    "On Track", "At Risk", "Blocked", "Ready for QA", "Ready for Release", "Released",
)
#: States that assert finished work, and therefore owe evidence.
EVIDENCED_STATES = {"Done", "Released"}

#: Column order a ``Backlog`` table must keep, per references/backlog.md.
BACKLOG_COLUMNS = (
    "ID", "FRD Ref", "Work Item", "Priority", "State",
    "Actual Condition", "Owner", "Dependencies", "Updated",
)

#: Findings that stay gating even on files the pack merely hosts (upstream ``SKILL.md``
#: copies): a broken pointer is a broken pointer whoever wrote the file.
_ALWAYS_GATING = {"dead-link"}

#: Sections that may exist only in the root master backlog, per references/backlog.md.
MASTER_ONLY_SECTIONS = (
    "State definitions", "Status policy", "Feature roll-up",
    "Branches in flight", "Risk register",
)

#: Headings that hold the runnable commands. Both the section contract and the CI-drift
#: check use this list, so a repo may head that section either way and still be gated.
_COMMANDS_HEADINGS = ("Commands", "Command Reference", "Available Commands",
                      "Available Scripts", "Quick Reference Playbook")

#: Section contract, mirroring references/{prd,frd,readme,backlog,agents-md}.md.
REQUIRED_SECTIONS = {
    "PRD.md": ("Problem Statement", "Goals", "Personas", "Scope",
               "Feature Requirements", "Non-functional", "Open Questions"),
    "FRD.md": ("Reference", "System Overview", "Functional Requirements",
               "API Contract", "Integration Points", "Non-functional",
               "Test Scenarios", "Assumptions"),
    "README.md": ("Prerequisites", "Quick Start", "Architecture", "Project Structure",
                  "Available Scripts", "Configuration", "Testing", "Contributing", "License"),
    "AGENTS.md": ("Precedence", "Security", "Commands", "Definition of Done",
                  "Related Documents"),
    "BACKLOG.md": ("Current Condition", "Backlog", "Blockers", "Dependencies",
                   "Release Readiness", "Deferred", "Change Log"),
}
#: Canonical contract section -> heading fragments that satisfy it. Repos head the same
#: obligation differently, so the check is on the information being present, not on one
#: spelling. The templates in the add-docs references still show the canonical name first.
_SECTION_ALIASES = {
    "Available Scripts": ("Available Scripts", "Available Commands", "Commands",
                          "Developer Workflows", "Orchestrator CLI"),
    "Commands": _COMMANDS_HEADINGS,
    "Configuration": ("Configuration", "Config", "Environment"),
    "Definition of Done": ("Definition of Done", "Quality Gates", "Done Criteria",
                           "Verification"),
    "Precedence": ("Precedence", "Priority Order", "When Documents Disagree"),
    "Project Structure": ("Project Structure", "Repository Structure", "Repo Layout",
                          "Directory Layout", "Architecture Map"),
    "Quick Start": ("Quick Start", "Quickstart", "Getting Started", "Installation"),
    "Related Documents": ("Related Documents", "Reference Paths", "See Also"),
    "Security": ("Security", "Guardrails", "Safety"),
    "Testing": ("Testing", "Test Suite", "Tests"),
    "Contributing": ("Contributing", "How to Contribute", "Contributor Guide"),
}
#: Sections a harness may legitimately not need, whatever the contract table says.
_SOFT_SECTIONS = {"README.md", "AGENTS.md"}

_COMMITS = re.compile(r"\b[0-9a-f]{7,40}\b")
_CODE_SPAN = re.compile(r"`[^`\n]+`")
_FR_ID = re.compile(r"\bFR-\d+\b")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.MULTILINE)
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")

#: Claims that belong in BACKLOG.md, never in a spec.
_STATUS_LEAKS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*[-*]\s*\[[ xX]\]"), "a checkbox task item"),
    (re.compile(r"^\s*\**\s*status\s*\**\s*:", re.IGNORECASE), "a Status: field"),
    (re.compile(r"\b(?:implemented|unimplemented|partially implemented)\b", re.IGNORECASE),
     "implementation state"),
    (re.compile(r"\b(?:shipped|released|deployed) in v\w*\b", re.IGNORECASE), "release state"),
    (re.compile(r"^\s*(?:✅|❌|🟢|🔴|✔️|✖)"), "a status marker"),
    (re.compile(r"\b\d+\s*%\s*(?:complete|done)", re.IGNORECASE), "a progress percentage"),
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


@dataclass(frozen=True)
class DocFinding:
    """One violated document invariant, ready for CLI reporting."""

    code: str
    message: str
    path: str = ""
    severity: str = ERROR

    @property
    def is_error(self) -> bool:
        """Whether the finding must be fixed before the documents can be trusted."""
        return self.severity == ERROR


@dataclass(frozen=True)
class _Section:
    """A markdown heading and the raw lines under it, up to the next heading."""

    level: int
    title: str
    body: str
    line: int


@dataclass(frozen=True)
class Table:
    """A parsed markdown table: header cells, ``(line, cells)`` rows, header line."""

    header: list[str]
    rows: list[tuple[int, list[str]]]
    line: int


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
def check_spec_status_leak(path: Path) -> list[DocFinding]:
    """Rule *Spec and status never share a file*."""
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
    return findings


def check_spec_pairing(root: Path) -> list[DocFinding]:
    """Rule *every spec has a partner backlog, and one master owns the definitions*."""
    findings: list[DocFinding] = []
    docs = iter_doc_files(root)
    master = root / "BACKLOG.md"
    specs = [path for path in docs if path.name in SPEC_DOCS]
    if specs and not master.is_file():
        findings.append(DocFinding(
            "no-master-backlog",
            f"{len(specs)} spec file(s) but no root BACKLOG.md to own the State/Health "
            "vocabulary and status policy",
            str(master),
        ))
    for spec in specs:
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
        if not any((backlog.parent / name).is_file() for name in SPEC_DOCS):
            findings.append(DocFinding(
                "backlog-without-spec",
                "feature BACKLOG.md has no spec beside it; a row needs a requirement to point at",
                str(backlog),
            ))
    return findings


def check_state_vocabulary(root: Path) -> list[DocFinding]:
    """Rule *definitions live once, in the master root file*."""
    findings: list[DocFinding] = []
    master = root / "BACKLOG.md"
    if master.is_file():
        # The vocabulary may sit in any section (Health usually shares State definitions),
        # so the invariant is that each term is defined somewhere in the master file.
        prose = _norm(blank_fenced(_read(master)))
        for term in (*STATE_VOCAB, *HEALTH_VOCAB):
            if _norm(term) not in prose:
                findings.append(DocFinding(
                    "undefined-state-vocab",
                    f"master backlog never defines {term!r}; feature files cite this "
                    "vocabulary and cannot define it themselves",
                    str(master),
                    severity=WARN,
                ))
        for title in MASTER_ONLY_SECTIONS:
            if find_section(master, title) is None:
                findings.append(DocFinding(
                    "master-section-missing",
                    f"root master backlog has no {title!r} section; this is the one place that "
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
        restated = [t for t in ("State definitions", "Status policy") if _norm(t) in headings]
        if restated:
            findings.append(DocFinding(
                "state-vocab-restated",
                f"feature backlog carries its own {' and '.join(restated)} section; those live "
                "once, in the root master backlog",
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
                    f"{', '.join(STATE_VOCAB)} or add the term to the root file",
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
        match = re.match(r"^#{2,5}\s+(FR-\d+)\b", line)
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
    """Rule *AGENTS.md commands match CI verbatim or are labelled advisory*.

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
        Sorted ``PRD.md``/``FRD.md``/``README.md``/``AGENTS.md``/``BACKLOG.md``/``SKILL.md``
        paths, ignoring build and dependency trees.
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
        elif path.name == "PRD.md":
            raw.extend(check_spec_status_leak(path))
        elif path.name == "BACKLOG.md":
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
    return sorted(set(findings), key=lambda f: (f.path, f.code, f.message))


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
