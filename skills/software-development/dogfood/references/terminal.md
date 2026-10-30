# Terminal / TUI Target — Toolset and Workflow

QA workflow for command-line tools and terminal user interface (TUI) apps.

## Prerequisites

- A shell with `run_terminal_command` (or equivalent) and a terminal capture
  utility (`screen` or `tmux`) for TUI state capture.
- The command or binary under test.

## Explore rhythm

1. **Run the command** and capture stdout + stderr separately:
   ```
   run_terminal_command(command="<cmd> 2> err.log; echo \"exit:$?\"", block_until_ms=30000)
   ```
   Record the exit code, stdout, and stderr separately.

2. **Test the help surface:**
   ```
   <cmd> --help
   <cmd> --version
   ```
   Check that exit code is 0, help text is complete, and version string is present.

3. **Test each subcommand** with valid and invalid arguments. Capture exit codes
   and stderr for every failure.

4. **Test pipe behavior:**
   ```
   <cmd> | grep -q .          # non-empty output on success
   echo "" | <cmd>            # empty stdin
   <cmd> </dev/null           # closed stdin
   ```
   The command must not hang on closed stdin; it should fail fast with a useful
   message.

5. **TUI-specific** — run inside `screen` or `tmux` to capture terminal state:
   ```
   screen -dmS qa <cmd>
   sleep 2 && screen -S qa hardcopy /tmp/qa-tui.txt
   screen -S qa -X quit
   ```
   Check: does the TUI render correctly at the default size? Does it crash if the
   terminal is resized? Does `SIGINT` (`kill -INT`) exit cleanly?

6. **Signal handling** — start the process in the background, send `SIGINT`,
   check that it exits (not hangs) and that exit code is 130:
   ```
   <cmd> &
   PID=$!
   kill -INT $PID
   wait $PID; echo "exit:$?"
   ```

7. **Evidence** — save transcripts to `{output_dir}/transcripts/`; save stderr
   captures to `{output_dir}/logs/`.

## Tips

- Test the TUI at at least two terminal sizes (narrow: 80 cols, wide: 200+ cols)
  to catch layout breakage.
- `SIGINT` must exit the process, not leave it hung — kill -INT and check the
  process is gone within 1 second.
- Non-interactive mode (`</dev/null` stdin) must not hang indefinitely.
- Respect `TERM` and `LANG`/`LC_ALL`; test with `TERM=dumb` and `LANG=C`.
- Test with very long lines and Unicode input for mojibake or truncation.
# Issue Taxonomy — Terminal / TUI

Terminal- and TUI-specific category detail. Shared severity levels and universal

## Visual (terminal)
- TUI garbling: misaligned columns, broken box-drawing, lost cursor after resize
- TUI colors or alignment break under specific `TERM` values or in a specific
  terminal emulator
- Output uses non-portable escape sequences that break on common terminals
- TUI assumes a minimum terminal size and breaks below it
- TUI cursor position lost after terminal resize

## Console (terminal)
- stderr noise on success
- non-zero exit code with no stderr message
- exit code 0 reported on failure, or non-zero on success
- locale / `LANG` not respected; UTF-8 mojibake

## UX (terminal)
- error messages that don't name the failing subcommand or suggest a fix
- `--help` / `--version` output incomplete or inaccurate
- command hangs on piped / closed stdin instead of failing fast
- config file not found error is cryptic; no `--config` flag documented

## Functional (terminal)
- signal handling: SIGINT / SIGTERM leaves the process running or corrupts state
- non-interactive mode (`</dev/null` stdin) hangs indefinitely
- pipe behavior broken: empty output on success, or non-empty on failure

