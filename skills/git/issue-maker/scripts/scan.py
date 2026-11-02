"""Parse AES spec docs into ScanOutput JSON.

Stdlib only. Reads the discovery JSON (the Rhai ``feature_schema`` object
verbatim: ``{"root": [...], "features": [{"name", "dir", "docs"}]}``), reads
the listed spec docs, and emits an object with ``rows`` / ``fr`` /
``fr_groups`` / ``rollups`` plus per-doc ``docs`` bookkeeping (rows, and a
``warning`` field naming a doc that was unreadable or had in-scope zero
rows). Column tables (ID/Feature/Branch + State) and aes-docs entry tables
(``## Backlog Status`` / ``## Roadmap Status`` + Aspect/Detail) are both
parsed.

Pure over files: no gh, no network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, TypedDict

# FR id tokens, any case scope: aes-docs entries mix case
# (``FR-Filesystem-001``) while agents-arwaky rows stay upper-cased
# (``FR-DOCTOR-001``). Shape mirrors ENTRY_HEADING_RE's id half.
FR_ID_RE = re.compile(r"\bFR-[A-Za-z0-9_]+-\d+\b")
# Doc-level "State: <value>" line near the top of a feature backlog.
# The value is anchored to the simplified four-state vocabulary so a
# trailing note (e.g. "State: In Progress (planned)") does not bleed into
# the captured value.
DOC_STATE_RE = re.compile(
    r"^State:\s*(?P<value>in.progress|in.review|ready|done)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")

# aes-docs dialect (internal/lint-arwaky/.../aes-docs/references): an entry
# heading `### FR-<SCOPE>-NNN: <title>` (H2–H4) followed by an
# `| Aspect | Detail |` table whose row labels carry `State`, etc.
# The `: <title>` half is optional — the template shows it, but real
# BACKLOG files (lint-arwaky crates) carry the bare ID alone.
ENTRY_HEADING_RE = re.compile(
    r"^(#{2,4})\s+(?P<id>(?:FR|DS|DT|PR)-[A-Za-z0-9_]+-\d+)(?::\s*(?P<title>.*))?$"
)
H2_RE = re.compile(r"^##\s+(?P<title>\S.*?)\s*$")
ANY_HEADING_RE = re.compile(r"^#{2,6}\s+")
# Markdown link target inside a table cell: `[...,](path)`.
MD_LINK_RE = re.compile(r"\]\((?P<path>[^)#\s]+)\)")
# Sections whose entry tables are staged for extraction.
ENTRY_SECTIONS = {"backlog status", "roadmap status"}
# Feature-directory markers for resolving a Backlog cell link to a feature.
FEATURE_DIR_MARKERS = ("modules", "packages", "crates")

# Table headers that mark a row table (ID / Branch + State).
ID_HEADERS = {"id", "branch"}
STATE_HEADERS = {"state", "doc_state"}
# Roll-up Feature cells are the feature directory (e.g. ``widgets`` or
# ``modules/tools``); normalize whitespace to "/" for the comparison.

Row = dict[str, Any]
Table = tuple[list[str], list[list[str]]]


class ScanDoc(TypedDict):
    doc: str
    rows: list[Row]
    warning: str | None


def log(msg: str) -> None:
    print(f"[task-tracker:scan] {msg}", file=sys.stderr)


def _split_row(line: str) -> list[str]:
    """Split a markdown table row into cell values between the pipes."""
    cells = line.split("|")
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_separator(cells: list[str]) -> bool:
    # A genuine separator row has one dash cell per column, so every cell
    # must match; do not skip empty cells from the check.
    return bool(cells) and all(SEPARATOR_CELL_RE.match(c) for c in cells)


def _header_names(headers: list[str]) -> set[str]:
    return {h.strip().lower().replace(" ", "_") for h in headers}


def _cell(headers: list[str], cells: list[str], name: str) -> str:
    target = name.strip().lower().replace(" ", "_")
    for idx, header in enumerate(headers):
        if idx < len(cells) and header.strip().lower().replace(" ", "_") == target:
            return cells[idx]
    return ""


def _extract_tables_ctx(
    doc_text: str,
) -> list[tuple[str, tuple[str, str] | None, list[str], list[list[str]]]]:
    """Extract every markdown table with its heading context.

    Returns ``(section, entry, headers, data_rows)`` where ``section`` is
    the normalized level-2 title in effect (``""`` before the first H2)
    and ``entry`` is the most recent aes-docs entry heading
    (``(entry_id, title)``) seen under that H2. A table is a consecutive
    run of lines starting with ``|``; the first line is the header, a dash
    separator line is dropped, the rest are data rows. A new H2 resets the
    section and clears the entry; a non-entry heading between an entry and
    its table also clears the entry, so only the entry heading that
    immediately frames a table resolves.
    """
    tables: list[tuple[str, tuple[str, str] | None, list[str], list[list[str]]]] = []
    section = ""
    entry: tuple[str, str] | None = None
    lines = doc_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        h2_match = H2_RE.match(line)
        if h2_match:
            section = h2_match.group("title").strip().lower()
            entry = None
        else:
            entry_match = ENTRY_HEADING_RE.match(line)
            if entry_match:
                entry = (
                    entry_match.group("id"),
                    (entry_match.group("title") or "").strip(),
                )
            elif ANY_HEADING_RE.match(line):
                entry = None
        if line.lstrip().startswith("|"):
            block = [line]
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            if len(block) < 2:
                continue
            headers = _split_row(block[0])
            data: list[list[str]] = []
            for row_line in block[1:]:
                cells = _split_row(row_line)
                if _is_separator(cells):
                    continue
                data.append(cells)
            if headers:
                tables.append((section, entry, headers, data))
            entry = None
            continue
        i += 1
    return tables


def _extract_tables(doc_text: str) -> list[tuple[list[str], list[list[str]]]]:
    """(headers, data_rows) pairs from every markdown table, no context."""
    return [(headers, data) for _s, _e, headers, data in _extract_tables_ctx(doc_text)]


def _is_task_table(headers: list[str]) -> bool:
    """True for row tables: an ID (or Branch) column plus a State column,
    but no Feature column. A `Feature` column marks a roll-up table, not a
    task table — the ID column in a roll-up holds feature paths, not task IDs.
    """
    names = _header_names(headers)
    if "feature" in names:
        return False
    return bool(names & ID_HEADERS) and bool(names & STATE_HEADERS)


def _looks_like_rollup_table(headers: list[str]) -> bool:
    """Feature Roll-up: a Feature + State table, with or without an ID column."""
    names = _header_names(headers)
    return "feature" in names and "state" in names


def _is_aspect_detail_table(headers: list[str]) -> bool:
    """aes-docs entry table: ``| Aspect | Detail |`` with label rows."""
    names = _header_names(headers)
    return "aspect" in names and "detail" in names


def _aspect_rows(headers: list[str], data: list[list[str]]) -> dict[str, str]:
    """Map an Aspect|Detail table's row labels (first column) to values."""
    out: dict[str, str] = {}
    for cells in data:
        if not cells:
            continue
        label = cells[0].strip().lower()
        value = cells[1].strip() if len(cells) > 1 else ""
        if label:
            out[label] = value
    return out


