"""Bootstrap entry for blender-mcp CLI."""

import sys


def main() -> None:
    """Entry point for the blender-mcp CLI."""
    from surfaces.cli_command_handler import CliCommandHandler

    sys.exit(CliCommandHandler.main())


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
