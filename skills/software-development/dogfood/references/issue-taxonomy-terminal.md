# Issue Taxonomy — Terminal / TUI

Terminal- and TUI-specific category detail. Shared severity levels and universal
categories live in `issue-taxonomy-general.md`.

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
