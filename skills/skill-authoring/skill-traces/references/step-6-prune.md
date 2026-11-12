# Step 6: Prune

After a run completes, clean up the raw session store so it doesn't grow unbounded.

`$GROK_HOME/sessions` holds one directory per TUI session and has no built-in retention mechanism — it grows indefinitely (8 GB observed after ~25 days of active use). Prune keeps only the N most recent session directories; older ones are removed with `shutil.rmtree`.

```bash
# Keep only the 100 most recent session dirs (default)
sac traces prune
```

Sessions are ordered by directory mtime, newest first. The oldest directories are deleted; the newest N are kept intact so the next `sac traces collect` can still scan recent history. If the store already has N or fewer session dirs, nothing is removed.

Run `sac traces prune` after every completed `--learn` or `--evolve` pass, or schedule it on a timer for unattended use.
