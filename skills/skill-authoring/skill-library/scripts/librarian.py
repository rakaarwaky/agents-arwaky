#!/usr/bin/env python3
"""Back-compat shim: delegate to the pack script package's CLI.

The implementation moved to ``skill-authoring/scripts/`` (pack-shared
code must not live inside one skill — design §5.2 Alternative C). This
file stays so every existing ``librarian.py <subcommand>`` invocation
keeps working: it puts the pack's ``scripts/`` directory on ``sys.path``
and hands the argument vector to ``cli.main()``.

Stack the sibling-pack dir, not the whole pack root: the modules import
each other by bare name (``model``, ``catalog``, ``cli``), and the
scripts dir is exactly where they live.

New code should invoke the canonical path directly::

    python3 skills/skill-authoring/scripts/cli.py <subcommand>
"""

from __future__ import annotations

import sys
from pathlib import Path

#: This file is <pack>/skill-library/scripts/librarian.py, so the pack
#: root is two levels up and its script package sits at ``scripts/``.
_PACK_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_PACK_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_PACK_SCRIPTS))

from cli import main

if __name__ == "__main__":
    sys.exit(main())
