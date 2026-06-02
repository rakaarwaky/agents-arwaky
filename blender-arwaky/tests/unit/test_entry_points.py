"""Tests for entry point modules (cli_main_entry, mcp_main_entry, src/__init__)."""
import pytest
from unittest.mock import patch, MagicMock
import surfaces.cli_command_handler
import surfaces.server_start_handler


class TestCliMainEntry:
    """Tests for cli_main_entry.py."""

    def test_main_dispatch(self):
        with patch("surfaces.cli_command_handler.CliCommandHandler.main", return_value=0) as mock_main, \
             patch("sys.exit") as mock_exit:
            from cli_main_entry import main
            main()
            mock_main.assert_called_once()
            mock_exit.assert_called_once_with(0)

    def test_main_exit_code(self):
        with patch("surfaces.cli_command_handler.CliCommandHandler.main", return_value=1) as mock_main, \
             patch("sys.exit") as mock_exit:
            from cli_main_entry import main
            main()
            mock_exit.assert_called_once_with(1)

    def test_main_is_callable(self):
        from cli_main_entry import main
        assert callable(main)


class TestMcpMainEntry:
    """Tests for mcp_main_entry.py."""

    def test_main_dispatch(self):
        with patch("surfaces.server_start_handler.ServerStartHandler.main") as mock_main:
            from mcp_main_entry import main
            main()
            mock_main.assert_called_once()

    def test_main_is_callable(self):
        from mcp_main_entry import main
        assert callable(main)


class TestSrcInit:
    """Tests for src/__init__.py."""

    def test_imports_resolve(self):
        import src
        assert hasattr(src, "cli_main")
        assert hasattr(src, "mcp_main")
        assert callable(src.cli_main)
        assert callable(src.mcp_main)

    def test_all_exports(self):
        import src
        assert "cli_main" in src.__all__
        assert "mcp_main" in src.__all__
