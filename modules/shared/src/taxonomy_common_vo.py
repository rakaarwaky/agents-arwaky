"""Shared value objects + pure helpers — taxonomy layer (non-feature).

Merged from: core_vo, manifest_vo, tool_vo, version_vo, launcher_vo, venv_vo,
doc_vo, xdg_paths, xdg_atomic_io, skill_audit. Feature-specific VOs live in
``taxonomy_<feature>_vo``.
"""
from __future__ import annotations

import datetime
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    _FENCE,
    DEFAULT_VERSION,
    DESCRIPTION_BUDGET_BYTES,
    ERROR,
    SKILL_FILE,
)
from modules.shared.src.taxonomy_common_constant import (
    REPO_ROOT as repo_root,
)

# --- core VOs ------------------------------------------------------------------


class Timestamp:
    """Frozen float timestamp VO (e.g. install/update stamps)."""

    __slots__ = ("_value",)

    def __init__(self, value: float) -> None:
        if not isinstance(value, float):
            value = float(value)
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> float:
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"Timestamp({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Timestamp):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


class ToolId:
    """Frozen string tool identifier VO (manifest `id`)."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        value = str(value)
        if not value:
            raise ValueError("ToolId must not be empty")
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"ToolId({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ToolId):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


@dataclass(frozen=True)
class AuditFinding:
    """One violated document invariant, ready for CLI reporting."""

    code: str
    message: str
    path: str = ""
    severity: str = "error"

    @property
    def is_error(self) -> bool:
        return self.severity == "error"


# --- manifest / tool VOs -------------------------------------------------------


@dataclass(frozen=True)
class Tool:
    """One entry of config/manifest.json (frozen VO)."""

    id: str
    category: str
    binary: str
    is_mcp: bool
    description: str
    path: str
    alias: str | None = None
    aliases: tuple[str, ...] = ()
    mcp_binary: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    """Resolved, immutable view of a manifest tool used by tool capabilities."""

    id: str
    category: str
    binary: str
    is_mcp: bool
    description: str
    path: str
    alias: str | None
    mcp_binary: str | None
    runner: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class InstallResult:
    """Outcome of a tool installation."""

    success: bool
    tool_id: str
    message: str


@dataclass(frozen=True)
class UpdateResult:
    """Outcome of a tool update."""

    success: bool
    tool_id: str
    message: str


@dataclass(frozen=True)
class UninstallResult:
    """Outcome of a tool uninstallation."""

    success: bool
    tool_id: str
    message: str


# --- version helpers (pure functions, allowed in _vo files) -------------------


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string (install/update stamps).

    Lives in taxonomy so utilities stay clock-free (aes-utility: no
    `datetime.now()` inside utility modules).
    """
    return datetime.datetime.now(datetime.UTC).isoformat()


def _version_file() -> Path:
    return repo_root / "config" / "version.txt"


def read_version() -> str:
    """Current version from config/version.txt (default 0.1.0)."""
    version_file = _version_file()
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return DEFAULT_VERSION


def bump(current: str, part: str) -> str:
    """Bump the current version by *part* (``major``/``minor``/``patch``).

    Raises:
        ValueError: if the version is unparseable or *part* is unknown.
    """
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", current.strip())
    if not m:
        raise ValueError(f"Unrecognized version format: {current!r}")
    major, minor, patch = (int(g) for g in m.groups())
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(
            f"Unknown version part {part!r}; expected major, minor or patch "
            f"(current: {current})"
        )
    return f"{major}.{minor}.{patch}"


# --- launcher / venv VOs -------------------------------------------------------


@dataclass(frozen=True)
class LauncherSpec:
    """One launcher to be written into $XDG_BIN_HOME."""

    name: str
    entry: str
    uv_args: tuple[str, ...] = ()


@dataclass(frozen=True)
class VenvInfo:
    """A venv install location for a Python tool."""

    tool_name: str
    venv_dir: str
    python_bin: str


# --- document-invariant VOs ----------------------------------------------------


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
class Section:
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


# --- XDG path resolution (pure functions over environment variables) -----------


def data_home() -> Path:
    """XDG_DATA_HOME (default ~/.local/share)."""
    p = os.environ.get("XDG_DATA_HOME")
    return Path(p).expanduser() if p else Path.home() / ".local" / "share"


def config_home() -> Path:
    """XDG_CONFIG_HOME (default ~/.config)."""
    p = os.environ.get("XDG_CONFIG_HOME")
    return Path(p).expanduser() if p else Path.home() / ".config"


