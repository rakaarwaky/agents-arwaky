"""Unit test: generated bash completion harus valid (P5-P2)."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/completion"))

import completion


def test_bash_syntax():
    script = completion.generate_bash()
    result = subprocess.run(
        ["bash", "-n"], input=script, capture_output=True, text=True
    )
    assert result.returncode == 0, f"bash -n failed: {result.stderr}"


if __name__ == "__main__":
    test_bash_syntax()
    print("test_completion.py: ALL PASSED")
