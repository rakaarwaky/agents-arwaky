#!/usr/bin/env python3
"""Report angle brackets in Markdown that sit outside code, not just in prose.

Editors and lint adapters classify a Markdown file as HTML/JSX/MDX when it
contains a bare `<...>` sequence that is not inside a fenced block or an inline
code span. The usual culprits are Rust/TypeScript generics written without
backticks, and bare comparison operators such as `under < 1s`.

Usage:
    python3 find_bare_angle_brackets.py FILE [FILE ...]
    python3 find_bare_angle_brackets.py --quiet DIR      # only exit status

Exit status:
    0  no bare angle brackets found
    1  at least one found (the report explains where)
    2  bad usage

Fenced code blocks are skipped: their contents never trigger the classifier, and
the closing-fence column is printed instead so a stray fence is still visible.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
CODE_SPAN_RE = re.compile(r"(`+).*?\1", re.DOTALL)
BRACKET_RE = re.compile(r"<[^<>\n]*>?")
MD_SUFFIXES = (".md", ".markdown", ".mdx")


def scan(text: str) -> tuple[list[tuple[int, int, str]], list[tuple[int, int, str]]]:
    """Return (findings, fence_notes) for one document.

    findings: (line, column, matched_text) for bare angle brackets.
    fence_notes: (line, column, text) for lines that open or close a fence.
    """
    findings: list[tuple[int, int, str]] = []
    fence_notes: list[tuple[int, int, str]] = []
    fence: str | None = None

    for lineno, line in enumerate(text.splitlines(), start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            fence_notes.append((lineno, len(line) - len(line.lstrip()) + 1, marker))
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is not None:
            continue

        # Column numbers refer to the original line, not the stripped copy.
        offset = 0
        for span in CODE_SPAN_RE.finditer(line):
            before = line[offset : span.start()]
            for hit in BRACKET_RE.finditer(before):
                findings.append((lineno, offset + hit.start() + 1, hit.group(0)))
            offset = span.end()
        for hit in BRACKET_RE.finditer(line[offset:]):
            findings.append((lineno, offset + hit.start() + 1, hit.group(0)))

    return findings, fence_notes


def iter_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            files.extend(
                sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in MD_SUFFIXES)
            )
        elif path.is_file():
            files.append(path)
        else:
            print(f"error: no such file or directory: {target}", file=sys.stderr)
            raise SystemExit(2)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("targets", nargs="+", help="Markdown files or directories")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the per-hit report; rely on the exit status only",
    )
    args = parser.parse_args()

    total = 0
    for path in iter_files(args.targets):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"skip (not utf-8): {path}", file=sys.stderr)
            continue
        except OSError as exc:
            print(f"skip ({exc.strerror}): {path}", file=sys.stderr)
            continue

        findings, fences = scan(text)
        if not findings:
            continue
        total += len(findings)
        if args.quiet:
            continue

        for lineno, column, hit in findings:
            print(f"{path}:{lineno}:{column}: bare angle bracket {hit!r}")
        for lineno, column, marker in fences:
            print(f"{path}:{lineno}:{column}: code fence {marker} (contents skipped)")

    if not args.quiet:
        if total:
            print(
                f"\n{total} bare angle bracket(s). Wrap each in backticks, "
                f"or rewrite it as prose."
            )
        else:
            print("clean: no bare angle brackets outside code.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
