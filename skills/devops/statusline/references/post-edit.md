# After the edit

What applies, and when, once the table or script changes.

**Goal:** the user knows exactly when the change takes effect and how to spot a mis-named key.

## Effect timing

A change to the `[ui.status_line]` table is read at startup, so they
must restart. A change to the script file applies on the next run. The
row is absent on the welcome screen and in a fullscreen subagent view.

## Failure mode

A row that begins `[ui.status_line]` in the rendered output names a key
Grok could not use; fix that key. `grok inspect` lists the same
problems.

## Completion

- The user was told to restart for a table change (or that a script
  change applies on the next run).
- No rendered row starts with the literal text `[ui.status_line]`.
