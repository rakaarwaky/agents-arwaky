# Script contract

Grok writes one JSON object to the script's stdin and shows stdout: at
most 5 lines, 1024 characters each. The run times out at 10 seconds.
Stderr is not shown. Empty stdout on success hides the row. A missing
field is omitted, not zero. `jq` prints the text `null` for a missing
key, so use `//`.

**Goal:** a script that renders correctly inside the 5 x 1024 stdout budget without guessing at missing fields.

## Stdin fields

Read fields that are on the stdin object. Common ones: `cwd`,
`session_id`, `session_name`, `transcript_path`,
`model.display_name`, `workspace.current_dir`,
`workspace.repo_root`, `workspace.branch`,
`context_window.used_percentage`, `cost.total_cost_usd`,
`turn.started_at_ms`, `trigger`. There is no `project_dir`,
dirty-file count, rate limit, or editor mode. Call `git` for dirty
state.

`transcript_path` is the session transcript when present. Read it for a
URL the user or the agent already wrote in full. Do not build a URL
from a bare number. Cache that read so a busy turn does not rescan the
file on every run.

## Output rules

ANSI color is kept. An OSC 8 hyperlink is kept for an `http`, `https`,
or `mailto` target, and any other target is plain text. Write it as
`ESC ] 8 ; ; url BEL label ESC ] 8 ; ; BEL`. The 1024-character cut
counts those escapes. Test the script with mock stdin before setting
`command`.

## Completion

- The script passes a mock-stdin test: at most 5 lines, each at most
  1024 characters, runs under 10 seconds.
- Missing stdin fields render as omitted, never as `null` text.
