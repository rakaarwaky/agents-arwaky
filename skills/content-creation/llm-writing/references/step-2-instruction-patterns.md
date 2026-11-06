# LLM Writing — Step 2: Instruction Patterns

Field tables and templates for defining tools, skills, tasks, and commands in agent-facing text.

**Goal:** every tool, skill, task, or command definition carries the full field set, copy-pasteable and unambiguous.

## Used-in values

| Value | Applies to |
|-------|------------|
| Tool | Tool definitions |
| Skill | Skill definitions |
| Task | Task definitions |
| Brief | Task briefs |

**Task vs Brief:** a Task is the work item an agent performs; a Brief is the packaged instruction (Goal, Trigger, Context, Inputs, Constraints, Execution, Outputs, Done condition, Error handling) handed to the agent to do the Task. Every Brief serves exactly one Task.

## Tool, Skill, and Task Definitions

| Field | Content | Rule | Used in |
|-------|---------|------|---------|
| Name | Exact identifier | Matches code or config verbatim | Tool, Skill, Task |
| Goal | One-line outcome wanted | Verb first. Measurable | Tool, Skill, Task, Brief |
| Trigger | `Use when <condition>. NEVER use for <anti-pattern>.` | Both halves required | Tool, Skill, Task |
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
goal: <one-line outcome>
trigger: "Use when <condition>. NEVER use for <anti-pattern>."
context:
  - <fact the agent lacks>
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

## Context
<Facts the agent lacks>

## Inputs
| Item | Value | Required |
|------|-------|----------|

## Constraints
| Rule | Check |
|------|-------|

## Execution
| Step | Action | Expected |
|------|--------|----------|

## Outputs
<Format, length, structure, exit codes>

## Done condition
<Boolean, verifiable without judgment>

## Error handling
| Symptom | Cause | Action |
|---------|-------|--------|
```

## Commands

| Field | Rule |
|-------|------|
| Format | One code block per command. No prompts (`$`) in copy-pasteable lines |
| Context | State `cwd`, required env vars, and prerequisites |
| Expectation | State expected exit code or output signature |
| Verification | `VERIFIED` only after running; else `UNVERIFIED` (Rule R6) |

The `VERIFIED`/`UNVERIFIED` marker sits in an adjacent column or field, never inside a copy-paste command block.

## Completion

- Every definition carries all fields from its `Used in` column.
- Trigger fields contain both halves: `Use when ...` and `NEVER use for ...`.
- Every command states cwd, prerequisites, expectation, and its verification status.
- Error handling rows include Symptom, Cause, and Action.
- All fields present and filled; no placeholders and no `UNKNOWN` without justification (Eval 1).
