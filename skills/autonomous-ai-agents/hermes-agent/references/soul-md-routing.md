# SOUL.md Identity & Routing

`$HERMES_HOME/SOUL.md` is always loaded into the system prompt when present. It sets
the agent's identity and standing routing rules — it is not project context (that's
`.hermes.md` / `AGENTS.md`). Use it to pin behavior that must hold in every session
across every directory: language, tone, who does what class of task.

## When to reach for SOUL.md

- The user wants Hermes to behave differently by default in a way that is not tied to
  one repo (a standing preference, not a project rule).
- The user wants Hermes to route a whole class of work to an external agent instead
  of doing it inline — e.g. "all coding goes to Grok Build, Hermes only orchestrates
  non-coding work."
- The user wants to pin the identity string Hermes introduces itself as.

Prefer a skill over SOUL.md when the behavior is task-scoped (triggered by a
specific ask). SOUL.md is the always-on layer; skills load on demand.

## Structure that works

- `# IDENTITY` — one or two lines: who the agent is, who it is for, what it owns.
- `# LANGUAGE AND WRITING` — response language, formatting, citation rules, who it
  addresses the user as.
- `# ROUTING` — the decision rule that splits tasks between "Hermes does directly"
  and "delegated to <external agent>". One crisp test (e.g. "a task that will add
  or modify source files is coding") beats a list of examples.
- `# <EXTERNAL-AGENT> DELEGATION` — the concrete command loop, in order, with the
  exact CLIs and flags that are verified working in this install.
- `# WORKFLOW` — how to decompose and parallelize; which lane (direct vs delegated)
  each sub-task goes to.

## Pitfalls

- Keep every delegation command in SOUL.md verified against the live CLI. A flag name
  or agent id that drifts (Orca `--text` vs a bare positional, `--surface terminal`
  vs chat, the registered agent id `grok`) silently breaks the loop in future sessions.
  Confirm with the tool's `--help` and the discovery file
  (`~/.config/orca/agent-model-catalog.json` for Orca agent ids + models) before
  writing it down.
- One line in the routing test should carve the boundary. If you need more than a
  sentence to say what is "coding," the test is too vague — tighten it to a single
  checkable condition.
- Do not let SOUL.md grow into a giant policy file. If a section is task-scoped,
  it belongs in a skill; keep SOUL.md to standing identity + routing.
- `SOUL.md` changes take effect on the next session start, not the live one. Tell the
  user to start a new session (or restart) after editing it.

## Verifying the external lane actually exists

Before committing a routing rule to SOUL.md, confirm the target tool is installed
and its agent id is registered (Orca: `~/.config/orca/agent-model-catalog.json`;
Hermes-spawned instances: `hermes --help`). An uninstalled or unregistered target
makes the whole delegation loop dead on arrival, and a future session will trust the
written-down commands without re-checking.
