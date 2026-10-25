"""Shared constants, types, and helpers for task-tracker scripts.

Stdlib only. Shared by scan.py, classify.py, and (later) validate.py /
cache.py / ledger.py.
"""

from __future__ import annotations

import json
import subprocess
from typing import NamedTuple, TypedDict

# gh CLI invocations never block a run longer than this.
GH_TIMEOUT = 30


class GhRateLimited(Exception):
    """gh returned 403/429 with a retryable rate-limit header."""


class GhAuthError(Exception):
    """gh returned a permanent auth failure (401, bad token)."""


def gh(*args: str, timeout: int = GH_TIMEOUT) -> str:
    """Run the gh CLI; return trimmed stdout on success.

    Propagates gh's stderr into the raised exception. Raise GhRateLimited
    on 403/429, GhAuthError on 401, and RuntimeError for any other
    non-zero exit.
    """
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode == 429 or "rate limit" in stderr.lower() or "403" in stderr:
        raise GhRateLimited(f"gh {' '.join(args)}: {stderr}")
    if "401" in stderr or "auth" in stderr.lower():
        raise GhAuthError(f"gh {' '.join(args)}: {stderr}")
    raise RuntimeError(f"gh {' '.join(args)} exited {proc.returncode}: {stderr}")


class ScanRow(TypedDict, total=False):
    """One parsed table row (scan_schema.row shape)."""

    id: str
    title: str
    state: str
    priority: str
    health: str
    fr_refs: list[str]
    source_doc: str
    row_text: str
    next_action: str


class FrSets(TypedDict, total=False):
    """Per-group FR-id declared / referenced sets."""

    fr_declared: list[str]
    fr_referenced: list[str]


class ScanDoc(TypedDict):
    """Per-document slice of the scan output."""

    doc: str
    rows: list[ScanRow]
    warning: str | None


class ScanOutput(TypedDict, total=False):
    """Top-level scan.py output."""

    docs: list[ScanDoc]
    rows: list[ScanRow]
    fr: FrSets
    rollup_row: str
    warnings: list[str]


class FeatureGroup(NamedTuple):
    """A discovery group: a feature dir or the repo-root group."""

    name: str
    dir: str
    docs: list[str]


def load_json(path: str) -> object:
    """Load a JSON document from a repo-relative or absolute path."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def emit_json(payload: object, out: str | None) -> None:
    """Write payload as JSON to out, or to stdout when out is None."""
    text = json.dumps(payload, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)


def log(msg: str) -> None:
    """Emit an observability line to stderr with the script prefix."""
    import sys

    print(f"[task-tracker] {msg}", file=sys.stderr)
