---
name: howto-generator
description: Generate standardized HOW-TO reference files following AES format. Use when creating new HOW-TO guides for skills.
metadata:
  tags:
    - howto
    - generator
    - template
    - aes
    - documentation
    - scaffolding
  related_skills:
    - author-skill-md
    - aes-architecture
triggers:
  - create howto
  - generate howto
  - make howto template
  - scaffold howto
  - create reference guide
  - howto template
  - howto generator
---

# HOW-TO Generator

> **Purpose**: Generate standardized HOW-TO reference files following the AES documentation format.
> **Audience**: Agents creating new HOW-TO guides for skills.
> **Scope**: Python, Rust, and TypeScript HOW-TO files with consistent structure.

This skill generates HOW-TO files with the standard AES structure:
- Header with Purpose, Audience, Scope, Location, Length
- Rules section
- Workflow section
- Template section
- Section Contract table
- Verify section

---

## Standard Format

Every HOW-TO file must follow this structure:

```markdown
# HOW TO MAKE <CONCEPT> <LANGUAGE>

> **Purpose**: <one-line description of what this HOW-TO teaches>
>
> **Audience**: <who will use this guide>
>
> **Scope**: <what files/patterns this covers>
>
> **Location**: <where files should be created>
>
> **Length**: <expected size/complexity>

---

## Rules

<numbered rules, each preventing a specific failure mode>

---

## Workflow

<step-by-step instructions>

---

## Template

<copy-paste-ready code examples>

---

## Section Contract

| Section | Why it belongs here |
| ------- | ------------------- |
| <section name> | <explanation> |

---

## Verify

<commands to validate the output>
```

---

## Generation Steps

1. **Identify the concept** — What layer/concern does this HOW-TO cover?
   - Layer: taxonomy, contract, utility, capabilities, agent, surface, root
   - Concept: daemon, harness, skill, tool, etc.

2. **Determine the language** — Python, Rust, TypeScript, or all three?

3. **Draft the header** — Fill in Purpose, Audience, Scope, Location, Length

4. **Write Rules** — Numbered list, each rule prevents one failure mode

5. **Write Workflow** — Sequential steps from start to verification

6. **Provide Template** — Copy-paste-ready code with placeholders

7. **Create Section Contract table** — Justify each required section

8. **Add Verify commands** — Machine checks + manual checks

---

## Template Variants

### For Layer Skills (taxonomy, contract, utility, etc.)

```markdown
# HOW TO MAKE <LAYER> <LANGUAGE>

> **Purpose**: Scaffold <layer> files — <one-line description>.
> **Audience**: Agents and engineers scaffolding <layer> files.
> **Scope**: <language> `_<pattern>` files in the shared domain.
> **Location**: Shared domain package next to <related layer>.
> **Length**: <expected size>.
```

### For Documentation Skills (PRD, FRD, BACKLOG, etc.)

```markdown
# HOW TO MAKE <DOC TYPE>

> **Purpose**: Create <doc type> — <one-line description>.
> **Audience**: Engineers, QA, Tech Lead.
> **Scope**: One <doc type> per <scope>.
> **Location**: <where file lives>.
> **Length**: <size range>.
```

### For Migration Skills

```markdown
# HOW TO MAKE MIGRATION <LANGUAGE>

> **Purpose**: Guide phased migration of legacy <language> projects into AES layered architecture.
> **Audience**: Agents and engineers executing a migration to AES.
> **Scope**: Phase-based migration workflow for <language> projects.
> **Location**: Project root; each phase operates on a layer directory.
> **Length**: 9 phases (0–8); total duration depends on violation count.
```

---

## Example: Generate New HOW-TO

To create a new HOW-TO for a hypothetical `logger` utility:

```bash
# 1. Create directory structure
mkdir -p skills/<skill-name>/references

# 2. Create the HOW-TO file
cat > skills/<skill-name>/references/HOW-TO-MAKE-PYTHON-LOGGER.md << 'EOF'
# HOW TO MAKE UTILITY LOGGER PYTHON

> **Purpose**: Hold stateless logging helpers shared across the system.
> **Audience**: Agents and engineers scaffolding AES utility files.
> **Scope**: Python `utility_<domain>_logger.py` files — free functions only.
> **Location**: Shared domain source root next to taxonomy.
> **Length**: Free functions only; used by ≥2 modules.

---

## Rules

1. **Suffix is strictly `_logger`.** File: `utility_<domain>_logger.py`.
2. **Free functions only** — no class, no state, no I/O beyond stdout/stderr.
3. **Domain-agnostic** — no business rules, no layer-name knowledge.
4. **≥2 consumers** — extract only when multiple modules need it.
5. **Register** in shared `__init__.py`.

## Workflow

1. Identify reusable logging pattern across ≥2 modules.
2. Create `utility_<domain>_logger.py` with free functions.
3. Register in shared barrel.
4. Verify: `lint-arwaky-cli scan <layer-path>`.

## Template

```python
"""<Domain> logging helpers — stateless, domain-agnostic."""
from __future__ import annotations
import sys

def log_debug(msg: str) -> None:
    """Print debug message to stderr."""
    print(f"[DEBUG] {msg}", file=sys.stderr)

def log_info(msg: str) -> None:
    """Print info message to stdout."""
    print(f"[INFO] {msg}")
```

## Section Contract

| Section | Why it belongs here |
| ------- | ------------------- |
| Module docstring | Names the role: stateless logging helper. |
| Correct filename + suffix | AES101/AES102 resolve the layer from the name. |
| Free functions only | Utility layer cannot have class/state (AES404). |
| Register in barrel | Makes importable without private module access. |

## Verify

```bash
lint-arwaky-cli scan modules/shared/src
python -c "from modules.shared.src.utility_<domain>_logger import log_debug; print('ok')"
```
EOF
```

---

## Verification

After generating a HOW-TO file:

```bash
# Check documentation invariants
python3 -m modules.root_cli_entry check docs skills/<skill-name>

# Verify structure
grep "^## " skills/<skill-name>/references/HOW-TO-MAKE-*.md
# Expected: ## Rules, ## Workflow, ## Template, ## Section Contract, ## Verify
```

---

## Related Skills

- `author-skill-md` — For SKILL.md creation rules
- `aes-architecture` — For layer-specific HOW-TO examples
