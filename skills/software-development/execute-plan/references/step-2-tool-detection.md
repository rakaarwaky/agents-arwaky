# Step 2 Tool Detection

## Step 2: Tool Detection (Orca, Graphite & gh)

Probe the environment **once** at the start of the run to verify Orca availability and choose the stack-assembly mode. Use the safe `if ... then ... else ... fi` form (the `&& X || Y` shortcut is a footgun if `X` ever fails):

```bash
# Orca CLI — every subagent worktree is Orca-managed, so this is mandatory
if command -v orca-ide >/dev/null 2>&1; then echo "yes"; else echo "no"; fi

# Graphite
if command -v gt >/dev/null 2>&1; then echo "yes"; else echo "no"; fi

# gh
if command -v gh >/dev/null 2>&1; then echo "yes"; else echo "no"; fi
```

If the Orca probe returns `no`, resolve the executable per the *Orca CLI Resolution* rule in `step-0-setup.md` (check `ORCA_CLI_COMMAND` first, then `orca-ide`). If neither is available, **stop and report**: "Orca CLI is required for execute-plan (subagents run in Orca worktrees). Install Orca or set ORCA_CLI_COMMAND, then re-run." Do not fall back to any other worktree mechanism.

For additional confidence that the binary named `gt` is actually Graphite (and not an unrelated tool that happens to share the name), additionally run `gt --help 2>/dev/null` when the first probe returns `yes` and verify the output contains `graphite` (case-insensitive substring match — e.g., `if gt --help 2>/dev/null | grep -qi graphite; then echo "yes"; else echo "no"; fi`). `gt --version` is unreliable here because Graphite's version output is a bare version string with no product name, so it fails the substring check even for a legitimate Graphite install; `gt --help` reliably prints the Graphite CLI banner. Treat unrecognized output as `no`.

Set the state variables based on the probe results:

- `gh_available = (gh probe returned "yes")`
- If `no_graphite_flag` is `true`: set `graphite_available = false` (user explicitly disabled Graphite).
- Otherwise: set `graphite_available = (gt probe returned "yes" AND gt --help output contains "graphite" case-insensitively)`.

Re-write the state file via the `write` tool with the updated `graphite_available` and `gh_available` values (the skill does not use a JSON-merge tool; every state-file update is a full rewrite). From this point on, every step that touches stack tooling branches on `graphite_available`.

Report exactly one of the following based on the resolved mode:

- Graphite mode: `"Graphite mode: gt detected. Stack will be assembled with gt create + gt submit --stack."`
- Plain-git mode (auto-fallback): `"Plain-git mode: gt not installed. Stack will be assembled with plain git branches; PR creation guidance will be printed after assembly."` (when `no_graphite_flag == false` AND `gt` missing)
- Plain-git mode (user override): `"Plain-git mode: --no-graphite was set. Stack will be assembled with plain git branches; PR creation guidance will be printed after assembly."` (when `no_graphite_flag == true`)

If plain-git mode is active and `auto_pr_flag` is true but `gh_available` is false, additionally warn: `"--auto-pr was requested but gh is not installed; the orchestrator will fall back to printing compare URLs."`

