# Google Tasks — Tools Reference

MCP tools for managing Google Tasks lists and tasks. All tools require `user_google_email` (string, required). Read tools work without task-specific OAuth scopes; write operations require tasks permission. When `task_list` is omitted, the API defaults to the first non-archived task list.

## Contents
- Task Lists: list_task_lists, get_task_list, manage_task_list
- Tasks: list_tasks, get_task, manage_task
- Tips

---

## Task Lists

### list_task_lists
List all non-archived task lists.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |

### get_task_list
Get a specific task list by ID.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| task_list_id | string | yes | | Task list ID |

### manage_task_list
Create, update, or delete a task list.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| action | string | yes | | "create", "update", or "delete" |
| task_list_name | string | conditional | | Required for create and update |
| task_list_id | string | conditional | | Required for update and delete |

---

## Tasks

### list_tasks
List tasks in a task list with a summary view.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| task_list | string | no | first list | Task list ID |
| show_completed | boolean | no | false | Include completed tasks |
| show_deleted | boolean | no | false | Include deleted tasks |

### get_task
Get full details of a single task.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| task_id | string | yes | | Task ID |
| task_list | string | no | first list | Task list ID |

### manage_task
Create, update, or delete a task; supports nested subtasks and list moves.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| action | string | yes | | "create", "update", or "delete" |
| task_title | string | for create | | Task title |
| task_description | string | no | | Task description |
| due_time | string | no | | RFC 3339 format |
| recurrence | string | no | | RRULE string, e.g. `FREQ=WEEKLY` |
| parent_task | string | no | | Parent task ID for subtasks |
| position | integer | no | | Position in the list (lower = earlier) |
| completed | boolean | no | | Mark as completed |
| task_list | string | no | first list | Task list ID |
| task_id | string | for update/delete | | Task ID |
| move_task_list | string | no | | Target task list ID for moving a task or subtask. If provided, the task is moved there; without this, it stays in its current list |

---

## Tips

**Task lists**: Use `list_task_lists` to discover task list IDs. When no `task_list` is provided, operations default to the first non-archived list.

**Time format**: `due_time` uses RFC 3339 format (e.g. `2026-03-19T09:00:00Z`).

**Subtasks**: Set `parent_task` to create a task as a subtask of another task. Use `position` to control ordering within a list.

**Recurrence**: Set `recurrence` with an RRULE string (e.g. `FREQ=WEEKLY`, `FREQ=DAILY;COUNT=5`) to create recurring tasks.
