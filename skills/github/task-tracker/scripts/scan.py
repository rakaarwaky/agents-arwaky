"""Parse AES spec docs into ScanOutput JSON.

Stdlib only. Reads the discovery JSON (the Rhai ``feature_schema`` object
verbatim: ``{"root": [...], "features": [{"name", "dir", "docs"}]}``), reads
the listed spec docs, and emits an object matching the task-tracker Rhai
workflow's ``scan_schema`` (``rows`` / ``fr`` / ``rollup_row``) plus
per-doc ``docs`` bookkeeping (rows, and a ``warning`` field naming a doc
that was unreadable or had in-scope zero rows).

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

FR_ID_RE = re.compile(r"\bFR-[A-Z]+-\d+\b")
# Doc-level "State: <value>" line near the top of a feature backlog.
DOC_STATE_RE = re.compile(r"^State:\s*(?P<value>\S.*?)\s*$", re.MULTILINE)
SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")

# Table headers that mark a row table (ID / Branch + State).
ID_HEADERS = {"id", "branch"}
STATE_HEADERS = {"state", "doc_state"}

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
    return bool(cells) and all(SEPARATOR_CELL_RE.match(c) for c in cells if c)


def _header_names(headers: list[str]) -> set[str]:
    return {h.strip().lower().replace(" ", "_") for h in headers}


def _cell(headers: list[str], cells: list[str], name: str) -> str:
    target = name.strip().lower().replace(" ", "_")
    for idx, header in enumerate(headers):
        if idx < len(cells) and header.strip().lower().replace(" ", "_") == target:
            return cells[idx]
    return ""


def _extract_tables(doc_text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Extract (headers, data_rows) pairs from every markdown table.

    A table is a consecutive run of lines starting with ``|``. The first
    line is the header; a dash separator line is dropped; the rest are data
    rows.
    """
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = doc_text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            block = [lines[i]]
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
                tables.append((headers, data))
            continue
        i += 1
    return tables


def _is_task_table(headers: list[str]) -> bool:
    """True for row tables: an ID (or Branch) column plus a State column.

    A `Feature` header alone is NOT enough: Feature Roll-up tables carry a
    `Feature` column plus `State` but no `ID`, so they must be routed to
    roll-up extraction instead.
    """
    names = _header_names(headers)
    return (bool(names & {"id", "branch"}) or "id" in names) and bool(names & STATE_HEADERS)


def _looks_like_rollup_table(headers: list[str]) -> bool:
    """Feature Roll-up: a Feature + State table with no ID column."""
    names = _header_names(headers)
    return "feature" in names and "state" in names and "id" not in names


def parse_doc(
    doc_rel: str,
    text: str,
    feature: str,
    feature_dir: str,
) -> tuple[list[Row], list[str], list[str], str | None, str | None]:
    """Parse one spec doc.

    Returns ``(rows, fr_declared, fr_referenced, rollup_row, doc_state)``.
    ``rollup_row`` is this feature's verbatim roll-up row text, or None when
    the doc carries no Feature Roll-up table for it. ``doc_state`` is the
    doc-level ``State:`` line value, or None.
    """
    rows: list[Row] = []
    fr_referenced: list[str] = []
    rollup_row: str | None = None
    dir_norm = feature_dir.strip().lower()

    for headers, data in _extract_tables(text):
        if _is_task_table(headers):
            for cells in data:
                if not cells:
                    continue
                row_id = _cell(headers, cells, "ID")
                if not row_id:
                    row_id = _cell(headers, cells, "Branch")
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
                feat_cell = _cell(headers, cells, "Feature").strip()
                if feat_cell.lower() == dir_norm:
                    rollup_row = " | ".join(cells)

    fr_declared = sorted(set(FR_ID_RE.findall(text)))
    match = DOC_STATE_RE.search(text)
    doc_state = match.group("value") if match else None
    return rows, fr_declared, fr_referenced, rollup_row, doc_state


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
    rollup_row: str | None = None
    docs_out: list[ScanDoc] = []
    warnings: list[str] = []
    seen_rows: set[tuple[str, str]] = set()
    docs_scanned = 0

    for name, dir_rel, docs in groups:
        group_rollup: str | None = None
        for doc_rel in docs:
            docs_scanned += 1
            doc_path = Path(repo_root) / doc_rel
            try:
                text = doc_path.read_text(encoding="utf-8")
            except OSError:
                warnings.append(f"unreadable doc: {doc_rel}")
                docs_out.append({"doc": doc_rel, "rows": [], "warning": f"unreadable: {doc_rel}"})
                continue
            rows, decl, refs, rollup, _doc_state = parse_doc(doc_rel, text, name, dir_rel)
            fr_declared.extend(decl)
            fr_referenced.extend(refs)
            if rollup is not None and group_rollup is None:
                group_rollup = rollup
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
        if group_rollup is not None:
            rollup_row = group_rollup

    output: dict[str, Any] = {
        "docs": docs_out,
        "rows": all_rows,
        "fr": {
            "fr_declared": sorted(set(fr_declared)),
            "fr_referenced": sorted(set(fr_referenced)),
        },
        "rollup_row": rollup_row or "",
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