def cache_home() -> Path:
    """XDG_CACHE_HOME (default ~/.cache)."""
    p = os.environ.get("XDG_CACHE_HOME")
    return Path(p).expanduser() if p else Path.home() / ".cache"


def state_home() -> Path:
    """XDG_STATE_HOME (default ~/.local/state)."""
    p = os.environ.get("XDG_STATE_HOME")
    return Path(p).expanduser() if p else Path.home() / ".local" / "state"


def bin_home() -> Path:
    """XDG_BIN_HOME launcher dir (default ~/.local/bin)."""
    p = os.environ.get("XDG_BIN_HOME")
    return Path(p).expanduser() if p else Path.home() / ".local" / "bin"


def tool_data_dir(tool: str) -> Path:
    """XDG data dir for one tool."""
    return data_home() / tool


def tool_config_dir(tool: str) -> Path:
    """XDG config dir for one tool."""
    return config_home() / tool


def tool_cache_dir(tool: str) -> Path:
    """XDG cache dir for one tool."""
    return cache_home() / tool


def tool_state_dir(tool: str) -> Path:
    """XDG data dir with state suffix for one tool."""
    return data_home() / f"{tool}.state"


def agents_arwaky_config_dir() -> Path:
    """Config dir of the agents-arwaky orchestrator itself."""
    return config_home() / "agents-arwaky"


# --- XDG side-effect I/O helpers ----------------------------------------------


def ensure_bin_home() -> None:
    bin_home().mkdir(parents=True, exist_ok=True)


def bin_on_path() -> bool:
    """True if $XDG_BIN_HOME is already on this process's PATH."""
    return str(bin_home()) in os.environ.get("PATH", "").split(os.pathsep)


def ensure_path() -> None:
    """Prepend $XDG_BIN_HOME to current process PATH (not persistent shell)."""
    b = str(bin_home())
    ensure_bin_home()
    paths = os.environ.get("PATH", "").split(os.pathsep)
    if b not in paths:
        os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")


def warn_if_bin_not_on_path() -> bool:
    """Warn once if $XDG_BIN_HOME is not on PATH (useful for installers).

    Return True if already on PATH (safe), False if user needs to add it.
    """
    if bin_on_path():
        return True
    print(
        f"  [WARN] {bin_home()} is not on your PATH.\n"
        f"         Launchers installed there won't be found by your shell.\n"
        f"         Add it to your profile, e.g.:\n"
        f"           echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc\n",
        file=sys.stderr,
    )
    return False


def remove_tool_artifacts(
    tool: str,
    launchers: list[str],
    *,
    clean_config: bool = True,
) -> None:
    """Remove all XDG artifacts that installers may have created for a tool.

    Removes: launchers + aliases in bin, data, cache (including build dir),
    and (optionally) config dir. Does not touch $XDG_STATE_HOME.
    Also cleans up .venv and target/ in source directories.
    """
    for name in launchers:
        (bin_home() / name).unlink(missing_ok=True)
    shutil.rmtree(tool_data_dir(tool), ignore_errors=True)
    shutil.rmtree(tool_cache_dir(tool), ignore_errors=True)
    if clean_config:
        shutil.rmtree(tool_config_dir(tool), ignore_errors=True)
    # Clean up build artifacts in source directories — only safe dirs
    source_candidates = [
        Path.home() / "projects" / tool,
        Path.home() / "src" / tool,
    ]
    for src_dir in source_candidates:
        if not src_dir.exists():
            continue
        # Clean .venv (uv-based Python tools)
        venv_path = src_dir / ".venv"
        if venv_path.is_symlink():
            venv_path.unlink(missing_ok=True)
        elif venv_path.is_dir():
            shutil.rmtree(venv_path, ignore_errors=True)
        # Clean target/ (Rust cargo tools)
        target_path = src_dir / "target"
        if target_path.is_dir():
            shutil.rmtree(target_path, ignore_errors=True)


