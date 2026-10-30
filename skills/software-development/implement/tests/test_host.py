#!/usr/bin/env python3
"""Tests for scripts/host.py.

Run: python3 tests/test_host.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import tempfile
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

_STUB = r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe"
_REAL = r"C:\Python312\python.exe"
_LAUNCHER = r"C:\Windows\py.exe"


def _which_only(name_to_path: dict[str, str]):
    return lambda name: name_to_path.get(name)


class TestResolvePython(unittest.TestCase):
    def test_py_launcher_returns_real_interpreter_not_launcher(self):
        completed = subprocess.CompletedProcess([], 0, stdout=_REAL + "\n", stderr="")
        with (
            mock.patch.object(host.sys, "executable", _STUB),
            mock.patch.object(host.shutil, "which", _which_only({"py": _LAUNCHER})),
            mock.patch.object(host.subprocess, "run", return_value=completed) as run,
        ):
            self.assertEqual(host.resolve_python(), _REAL)
        argv = run.call_args.args[0]
        self.assertEqual(argv[0], _LAUNCHER)
        self.assertIn("-3", argv)

    def test_stub_reported_by_launcher_is_rejected(self):
        completed = subprocess.CompletedProcess([], 0, stdout=_STUB + "\n", stderr="")
        with (
            mock.patch.object(host.sys, "executable", _STUB),
            mock.patch.object(host.shutil, "which", _which_only({"py": _LAUNCHER})),
            mock.patch.object(host.subprocess, "run", return_value=completed),
        ):
            with self.assertRaises(SystemExit):
                host.resolve_python()

    def test_failing_launcher_is_skipped_for_next_candidate(self):
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="no 3")
        with (
            mock.patch.object(host.sys, "executable", _STUB),
            mock.patch.object(
                host.shutil,
                "which",
                _which_only({"py": _LAUNCHER, "python3": r"C:\Python312\python3.exe"}),
            ),
            mock.patch.object(host.subprocess, "run", return_value=failed),
        ):
            self.assertEqual(host.resolve_python(), r"C:\Python312\python3.exe")

    def test_good_current_interpreter_wins(self):
        with mock.patch.object(host.sys, "executable", _REAL):
            self.assertEqual(host.resolve_python(), _REAL)


class TestSetupPayload(unittest.TestCase):
    def test_setup_reports_state_dir_and_run_id(self):
        with tempfile.TemporaryDirectory() as home:
            with mock.patch.dict(os.environ, {"HOME": home, "USERPROFILE": home}):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = host.cmd_setup(mock.Mock())
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(
            sorted(payload), ["python", "run_id", "scratch_dir", "state_dir"]
        )
        self.assertEqual(len(payload["run_id"]), 8)
        self.assertTrue(payload["state_dir"].endswith("implement-state"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
