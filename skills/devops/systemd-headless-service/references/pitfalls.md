# Pitfalls

**Goal:** avoid the six failure modes that waste a backgrounding run.

## Don't `rm -rf` the data dir of an app you're only trying to background

Uninstall and "make it run 24/7" are different requests; confirm
scope before any destructive step.

## Double-launch race

Stop any manually-started instance (`kill` the PID) before
`systemd start`, or two processes fight for the port.

## `cd` into a deleted dir

If you just removed a state dir like `~/.omniroute/` the shell's cwd
may be invalid — always pass `workdir=/home/<user>` to terminal calls
after a destructive rm.

## OOM during build

Presents as exit code -9 / SIGKILL on the *shell*, not a clean app
error. Raise MemoryMax and retry.

## `No such column` / SQL errors from sqlite3

Mean the column/table name is wrong or the DB is WAL-locked by a
running process — stop the app first, or use `sqlite3` read-only.

## Completion

- Each pitfall was checked against the run: no data dir deleted
  without scope confirmation, no manual instance left running before
  `systemd start`, no terminal call running from a deleted cwd.