def atomic_write_text(path: Path, content: str, mode: int = 0o755) -> None:
    """Atomically write file (temp + os.replace).

    Avoids ETXTBSY ('Text file busy') when overwriting an executable
    that is currently running: rename is safe because the old process
    still holds the old inode.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.chmod(mode)
    os.replace(tmp, path)


# --- skill-pack loadability audit (pure, stateless) ---------------------------

_SKIP_PARTS = {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"}


@dataclass(frozen=True)
class PackFinding:
    """One violated loadability invariant, ready for CLI reporting."""

    code: str
    message: str
    path: str = ""


def _read(skill_md: Path) -> str:
    try:
        return skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontmatter_value(text: str, field: str) -> str:
    block = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not block:
        return ""
    found = re.search(
        rf"^{field}:\s*[\"']?(.*?)[\"']?\s*$", block.group(1), re.MULTILINE
    )
    return found.group(1).strip() if found else ""


def skill_name(skill_md: Path) -> str:
    return _frontmatter_value(_read(skill_md), "name")


def skill_description(skill_md: Path) -> str:
    return _frontmatter_value(_read(skill_md), "description")


def iter_skill_files(base: Path) -> list[Path]:
    """Every ``SKILL.md`` under *base*, ignoring vendored/build directories."""
    if not base.is_dir():
        return []
    return [
        path
        for path in sorted(base.rglob(SKILL_FILE))
        if not _SKIP_PARTS.intersection(path.relative_to(base).parts)
    ]


def pack_names(base: Path) -> set[str]:
    """Folder names of every skill in the pack."""
    return {path.parent.name for path in iter_skill_files(base)}


def audit_pack(base: Path) -> list[PackFinding]:
    """Check the pack against the loadability invariants; empty list means clean."""
    files = iter_skill_files(base)
    if not files:
        return [PackFinding("pack-missing", f"No {SKILL_FILE} found under {base}", str(base))]

    findings: list[PackFinding] = []
    seen: dict[str, str] = {}
    description_bytes = 0
    categories: set[str] = set()

    for path in files:
        parts = path.relative_to(base).parts
        rel_text = str(Path(base.name, *parts))
        category = parts[0] if len(parts) >= 2 else ""
        skill_dir = parts[1] if len(parts) >= 3 else ""
        if category:
            categories.add(category)

        # 1. one level below a category: <category>/<skill>/SKILL.md
        if len(parts) != 3:
            findings.append(PackFinding(
                "nested-layout",
                f"{rel_text} is not <category>/<skill>/{SKILL_FILE}; the harness scans "
                "one level below a skills root, so this skill never loads",
                rel_text,
            ))

        text = _read(path)

        # 2. frontmatter name == folder name
        name = _frontmatter_value(text, "name")
        if not name:
            findings.append(PackFinding("name-missing", f"{rel_text} has no frontmatter name:", rel_text))
        elif skill_dir and name != skill_dir:
            findings.append(PackFinding(
                "name-mismatch",
                f"{rel_text} declares name '{name}' but lives in folder '{skill_dir}'",
                rel_text,
            ))

        # 3. non-empty description
        description = _frontmatter_value(text, "description")
        if not description:
            findings.append(PackFinding(
                "description-missing", f"{rel_text} has no description:", rel_text
            ))
        description_bytes += len(description.encode("utf-8"))

        # 4. names unique across the whole pack
        if name:
            if name in seen:
                findings.append(PackFinding(
                    "duplicate-name",
                    f"'{name}' is used by both {seen[name]} and {rel_text}",
                    rel_text,
                ))
            else:
                seen[name] = rel_text

    # 5. aggregate description budget (injected into every session prompt)
    if description_bytes > DESCRIPTION_BUDGET_BYTES:
        findings.append(PackFinding(
            "description-budget",
            f"descriptions total {description_bytes} bytes, over the "
            f"{DESCRIPTION_BUDGET_BYTES}-byte budget; shorten triggers or move detail "
            "into references/*.md",
            base.name,
        ))

    # A category with no skill is never registered as a root, so it hides its files.
    present = {
        entry.name
        for entry in sorted(base.iterdir())
        if entry.is_dir() and not entry.name.startswith(".")
        and entry.name not in _SKIP_PARTS
    }
    for empty in sorted(present - categories):
        findings.append(PackFinding(
            "empty-category",
            f"skills/{empty} holds no <skill>/{SKILL_FILE}; a category with no skill "
            "is never registered as a skills root, so anything inside it is invisible",
            f"{base.name}/{empty}",
        ))

    # A folder at skill depth must carry SKILL.md directly, or the loader skips it.
    for category in sorted(present):
        for entry in sorted((base / category).iterdir()):
            if not entry.is_dir() or entry.name.startswith(".") or entry.name in _SKIP_PARTS:
                continue
            if not (entry / SKILL_FILE).is_file():
                findings.append(PackFinding(
                    "skill-without-skill-md",
                    f"skills/{category}/{entry.name} has no {SKILL_FILE}; the loader "
                    "only reads that exact filename, so the folder is dead weight",
                    f"{base.name}/{category}/{entry.name}",
                ))

    return findings


# --- Shared VO types for contracts (AES402 compliance) ------------------------
from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Raw or parsed configuration data mapping.
ConfigData = NewType("ConfigData", dict)

#: Configuration file format ("yaml", "jsonc", "json", "toml").
ConfigFormat = NewType("ConfigFormat", str)

#: Tuple of (data, format) loaded from a configuration file.
ConfigTuple = tuple[ConfigData, ConfigFormat]

#: Mapping of environment key-value pairs.
EnvPairs = NewType("EnvPairs", dict)

#: Mapping of MCP server specifications.
McpServersMap = NewType("McpServersMap", dict)

#: Domain message VO — wraps a human-readable error string (AES401/AES402).
ErrorMessage = NewType("ErrorMessage", str)

#: Help / usage text returned by an aggregate's ``help`` method.
HelpText = NewType("HelpText", str)

#: Read-only config inspection snapshot (path, format, data, servers).
ConfigSnapshot = NewType("ConfigSnapshot", dict)

#: Operation token dispatched through ``IConfigProtocol.execute``.
ConfigOp = NewType("ConfigOp", str)

#: Named config/server/env keys accepted by a remove or merge call.
ConfigKeys = NewType("ConfigKeys", list)

#: Aggregated document-invariant findings (audit output bag).
DocFindings = NewType("DocFindings", list)

#: Flag bag for doctor diagnostics (``json`` toggle, ``mode`` selector).
DoctorFlags = NewType("DoctorFlags", dict)

#: Polymorphic doctor report payload rendered by the report action.
DoctorReport = NewType("DoctorReport", object)

#: Tuple of manifest tools returned by ``IToolsAggregate.list``.
ToolList = NewType("ToolList", list)


# --- markdown/text helpers (shared by doc_pack / doc_hygiene utilities) --------


def read_md_text(path: Path) -> str:
    """File contents of *path*, or an empty string when unreadable."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def norm_md_heading(text: str) -> str:
    """Lowercase and strip punctuation/emoji so heading matching tolerates decoration."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def blank_fenced(text: str) -> str:
    """Return *text* with fenced code bodies replaced by blank lines.

    Line count and numbering are preserved, so a caller can still report a line.
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


