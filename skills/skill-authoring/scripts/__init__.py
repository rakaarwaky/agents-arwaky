"""Importable skill-library script package.

Modules:
- ``model`` — tree walking, frontmatter parsing, dataclasses
- ``validate`` — the 13 issue checks, emitting byte-identical messages
- ``cli`` — path-invocable CLI entrypoint

Import this package by path, not by name: the pack directory
(``skill-authoring``) contains a hyphen and is not a valid ``python3 -m``
target, so the canonical invocation is ``python3 skills/skill-authoring/
scripts/cli.py validate``.

In-process host constraint: importing this package (or any module in it)
inserts the pack's ``_rules/`` and ``scripts/`` directories on
``sys.path`` and leaves them there for the life of the process. A host
that imports the pack in-process must therefore not define top-level
modules named ``model``, ``validate``, or ``cli`` (they would be shadowed
by, or shadow, the pack's modules) and must not rely on ``sys.path``
being unchanged across the import.
"""
