"""Run the agents-arwaky CLI: ``python3 -m modules.cli``."""
import sys

from modules.cli.src.root_cli_entry import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
