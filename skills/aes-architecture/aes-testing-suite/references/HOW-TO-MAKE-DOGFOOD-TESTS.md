# HOW TO MAKE DOGFOOD / INTEGRATION PIPELINE TESTS

> **Purpose**: Add real end-to-end validation tests that exercise actual CLI commands against a live service/session.
>
> **Audience**: Agents and engineers adding integration coverage for user-facing pipelines.
>
> **Scope**: Integration test files that run the CLI with real sessions or external services.
>
> **Location**: Project's integration test directory (commonly `tests/integration/` or `tests/e2e/`).
>
> **Length**: One file per pipeline type; skip gracefully when required services are unavailable.

---

## Rules

### Placement rules

**Allowed:** Integration test files in the project's designated integration test directory.
**Forbidden:** Browser automation in unit tests; tests requiring credentials in CI without skip logic.

### Naming rules

Pattern: `integration_<feature>.py` (Python), `integration_<feature>.rs` (Rust), `integration_<feature>.ts` (TypeScript).
Prefix with `integration_` to distinguish from unit tests.

### Skip logic rules

- **Always provide graceful skip** when external dependencies are unavailable.
- Check for required credentials, sessions, or services before running.
- Use `pytestmark = pytest.mark.skipif()` (Python) or equivalent in other languages.
- CI should never fail because a local session/credential is missing.

### Test structure rules

- **Structure tests first**: Verify command exists/discoverable without external deps.
- **Functional tests second**: Run actual pipeline with mocked/real inputs.
- **One assertion per test**: Clear failure messages.
- **Cleanup fixtures**: Remove temporary files after tests.

---

## Workflow

### Step 1: Identify the pipeline

Which CLI command or service interaction needs validation?

| Pipeline Type | Description | Example |
|---------------|-------------|---------|
| Direct text | Simple command with text input | `cmd --input "text"` |
| File-based | Command reading from file | `cmd --file input.txt` |
| Attachment | Command with file attachment | `cmd --file input.txt --attach doc.pdf` |
| Authenticated | Command requiring login/session | `cmd --session <session>` |
| Batch/Swarm | Multiple concurrent operations | `cmd --batch files/` |

### Step 2: Create test file structure

```python
"""Integration tests for <feature> — real end-to-end validation."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
import pytest

# ─── Skip Logic ───────────────────────────────────────────────────────────────

def _has_required_service() -> bool:
    """Check if required external service/session is available."""
    # Implementation depends on your project
    # Example: check for credential file, session token, etc.
    return False  # Return True when service is available

pytestmark = pytest.mark.skipif(
    not _has_required_service(),
    reason="Skip: Required service/session not available",
)

# ─── CLI Runner ───────────────────────────────────────────────────────────────

def _run_cli(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run CLI command and return result."""
    return subprocess.run(
        [sys.executable, "-m", "<module_path>"] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_files(tmp_path_factory):
    """Create temporary test files, cleanup after."""
    test_dir = tmp_path_factory.mktemp("integration_tests")
    input_file = test_dir / "input.txt"
    input_file.write_text("# Test Input\n\nPlease process this.\n")
    yield {"input": input_file}
    # Cleanup happens automatically with tmp_path

# ─── Tests ────────────────────────────────────────────────────────────────────

class Test<Pipeline>Structure:
    """Tests that verify command discoverability (no external deps needed)."""

    def test_<command>_exists(self):
        result = _run_cli(["--help"])
        assert result.returncode == 0
        assert "<command>" in result.stdout

class Test<Pipeline>Functional:
    """Tests that run actual pipelines (requires external service)."""

    def test_<scenario>(self, test_files):
        result = _run_cli(["<command>", "-i", str(test_files["input"])])
        assert result.returncode in (0, 1), f"CLI error: {result.stderr[:500]}"
        print(f"\n[OUTPUT] {result.stdout[:200]}")
```

### Step 3: Implement skip logic

Determine what external dependency your tests need and how to check for it:

```python
def _has_valid_session() -> bool:
    """Check for valid authentication session."""
    session_dir = Path.home() / ".config" / "<app>" / "session"
    if not session_dir.exists():
        return False
    return (session_dir / "token.json").exists()

def _has_credential_file() -> bool:
    """Check for credential configuration."""
    return Path("~/.config/<app>/credentials.toml").expanduser().exists()
```