def numbered_lines(text: str) -> list[tuple[int, str]]:
    """1-based ``(line, content)`` pairs."""
    return list(enumerate(text.splitlines(), start=1))


def markdown_links(text: str) -> list[tuple[str, int]]:
    """``(target, line)`` for every markdown link outside a fenced block."""
    out: list[tuple[str, int]] = []
    for number, line in numbered_lines(blank_fenced(text)):
        for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            out.append((match.group(1), number))
    return out


def is_resolvable_link(target: str) -> bool:
    """Whether *target* is a real relative path rather than an anchor, URL or placeholder."""
    if target.startswith(("#", "/", "http://", "https://", "mailto:", "tel:")):
        return False
    return not any(bad in target for bad in ("<", ">", "*", "...", "$", "{", "%"))


__all__ = [
    "DEFAULT_VERSION",
    "DESCRIPTION_BUDGET_BYTES",
    "SKILL_FILE",
    "AuditFinding",
    "ConfigData",
    "ConfigFormat",
    "ConfigKeys",
    "ConfigOp",
    "ConfigSnapshot",
    "ConfigTuple",
    "DocFinding",
    "DocFindings",
    "DoctorFlags",
    "DoctorReport",
    "EnvPairs",
    "ErrorMessage",
    "ExitCode",
    "HelpText",
    "InstallResult",
    "LauncherSpec",
    "McpServersMap",
    "PackFinding",
    "Section",
    "Timestamp",
    "Tool",
    "ToolId",
    "ToolList",
    "ToolSpec",
    "UninstallResult",
    "UpdateResult",
    "VenvInfo",
    "agents_arwaky_config_dir",
    "audit_pack",
    "bin_home",
    "bin_on_path",
    "blank_fenced",
    "bump",
    "cache_home",
    "config_home",
    "data_home",
    "ensure_bin_home",
    "ensure_path",
    "is_resolvable_link",
    "iter_skill_files",
    "markdown_links",
    "norm_md_heading",
    "numbered_lines",
    "pack_names",
    "read_md_text",
    "read_version",
    "remove_tool_artifacts",
    "repo_root",
    "skill_description",
    "skill_name",
    "state_home",
    "tool_cache_dir",
    "tool_config_dir",
    "tool_data_dir",
    "tool_state_dir",
    "utc_now_iso",
    "warn_if_bin_not_on_path",
]
