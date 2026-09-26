"""Pointer/hygiene/budget document checks (utility layer).

Split from ``utility_doc_pack`` for AES301 (max 1000 lines). Shared text helpers
live in taxonomy (AES201: utility may import taxonomy only).
"""
from __future__ import annotations

import re
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    _ABSOLUTE_PATH,
    _ADVISORY,
    _ALWAYS_GATING,
    _COMMANDS_HEADINGS,
    _FENCE,
    _GATE_COMMANDS,
    _HEADING_LINE,
    _OWNERSHIP_SKIP_DIRS,
    _PLACEHOLDER_VALUE,
    _SECRET_KEY,
    _SECRET_VALUE,
    _SKIP_PARTS,
    DOC_NAMES,
    ERROR,
    WARN,
)
from modules.shared.src.taxonomy_common_vo import (
    DocFinding,
    blank_fenced,
    is_resolvable_link,
    markdown_links,
    norm_md_heading,
    numbered_lines,
    read_md_text,
)


# --- pointers, hygiene, budgets ---------------------------------------------
def check_links(path: Path, *, skill_local_only: bool = False) -> list[DocFinding]:
    """Rule *every pointer a document tells the reader to follow resolves*."""
    findings: list[DocFinding] = []
    for target, number in markdown_links(read_md_text(path)):
        if not is_resolvable_link(target):
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
    raw = read_md_text(skill_md)
    surfaced = {target for target, _ in markdown_links(raw)}
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
    for target, number in markdown_links(read_md_text(doc)):
        if not is_resolvable_link(target):
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
    for number, line in numbered_lines(blank_fenced(read_md_text(path))):
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
    return "\n".join(read_md_text(f) for f in sorted(workflows.glob("*.yml"))) if workflows.is_dir() else ""


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
    for number, line in numbered_lines(read_md_text(agents_md)):
        heading = _HEADING_LINE.match(line) if not fence else None
        if heading:
            level = len(heading.group(1))
            title = norm_md_heading(heading.group(2))
            if any(norm_md_heading(alias) in title for alias in _COMMANDS_HEADINGS):
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
    text = read_md_text(path)
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


def owns_gating_doc(path: Path) -> bool:
    """Whether findings on *path* are gating (owned doc names) vs advisory skill copy."""
    return path.name in DOC_NAMES


def audit_hygiene(root: Path, *, include_subtrees: bool = False) -> list[DocFinding]:
    """Pointer/hygiene/budget/CI-drift findings for every owned document under *root*.

    Split from the doc-pack ``audit_docs`` so neither utility imports the other
    (AES201). Consumers merge these with ``audit_docs`` via ``as_strict``.

    Args:
        root: Project root holding the root-level documents plus the per-feature
            ``FRD.md``/``BACKLOG.md`` pairs.
        include_subtrees: Include vendored/submodule trees in the walk.

    Returns:
        Findings sorted by path, code and message, warnings included.
    """
    import os

    names = frozenset((*DOC_NAMES, "SKILL.md"))
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        parts = Path(dirpath).relative_to(root).parts
        if parts and parts[0] in _OWNERSHIP_SKIP_DIRS and not include_subtrees:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in _SKIP_PARTS]
        found.extend(Path(dirpath) / name for name in filenames if name in names)
    docs = sorted(found)
    ci_text = _ci_text(root)
    findings: list[DocFinding] = []
    for path in docs:
        gating = owns_gating_doc(path)
        raw: list[DocFinding] = []
        raw.extend(check_links(path, skill_local_only=not gating))
        if gating:
            raw.extend(check_hygiene(path))
            raw.extend(check_length_budget(path))
        if path.name == "AGENTS.md":
            raw.extend(check_command_drift(path, ci_text))
        if path.name == "SKILL.md":
            raw.extend(check_surface_links(path))
        if not gating:
            raw = [
                f if f.code in _ALWAYS_GATING else DocFinding(f.code, f.message, f.path, WARN)
                for f in raw
            ]
        findings.extend(raw)
    return [
        f if f.is_error else DocFinding(f.code, f.message, f.path, ERROR)
        for f in sorted(set(findings), key=lambda f: (f.path, f.code, f.message))
    ]