def _feature_from_backlog_link(cell: str) -> str:
    """Resolve the feature dir from a Backlog cell's markdown link.

    ``[BACKLOG.md](crates/filesystem/BACKLOG.md)`` → ``crates/filesystem``;
    a link without a feature-directory segment (e.g. root-relative) → ``""``.
    """
    match = MD_LINK_RE.search(cell)
    if not match:
        return ""
    parts = match.group("path").split("/")
    for idx in range(len(parts) - 1):
        if parts[idx] in FEATURE_DIR_MARKERS:
            return f"{parts[idx]}/{parts[idx + 1]}"
    return ""


def parse_doc(
    doc_rel: str,
    text: str,
    feature: str,
    feature_dir: str,
) -> tuple[list[Row], list[str], list[str], list[dict[str, str]], str | None, list[str]]:
    """Parse one spec doc.

    Returns ``(rows, fr_declared, fr_referenced, rollups, doc_state,
    warnings)``. ``rollups`` is a list of ``{"feature", "claimed_state"}``
    dicts — one per roll-up table row — for any Feature/State table found in
    the doc (and one per aes-docs ``Roadmap Status`` PR entry, keyed by its
    Backlog link). ``doc_state`` is the doc-level ``State:`` line value, or
    None. ``warnings`` names malformed table rows (short cells, empty IDs,
    entry-shape problems).

    Two shapes produce entries:

    - Column tables (ID/Branch + State, or Feature + State) — the
      agents-arwaky flat-table dialect.
    - aes-docs entry tables: an ``FR/DS/DT/PR-...`` H2–H4 heading inside
      ``## Backlog Status`` (task row) or ``## Roadmap Status`` (PR entry →
      roll-up claim) followed by an ``| Aspect | Detail |`` table. Entry
      rows carry no ``next_action`` key: the Aspect/Detail shape has no
      Next Action column, so classification falls back to the State row.
    """
    rows: list[Row] = []
    fr_referenced: list[str] = []
    rollups: list[dict[str, str]] = []
    warnings: list[str] = []

    for section, entry, headers, data in _extract_tables_ctx(text):
        if _is_task_table(headers):
            for cells in data:
                if not cells:
                    continue
                row_id = _cell(headers, cells, "ID")
                if not row_id:
                    row_id = _cell(headers, cells, "Branch")
                if len(cells) < len(headers):
                    warnings.append(
                        f"malformed row ({len(cells)} cells, expected {len(headers)}): {doc_rel}"
                    )
                if not row_id:
                    warnings.append(f"row with empty ID/Branch cell: {doc_rel}")
                state = _cell(headers, cells, "State") or "unknown"
                fr_cell = _cell(headers, cells, "FRD Ref")
                fr_refs = sorted(set(FR_ID_RE.findall(fr_cell))) if fr_cell else []
                fr_referenced.extend(fr_refs)
                title = _cell(headers, cells, "Work Item") or _cell(headers, cells, "Item")
                next_action = _cell(headers, cells, "Next Action")
                if not next_action:
                    next_action = _cell(headers, cells, "Item")
                rows.append(
                    {
                        "id": row_id,
                        "title": title,
                        "state": state,
                        "priority": _cell(headers, cells, "Priority") or "—",
                        "health": _cell(headers, cells, "Health") or "—",
                        "fr_refs": fr_refs,
                        "source_doc": doc_rel,
                        "row_text": " | ".join(cells),
                        "next_action": next_action,
                        "feature": feature,
                        "updated": _cell(headers, cells, "Updated") or "",
                    }
                )
        elif _looks_like_rollup_table(headers):
            for cells in data:
                # The ID cell carries the feature path (e.g. "modules/tools");
                # fall back to the Feature cell when the table has no ID column
                # (fixture-style Feature Roll-up tables with only Feature + State).
                feat_cell = _cell(headers, cells, "ID").strip() or _cell(
                    headers, cells, "Feature"
                ).strip()
                if feat_cell:
                    rollups.append(
                        {
                            "feature": feat_cell,
                            "claimed_state": _cell(headers, cells, "State").strip(),
                        }
                    )
        elif entry and section in ENTRY_SECTIONS and _is_aspect_detail_table(headers):
            entry_id, entry_title = entry
            aspects = _aspect_rows(headers, data)
            if section == "roadmap status":
                # A Roadmap Status PR entry is a feature-index claim: the
                # roll-up state comes from its State row, the feature key
                # from the Backlog link (no link → warning, no claim).
                if not entry_id.startswith("PR-"):
                    warnings.append(
                        f"non-PR entry in Roadmap Status: {doc_rel} ({entry_id})"
                    )
                    continue
                rollup_feature = _feature_from_backlog_link(aspects.get("backlog", ""))
                if rollup_feature:
                    rollups.append(
                        {
                            "feature": rollup_feature,
                            "claimed_state": aspects.get("state", "").strip(),
                        }
                    )
                else:
                    warnings.append(
                        f"Roadmap Status entry without a feature Backlog link: "
                        f"{doc_rel} ({entry_id})"
                    )
                continue
            # Backlog Status entry → task row. No next_action key on
            # purpose: the Aspect/Detail shape has no Next Action column.
            state = aspects.get("state", "") or "unknown"
            fr_refs = [entry_id] if entry_id.startswith("FR-") else []
            if fr_refs:
                fr_referenced.append(entry_id)
            aspect_text = " | ".join(
                f"{label}: {value}" for label, value in aspects.items()
            )
            rows.append(
                {
                    "id": entry_id,
                    "title": entry_title,
                    "state": state,
                    "priority": aspects.get("priority", "") or "—",
                    "health": "—",
                    "fr_refs": fr_refs,
                    "source_doc": doc_rel,
                    "row_text": (
                        f"{entry_id}: {entry_title} | {aspect_text}"
                        if entry_title
                        else f"{entry_id} | {aspect_text}"
                    ),
                    "feature": feature,
                    "updated": aspects.get("updated", ""),
                }
            )

    fr_declared = sorted(set(FR_ID_RE.findall(text)))
    match = DOC_STATE_RE.search(text)
    doc_state = match.group("value") if match else None
    return rows, fr_declared, fr_referenced, rollups, doc_state, warnings


