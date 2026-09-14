---
name: lint-arwaky
description: Architecture Enforcement System (AES) linter for Rust, Python, and TypeScript codebases.
version: 3.6.1
---

# Lint Arwaky (AES Architecture Linter)

Lint Arwaky is a high-speed Rust-based architecture enforcement engine. Structured under the Agentic Engineering System (AES) specification, it enforces layer boundaries, naming conventions, import directions, and role boundaries across Rust, Python, and TypeScript codebases.

## When to Use This Skill

Activate this skill when:
- Creating, modifying, or refactoring files in AES-governed repositories.
- Verifying layer boundaries and dependency rules before submitting pull requests.
- Diagnosing architecture violations, orphan files, or illegal upward/circular imports.
- Running automated CI quality gates or architecture health checks.

## AES 7-Layer Hierarchy & Naming Contract

Every source file must follow the convention:
`<layer>_<concern>_<role>.<ext>`

The 7 strictly-ordered layers (from top to bottom) are:
1. **`root`**: Top-level entry points and public APIs (`root_main_entry.py`)
2. **`surface`**: External exposure adapters like CLI, MCP, REST, GUI (`surface_cli_adapter.py`)
3. **`contract`**: Interfaces, schemas, DTOs, data protocols (`contract_payload_model.py`)
4. **`capabilities`**: Domain logic, orchestration, and business rules (`capabilities_task_executor.py`)
5. **`taxonomy`**: Types, enums, constants, entity classifications (`taxonomy_status_type.py`)
6. **`utility`**: Pure helpers, formatting, cryptographic utilities (`utility_hash_helper.py`)
7. **`test`**: Automated test suites and fixtures (`test_task_spec.py`)

*Core Invariant:* Upper layers may only depend downward. Lower layers may never import upper layers.

## Commands & Usage

Run lint checks via the unified CLI orchestrator:

```bash
# Run architecture check on current repository
aa run lint check .

# Check specific file or directory
aa run lint check src/modules/

# Attempt automatic remediation for fixable violations
aa run lint fix .

# Export skills or rule references
aa run lint export-rules
```

## Exit Codes

- `0`: All architecture rules and layer constraints passed.
- `1`: Architectural violations detected (blocks merge/quality gates).
- `2`: Configuration or parse errors.
