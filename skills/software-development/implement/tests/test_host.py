#!/usr/bin/env python3
"""Tests for scripts/host.py (Linux-only, per-repo scratch_dir).

Run: python3 tests/test_host.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve().parent
_HELPER = _HERE.parent / "scripts" / "host.py"

_spec = importlib.util.spec_from_file_location("implement_host_helper", _HELPER)
assert _spec is not None and _spec.loader is not None, f"Could not load {_HELPER}"
host = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(host)


def _completed_git_toplevel(root: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout=root + "\n", stderr="")


def _completed_git_fail() -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 1, stdout="", stderr="not a git repository")


class TestResolvePython(unittest.TestCase):
    def test_current_interpreter_wins_when_python3(self):
        with mock.patch.object(host.sys, "executable", "/usr/bin/python3.12"):
            self.assertEqual(host.resolve_python(), "/usr/bin/python3.12")

    def test_falls_back_to_which_python3(self):
        with (
            mock.patch.object(host.sys, "executable", ""),
            mock.patch.object(host.shutil, "which", return_value="/usr/bin/python3"),
        ):
            self.assertEqual(host.resolve_python(), "/usr/bin/python3")

    def test_exits_when_no_python3_found(self):
        with (
            mock.patch.object(host.sys, "executable", ""),
            mock.patch.object(host.shutil, "which", return_value=None),
        ):
            with self.assertRaises(SystemExit):
                host.resolve_python()

    def test_linux_platform_guard(self):
        with mock.patch.object(host.os, "name", "nt"):
            with self.assertRaises(SystemExit) as ctx:
                host.resolve_python()
        self.assertIn("Linux only", str(ctx.exception))


class TestRepoSlug(unittest.TestCase):
    def test_slugifies_repo_name(self):
        with mock.patch.object(
            host.subprocess, "run", return_value=_completed_git_toplevel("/home/raka/agents-arwaky")
        ):
            self.assertEqual(host._repo_slug(), "agents-arwaky")

    def test_not_inside_git_repository(self):
        with mock.patch.object(host.subprocess, "run", return_value=_completed_git_fail()):
            with self.assertRaises(SystemExit) as ctx:
                host._repo_slug()
        self.assertIn("not inside a git repository", str(ctx.exception))

    def test_slug_must_not_be_empty(self):
        with mock.patch.object(
            host.subprocess, "run", return_value=_completed_git_toplevel("/home/raka/--")
        ):
            with self.assertRaises(SystemExit) as ctx:
                host._repo_slug()
        self.assertIn("could not derive project repo name", str(ctx.exception))


class TestScratchDir(unittest.TestCase):
    def test_under_grok_plans_with_repo_slug(self):
        with mock.patch.object(host, "_repo_slug", return_value="agents-arwaky"):
            path = host.scratch_dir()
        self.assertEqual(path, Path.home() / ".grok" / "plans" / "agents-arwaky")
        self.assertTrue(path.is_dir())


class TestSetupPayload(unittest.TestCase):
    def test_setup_payload_keys_and_run_id(self):
        with (
            mock.patch.object(host.subprocess, "run", return_value=_completed_git_toplevel("/home/raka/agents-arwaky")),
            mock.patch.object(host.sys, "executable", "/usr/bin/python3"),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = host.cmd_setup(mock.Mock())
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(sorted(payload), ["python", "run_id", "scratch_dir"])
        self.assertEqual(len(payload["run_id"]), 8)
        self.assertEqual(
            Path(payload["scratch_dir"]),
            Path.home() / ".grok" / "plans" / "agents-arwaky",
        )


class TestCleanup(unittest.TestCase):
    def test_missing_paths_are_ok(self):
        rc = host.cmd_cleanup(mock.Mock(paths=["/nonexistent/path-xyz"]))
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
