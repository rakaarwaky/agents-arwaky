# BlenderMCP — Testing Guide

## Quick Start

```bash
cd /home/raka/mcp-servers/blender-mcp
uv run pytest
```

All tests run via `pytest` with coverage reporting. Configuration in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov=blender_mcp_addon --cov-report=term --cov-report=html --cov-report=xml
markers =
    unit: Pure logic tests, no external dependencies
    integration: Layer interaction tests with real DI, mocked I/O
    functional: End-to-end command flows within project boundaries
    addon: Blender addon tests using bpy mock (tests/addon/)
    slow: Tests that take >1s to run
```

---

Tests are organized by type (Unit, Integration, Functional, Addon):

```
tests/
  unit/           # Pure logic, data models, and mocked interfaces
  integration/    # Layer interactions, DI wiring, and service integration
  functional/     # End-to-end command flows within project boundaries
  addon/          # blender addon test 
```

---

## Coverage Targets

| Layer                  | Target        | Notes                              |
| ---------------------- | ------------- | ---------------------------------- |
| `taxonomy/`          | 100%          | Pure data — must be fully covered |
| `contract/`          | 90%           | Interface definitions              |
| `infrastructure/`    | 80%           | Adapters + API clients             |
| `capabilities/`      | 90%           | Business logic                     |
| `agent/`             | 80%           | Orchestration                      |
| `surfaces/`          | 85%           | Handlers                           |
| `blender_mcp_addon/` | 70%           | Blender-specific (harder to mock)  |
| **Overall**      | **85%** | minimum                            |

---

## Running Tests

### Full suite with coverage

```bash
uv run pytest
```

### Specific test file

```bash
uv run pytest tests/unit/test_command_catalog.py -v
```

### Specific test function

```bash
uv run pytest tests/integration/test_tool_registry.py::test_register_tools -v
```

### With verbose output

```bash
uv run pytest -v --tb=short
```

### Exclude slow tests

```bash
uv run pytest -m "not slow"
```

### Run only integration tests (need Blender)

```bash
uv run pytest -m "integration"
```

### Run only addon tests

```bash
uv run pytest tests/addon/ -v
```

### Run addon tests tanpa coverage overhead

```bash
uv run pytest tests/addon/ -v --no-cov
```

### Run berdasarkan marker

```bash
uv run pytest -m unit       # hanya unit tests
uv run pytest -m addon      # hanya addon tests
uv run pytest -m "not slow" # skip slow tests
```

---

## Test Categories

### Unit Tests (`pytest -m unit`)

- Pure functions, data models, value objects
- No external dependencies (mocked)
- Fast: <10ms per test
- Examples: catalog parsing, config loading, serialization

### Integration Tests (`pytest -m integration`)

- Layer interactions: handler → capability → infrastructure
- Mock API calls, real DI container
- Medium: <500ms per test
- Examples: execute_command flow, DI wiring, socket message parsing

### Functional Tests (`pytest -m functional`)

- End-to-end within boundaries (no external services)
- Full command execution pipeline
- Slower: <2s per test
- Examples: create_primitive → scene update cycle

### Blender Addon Tests (`pytest -m addon`)

- Test Blender-specific logic dengan **mock `bpy`** — tidak perlu Blender terpasang
- `tests/addon/conftest.py` meng-inject mock `bpy` dan `mathutils` ke `sys.modules` sebelum import apapun
- Examples: server start/stop, operator registration, UI rendering

**File test addon yang tersedia:**

| File                   | Module yang Ditest                                                          |
| ---------------------- | --------------------------------------------------------------------------- |
| `test_config.py`     | `blender_mcp_addon/config.py` — env-var overrides, built-in defaults     |
| `test_utils.py`      | `blender_mcp_addon/utils.py` — AABB, screenshot, GLB import              |
| `test_properties.py` | `blender_mcp_addon/properties.py` — register/unregister, inject_env_vars |
| `test_operators.py`  | `blender_mcp_addon/operators.py` — start/stop server operators           |
| `test_server.py`     | `blender_mcp_addon/server.py` — BlenderMCPServer lifecycle & dispatch    |
| `test_ui.py`         | `blender_mcp_addon/ui.py` — Panel, AddonPreferences draw                 |
| `test_init.py`       | `blender_mcp_addon/__init__.py` — register, unregister, _auto_start      |

**Cara kerja mock bpy (`tests/addon/conftest.py`):**

```python
# conftest.py otomatis dijalankan pytest sebelum test
# Meng-inject mock ke sys.modules agar import bpy tidak error:
sys.modules['bpy'] = MockBpy
sys.modules['bpy.types'] = MockBpy.types
sys.modules['bpy.props'] = MockBpy.props
sys.modules['bpy.app'] = MockBpy.app
sys.modules['bpy.utils'] = MockBpy.utils
sys.modules['mathutils'] = MockMathutils
```

---

## Manual End-to-End Test

### Prerequisites

1. Blender running with addon enabled (server on port 9876)
2. MCP server started: `uv run python -m surfaces.mcp_server_entry`

### Test Steps

**Step 1: Health Check**

```python
# Use health_check tool
health_check()
# Expect: blender_connected=true, tool_count=5
```

**Step 2: Scene Discovery**

```python
execute_command(action="get_scene_info")
# Expect: JSON with scene_name, object_count, frame info
```

**Step 3: Create Object**

```python
execute_command(
    action="create_primitive",
    args={"type": "sphere", "radius": 2.0}
)
# Expect: success message with object name
```

**Step 4: Execute Code**

```python
execute_command(
    action="execute_blender_code",
    args={"code": "import bpy; print(bpy.data.objects.keys())"}
)
# Expect: JSON output with object names
```

---

## CI/CD Integration

The project uses a self-hosted linter (`auto-lint`) for architecture compliance.

```bash
# Run linter
auto-lint check /home/raka/mcp-servers/blender-mcp

# Run tests with coverage
uv run pytest --cov=src --cov=blender_mcp_addon --cov-report=term

# Check ruff
uv run ruff check src/ blender_mcp_addon/

# Check mypy
uv run mypy src/
```

---

## Common Test Failures

### ImportError: circular import

**Cause:** Module imports from barrel (`__init__.py`) that imports back.
**Fix:** Import directly from source file, not from barrel.

### Blender connection tests fail

**Cause:** No Blender running with addon.
**Fix:** Mark with `@pytest.mark.integration` and skip if no Blender.

### Coverage drops

**Cause:** New code without tests.
**Fix:** Write tests for new code before merging. Run `--cov-report=html`
and open `htmlcov/index.html` to see uncovered lines.

---

## Writing New Tests

1. Add test file in `tests/unit/`, `tests/integration/`,  `tests/functional/` `tests/addon/` matching source path
2. Use `test_` prefix for function/file names
3. Mock external dependencies (API calls, Blender socket)
4. Add to appropriate `@pytest.mark` category
5. Verify coverage: `uv run pytest --cov=<module> tests/`

**Template:**

```python
"""Tests for <module_name>."""
import pytest


def test_<function_name>():
    """<description of what's being tested>."""
    # Arrange
    # Act
    # Assert
```