### Step 4: Add structure tests (always run)

Structure tests verify commands are discoverable — these don't need external services:

```python
class TestCommandStructure:
    def test_help_returns_zero(self):
        result = _run_cli(["--help"])
        assert result.returncode == 0

    def test_command_exists(self):
        result = _run_cli(["--help"])
        assert "<command-name>" in result.stdout
```

### Step 5: Create test fixtures

```python
@pytest.fixture
def sample_input(tmp_path):
    """Create sample input file for testing."""
    input_file = tmp_path / "input.md"
    input_file.write_text("# Sample\n\nTest content here.\n")
    return input_file

@pytest.fixture
def sample_attachment(tmp_path):
    """Create sample attachment file."""
    attachment = tmp_path / "attachment.txt"
    attachment.write_text("This is test attachment content.\n")
    return attachment
```

### Step 6: Run and verify

```bash
# Run all integration tests (skips if dependencies missing)
pytest tests/integration/ -v

# Run only structure tests (no dependencies needed)
pytest tests/integration/ -k Structure -v

# Run with verbose output
pytest tests/integration/ -v --tb=short
```

---

## Template

### Complete integration test structure

```python
"""Integration tests for <feature-name> — real end-to-end validation.

These tests exercise actual CLI commands against live services.
They skip gracefully when required dependencies are unavailable.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest


# ─── Configuration ────────────────────────────────────────────────────────────

REQUIRED_SERVICE_CHECK = lambda: Path.home().joinpath(".config", "<app>").exists()
CLI_MODULE = "<package>.<entry_point>"


# ─── Skip Logic ───────────────────────────────────────────────────────────────

def _service_available() -> bool:
    """Check if required external service is available."""
    return REQUIRED_SERVICE_CHECK()


pytestmark = pytest.mark.skipif(
    not _service_available(),
    reason="Skip: Required service not available",
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _run_cli(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run CLI and return result."""
    return subprocess.run(
        [sys.executable, "-m", CLI_MODULE] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_input(tmp_path: Path) -> Path:
    """Create temporary sample input file."""
    f = tmp_path / "input.txt"
    f.write_text("# Test Input\n\nPlease process.\n")
    return f


# ─── Structure Tests ──────────────────────────────────────────────────────────

class TestCommandStructure:
    """Verify command discoverability (no external deps)."""

    def test_help_succeeds(self):
        result = _run_cli(["--help"])
        assert result.returncode == 0

    def test_command_in_help(self):
        result = _run_cli(["--help"])
        assert "<command-name>" in result.stdout


# ─── Functional Tests ─────────────────────────────────────────────────────────

class Test<Pipeline>Functional:
    """Run actual pipeline (requires service)."""

    def test_pipeline_runs(self, sample_input: Path):
        result = _run_cli([
            "<command>",
            "-i", str(sample_input),
        ])
        assert result.returncode in (0, 1), f"CLI error: {result.stderr[:500]}"
        print(f"\n[OUTPUT] {result.stdout[:200]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Section Contract

| Section | Why it belongs here |
| ------- | ------------------- |
| Skip logic with `pytestmark` | Prevents CI failures when external deps unavailable |
| `_run_cli()` helper | Standardizes invocation across all tests |
| Structure tests | Verify discoverability without external deps |
| Functional tests | Validate actual behavior with real service |
| Fixtures | Provide reusable test data with cleanup |

---

## Verify

```bash
# Run integration tests (skips if dependencies missing)
pytest tests/integration/ -v

# Run only structure tests (no dependencies)
pytest tests/integration/ -k Structure -v

# Full suite
pytest tests/ -q
```

### Manual checks

- [ ] Tests skip gracefully when service unavailable
- [ ] Structure tests pass without external deps
- [ ] Functional tests run with valid session
- [ ] Exit codes handled correctly (0 = success, 1 = expected error)
- [ ] Fixtures cleaned up after tests

### Fallback compile gate

```bash
python -c "from tests.integration.test_<feature> import _run_cli; print('ok')"
python -c "from tests.integration.test_<feature> import _service_available; print(_service_available())"
```