def load_discovery(path: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Flatten feature_schema JSON into ``(root_docs, {feature: {dir, docs}})``."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    root_docs = [str(d) for d in payload.get("root", [])]
    features: dict[str, dict[str, Any]] = {}
    for feat in payload.get("features", []):
        name = str(feat.get("name", ""))
        if not name:
            continue
        features[name] = {
            "dir": str(feat.get("dir", "")),
            "docs": [str(d) for d in feat.get("docs", [])],
        }
    return root_docs, features


def run_scan(
    repo_root: str,
    discovery: str,
    out: str | None = None,
    features_filter: list[str] | None = None,
) -> dict[str, Any]:
    """Scan the docs named in discovery; return the ScanOutput dict."""
    started = time.perf_counter()
    root_docs, feature_map = load_discovery(Path(discovery))

    groups: list[tuple[str, str, list[str]]] = []
    if features_filter is None:
        if root_docs:
            groups.append(("root", ".", root_docs))
        for name, spec in feature_map.items():
            groups.append((name, str(spec.get("dir", "")), [str(d) for d in spec.get("docs", [])]))
    else:
        for name in features_filter:
            if name == "root":
                if root_docs:
                    groups.append(("root", ".", root_docs))
            elif name in feature_map:
                spec = feature_map[name]
                groups.append((name, str(spec.get("dir", "")), [str(d) for d in spec.get("docs", [])]))
            else:
                log(f"warning: --features {name} not in discovery JSON; skipping")

    all_rows: list[Row] = []
    fr_declared: list[str] = []
    fr_referenced: list[str] = []
    fr_groups: dict[str, dict[str, list[str]]] = {}
    rollups: list[dict[str, str]] = []
    docs_out: list[ScanDoc] = []
    warnings: list[str] = []
    seen_rows: set[tuple[str, str]] = set()
    docs_scanned = 0

    for name, dir_rel, docs in groups:
        group_declared: list[str] = []
        group_referenced: list[str] = []
        for doc_rel in docs:
            docs_scanned += 1
            doc_path = Path(repo_root) / doc_rel
            try:
                text = doc_path.read_text(encoding="utf-8")
            except OSError:
                warnings.append(f"unreadable doc: {doc_rel}")
                docs_out.append({"doc": doc_rel, "rows": [], "warning": f"unreadable: {doc_rel}"})
                continue
            rows, decl, refs, doc_rollups, _doc_state, doc_warnings = parse_doc(
                doc_rel, text, name, dir_rel
            )
            warnings.extend(doc_warnings)
            fr_declared.extend(decl)
            fr_referenced.extend(refs)
            group_declared.extend(decl)
            group_referenced.extend(refs)
            rollups.extend(doc_rollups)
            kept: list[Row] = []
            for row in rows:
                key = (row["id"], row["source_doc"])
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                kept.append(row)
            all_rows.extend(kept)
            warning: str | None = None
            if not kept:
                # An in-scope doc that contributed no row table (zero-rows
                # case) is named in the per-doc warning; unreadable docs are
                # already handled above.
                warning = f"in-scope zero rows: {doc_rel}"
            docs_out.append({"doc": doc_rel, "rows": kept, "warning": warning})
        fr_groups[name] = {
            "fr_declared": sorted(set(group_declared)),
            "fr_referenced": sorted(set(group_referenced)),
        }

    output: dict[str, Any] = {
        "docs": docs_out,
        "rows": all_rows,
        "fr": {
            "fr_declared": sorted(set(fr_declared)),
            "fr_referenced": sorted(set(fr_referenced)),
        },
        "fr_groups": fr_groups,
        "rollups": rollups,
        "warnings": warnings,
    }
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)
            fh.write("\n")
    else:
        print(json.dumps(output, indent=2))
    elapsed = time.perf_counter() - started
    log(
        f"scanned {docs_scanned} docs, {len(all_rows)} rows, "
        f"{len(groups)} features in {elapsed:.2f} s"
    )
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scan.py")
    parser.add_argument("--repo-root", required=True, help="Absolute path to the AES repo.")
    parser.add_argument("--discovery", required=True, help="Discovery JSON (feature_schema).")
    parser.add_argument("--features", nargs="*", default=None, help="Feature names to scan (default: all).")
    parser.add_argument("--out", default=None, help="Write ScanOutput JSON here; default: stdout.")
    args = parser.parse_args(argv)

    repo_root = str(Path(args.repo_root).resolve())
    run_scan(repo_root, args.discovery, out=args.out, features_filter=args.features)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
