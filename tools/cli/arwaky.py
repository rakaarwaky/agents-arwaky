#!/usr/bin/env python3
"""agents-arwaky Unified Tool Orchestrator — thin entry launcher.

Delegates all subcommand routing to the AES 7-layer modules under
``modules/``. This file exists only so the ``~/.local/bin/aa`` launcher
keeps working without modification.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so ``modules.*`` is importable.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.cli.src.root_cli_entry import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
