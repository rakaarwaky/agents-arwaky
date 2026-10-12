# Hook Payload Schemas

This document defines the JSON input/output schemas for each guard hook.

## Common Fields (All Hooks)

```json
{
  "toolName": "string",
  "toolInput": "object",
  "toolResult": {"exit_code": "number", "output": "string"},
  "cwd": "string",
  "workspaceRoot": "string",
  "sessionId": "string",
  "timestamp": "ISO8601"
}
```

## PreToolUse Input

```json
{
  "toolName": "write|search_replace|create_file|run_terminal_command|spawn_subagent|use_tool",
  "toolInput": "{ varies by tool }",
  "cwd": "/absolute/path",
  "workspaceRoot": "/absolute/path",
  "sessionId": "uuid"
}
```

### `run_terminal_command` toolInput
```json
{
  "command": "git commit -m test",
  "description": "commit message"
}
```

### `write` / `search_replace` / `create_file` toolInput
```json
{
  "file_path": "/absolute/path",
  "content": "string"  // write, create_file
  "old_string": "...",
  "new_string": "..."  // search_replace
}
```

### `use_tool` toolInput
```json
{
  "tool_name": "codegraph_explore",
  "tool_input": {}
}
```

### `spawn_subagent` toolInput
```json
{
  "prompt": "...",
  "cwd": "/absolute/path"
}
```

## PreToolUse Output (Allow)

```json
{}
```
Exit code 0, empty stdout.

## PreToolUse Output (Deny)

```json
{
  "decision": "deny",
  "reason": "Denied: <message>"
}
```
Exit code 2.

## PreToolUse Output (Rewrite)

```json
{
  "toolName": "use_tool",
  "toolInput": {
    "tool_name": "codegraph__codegraph_explore",
    "tool_input": {}
  }
}
```
Exit code 0.

## PostToolUse Input

```json
{
  "toolName": "run_terminal_command|write|search_replace|create_file|spawn_subagent|use_tool",
  "toolInput": "{ as above }",
  "toolResult": {"exit_code": "number", "output": "string"},
  "cwd": "...",
  "workspaceRoot": "...",
  "sessionId": "...",
  "timestamp": "..."
}
```

## PostToolUse Output (Allow with Context)

```json
{
  "additionalContext": {
    "reverted": ["/path/to/file1", "/path/to/file2"]
  }
}
```
Exit code 0.

## Stop Hook Input

```json
{
  "reason": "end_turn|error|max_turns",
  "sessionId": "uuid",
  "workspaceRoot": "/absolute/path",
  "stopHookActive": "boolean",
  "subagentType": "string"
}
```

## Stop Hook Output (Block with Notice)

```json
{
  "decision": "block",
  "reason": "Notice: <nudge message>"
}
```
Exit code 2.

## Stop Hook Output (Allow)

```json
{}
```
Exit code 0.
