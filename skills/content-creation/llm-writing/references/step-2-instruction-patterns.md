# LLM Writing — Step 2: Instruction Patterns

Field tables and templates for defining tools, skills, tasks, and commands in agent-facing text.

**Goal:** every tool, skill, task, or command definition carries the full field set, copy-pasteable and unambiguous.

## Used-in values

| Value | Applies to |
|-------|------------|
| Tool | Tool definitions |
| Skill | Skill definitions |
| Task | Task definitions |
| Command | Command definitions |
| Brief | Task briefs |

## Tool, Skill, and Task Definitions

| Field | Content | Rule | Used in |
|-------|---------|------|---------|
| Name | Exact identifier | Matches code or config verbatim | Tool, Skill, Task |
| Goal | One-line outcome wanted | Verb first. Measurable | Tool, Skill, Task, Brief |
| Trigger | `Use when [condition]. NEVER use for [anti-pattern].` | Both halves required | Tool, Skill, Task |
| Context | Facts the agent lacks: state, background, prior decisions | Include only facts that change the action | Tool, Skill, Task, Brief |
| Inputs | Parameter schema or provided materials | Mark each required or optional. Give type, default, example | Tool, Skill, Task |
| Constraints | Hard limits: scope, forbidden actions, budgets | Rule row format from `step-4-rules-constraints.md` | Tool, Skill, Task, Brief |
| Execution | Exact CLI command, API call, or ordered steps | Copy-pasteable. State working directory | Tool, Skill, Task |
| Outputs | Return format | JSON schema or text shape. State length, structure, exit codes | Tool, Skill, Task |
| Done condition | Checkable end state | Boolean. Verifiable without judgment | Brief |
| Error handling | Fallback per failure | One row per failure: Symptom, Cause, Action | Tool, Skill, Task |

## Tool definition template

```yaml
name: <identifier>
trigger: "Use when <condition>. NEVER use for <anti-pattern>."
inputs:
  - name: <param>
    type: <type>
    required: true
    default: null
    example: <value>
constraints:
  - id: <id>
    rule: <rule>
    check: <check>
execution: "<command>"
cwd: "<path>"
outputs: "<format>"
exit_code: <number>
on_error:
  - symptom: "<message or exit code>"
    cause: "<why it happens>"
    action: "<exact fallback>"
```

## Brief template

```markdown
# <Task Title>

## Goal
<One line: what the agent must do>

## Trigger
Use when <condition>. NEVER use for <anti-pattern>.

## Inputs
| Item | Value | Required |
|------|-------|----------|

## Steps
| Step | Action | Expected |
|------|--------|----------|

## Outputs
<Format, length, structure, exit codes>

## Done condition
<Boolean, verifiable without judgment>
```

## Commands

| Field | Rule |
|-------|------|
| Format | One code block per command. No prompts (`$`) in copy-pasteable lines |
| Context | State `cwd`, required env vars, and prerequisites |
| Expectation | State expected exit code or output signature |
| Verification | `VERIFIED` only after running; else `UNVERIFIED` (Global Rule R6) |

The `VERIFIED`/`UNVERIFIED` marker sits in an adjacent column or field, never inside a copy-paste command block.

## Completion

- Every definition carries all fields from its `Used in` column.
- Trigger fields contain both halves: `Use when ...` and `NEVER use for ...`.
- Every command states cwd, prerequisites, expectation, and its verification status.
- Error handling rows include Symptom, Cause, and Action.
