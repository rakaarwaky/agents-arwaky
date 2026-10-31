# Step 0: Intake & Repro Setup

Everything the debugging run needs before any fix: the symptom statement, environment, and a red-capable feedback loop.

## Intake

Resolve the issue input (from the `/systematic-debugging` argument or conversation context):

- `issue_description` — the user's symptom, error text, or failing command.
- `target_lang` — `python`, `typescript`/`node`, or `rust`, picked by file extension / runtime. The language reference (Step 3) is selected from this.
- `repro_command` — the command that triggers the symptom, if one exists.
- `affected_paths` — files, tests, or endpoints named in the issue.

If the issue is vague, ask the user for the exact failing output or command. A debugging run without a symptom statement is guessing.

## Iron Law Gate

The whole run is gated by two conditions. Neither may be bypassed:

```text
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Phase 1–3 establish the root cause. Phase 4 turns the red loop green with the smallest possible change and a regression test. You may not propose or write a fix until both conditions hold.

## Red Flags

If you catch yourself thinking "quick fix for now, investigate later", "just try changing X and see", or "one more fix attempt" after 2+ failed fixes — stop and return to this step. The full list of red flags and the rationalization table live in [`step-6-guardrails.md`](step-6-guardrails.md).

## State

Initialize run state for later steps:

- `fix_attempts`: `0` — incremented per fix tried in Phase 4.
- `hypotheses` — ranked list built in Step 2.
- `repro_command` — finalized tight loop from this step or Step 1.

## Invocation

The user runs:

```
/systematic-debugging <issue-or-error> [--phase <1|2|3|4>] [--lang <python|typescript|rust|node>] [--repro <command>]
```

If `--repro` is given, it seeds `repro_command`. If `--phase` is given, start at that phase instead of Phase 1 (use when resuming mid-run).
