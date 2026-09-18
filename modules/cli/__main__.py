"""``python3 -m modules.cli`` bridge — delegates to the root CLI entry point.

The ``aa`` launcher runs ``python3 -m modules.cli "$@"``. The composition-root
entry lives at ``modules.root_cli_entry`` (root layer); this surface shim only
forwards argv so the launcher keeps working without a static root->surface edge.
"""
from __future__ import annotations

import sys

from modules.root_cli_entry import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))