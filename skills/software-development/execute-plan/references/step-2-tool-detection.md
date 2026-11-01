# Step 2 Tool Detection

Probe the environment once to verify Orca and `gh` availability.

```bash
if command -v orca-ide >/dev/null 2>&1; then echo "yes"; else echo "no"; fi
if command -v gh >/dev/null 2>&1; then echo "yes"; else echo "no"; fi
```

If Orca is missing, stop and report.
Set `gh_available` based on the probe. Re-write the state file.

If `auto_pr_flag` is true but `gh_available` is false, warn:
`"--auto-pr was requested but gh is not installed; the orchestrator will fall back to printing a compare URL."`

## In-Progress Reporting

- After probe (Orca available): `"Tool detection complete: Orca available, gh available: <yes/no>."`
- After probe (Orca missing): `"Orca CLI not found. Install Orca or set ORCA_CLI_COMMAND, then re-run. Stopping."`
