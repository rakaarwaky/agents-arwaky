# LLM Writing — Step 2: Instruction Patterns

Field tables and templates for defining tools, skills, tasks, and commands in agent-facing text.

**Goal:** every tool, skill, task, or command definition carries the full field set, copy-pasteable and unambiguous.

## Tool, Skill, and Task Definitions

| Field | Content | Rule | Used in |
|---|---|---|---|
| Name | Exact identifier | Matches code or config verbatim | Tool |
| Goal | One-line outcome wanted | Verb first. Measurable | Brief |
| Trigger | `Use when [condition]. NEVER use for [anti-pattern].` | Both halves required | Tool |
| Context | Facts the agent lacks: state, background, prior decisions | Include only facts that change the action | Brief |
| Inputs | Parameter schema or provided materials | Mark each required or optional. Give type, default, example | Tool, Brief |
| Constraints | Hard limits: scope, forbidden actions, budgets | Use the rule row format from `step-4-rules-constraints.md` | Tool, Brief |
| Execution | Exact CLI command, API call, or ordered steps | Copy-pasteable. State working directory | Tool, Brief |
| Outputs | Return format | JSON schema or text shape. State length and structure. State exit codes | Tool, Brief |
| Done condition | Checkable end state | Boolean. Verifiable without judgment | Brief |
| Error handling | Fallback per failure | One row per known failure: Symptom, Cause, Action | Tool, Brief |

Tool definition template:

```yaml
name: <identifier>
trigger: "Use when <condition>. NEVER use for <anti-pattern>."
inputs:
  - name: <param>
    type: <type>
    required: true
    default: null
execution: "<command>"
cwd: "<path>"
outputs: "<format>"
on_error:
  - symptom: "<message or exit code>"
    action: "<exact fallback>"
```

## Commands

| Field | Rule |
|---|---|
| Format | One code block per command. No prompts (`$`) in copy-pasteable lines |
| Context | State `cwd`, required env vars, and prerequisites |
| Expectation | State expected exit code or output signature |
| Verification | Mark `VERIFIED` only after running it. Else `UNVERIFIED` |

## Completion

- Every definition carries all fields from its `Used in` column.
- Trigger fields contain both halves: `Use when ...` and `NEVER use for ...`.
- Every command states cwd, prerequisites, expectation, and its verification status.
