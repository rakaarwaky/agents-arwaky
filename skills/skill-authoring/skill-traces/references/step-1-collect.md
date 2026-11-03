# Step 1: Collect

The collector scans the session store under `$GROK_HOME` (default `~/.grok`). If `aa skills traces collect` reports `kept: 0` / `seen: 0` despite recent activity, re-run with `--grok-home <path>` pointing at the populated session store — a scan root with no sessions yields a run the workflow cannot launch (`count` 0 pauses the run).

Run `aa skills traces collect` into a run dir. The collector writes `manifest.json` (sessions seen / kept / dropped by reason, window and filters used) and `sessions/NNNN-<id>.json` (kept session records).

`scan_sessions` drops records for: no_summary, summary_unreadable, subagent, headless, excluded_cwd, older_than_window, no_human_turns, repeated_single_turn, smoke_test, beyond_limit. The `--min-turns` flag (default `3`, constant `TRACE_COLLECT_MIN_TURNS`) is applied per session: sessions with fewer human turns than the threshold are dropped before record writing.

A narrow window does not affect creation — a phrase repeated in 3 sessions is still a habit, and gaps observed in a few sessions are still open jobs. It only gates retirement.

Read the last run's usage report:

```bash
aa skills traces usage --run-dir <RUN>
```

Then materialize the deterministic files the workflow reads:

    aa skills traces materialize --run-dir <RUN>

This writes `usage.json` (per-skill `count`, `sessions`, `in_slash_mru`, `unused_loaded`) and `phrases.json` (`exact_prompts`, `prompt_stems_12_words`, `repeated_instruction_lines`) into the run dir. Section 3 of the report is derived from `usage.json`; the phrase sections are derived from `phrases.json` — never recounted by an agent.

## Signal definitions the workflow agents read

Skills-only: no plugins, MCP servers, workflows, or hooks. Per-skill use counts and
the `unused_loaded` verdict come from `usage.json` in the run dir; repeated-phrase
material (exact prompts, 12-word stems, repeated instruction lines) comes from
`phrases.json`. Both are written by `aa skills traces materialize` into the run dir
before the workflow launches, so mappers and reducers read them off disk instead of
recounting the `sessions/*.json` records by hand. Coverage counts and window params
come from `manifest.json`.

Ordered by blast radius: an item higher on this list costs the user more per session
than one lower down. Mappers extract these per session; reducers merge them across
sessions; every claim carries the session ids that show it.

## 1. Instructions the user types by hand (a skill should own them)

Text in `turns` that tells the agent HOW to work rather than WHAT to do: process,
order of steps, tools to prefer, checks to run, style, who to notify. Quote it
exactly (at most 200 characters). Then check the loaded skills named in the
session's `skills_loaded`: if one already states it, the owner is that skill (the
phrase joins it as a trigger line); if none does, the owner is NEW.

The task content itself ("fix the flaky test in X") is not an instruction. A phrase
seen in one session is a candidate; two or more distinct sessions make it a habit.
The repeated-phrase candidates are confirmed against `phrases.json` (`exact_prompts`,
`prompt_stems_12_words`, `repeated_instruction_lines`) — the verifier does not
recount them by hand. Mine them with:

```bash
aa skills traces phrases --run-dir <RUN>
```

## 2. Friction (the harness failed the user)

Turns where the user corrected the agent, repeated an earlier instruction, said the
result was wrong or too big, or asked "how's it going" while waiting. Quote
briefly. Friction that recurs across sessions points at a missing or unclear skill
line.

## 3. Stale skill lines (a loaded skill is wrong)

A line in a loaded SKILL.md that the session shows to be wrong or outdated: a path
that did not exist, a flag or command that failed, a model or tool name that was
overridden, a step the user told the agent to skip. Name the skill, quote the
current line from the file, and quote the trace evidence. If the line is not in the
current file, there is no claim.

## 4. Unused skills (candidates to retire)

Never counted by an agent. Per-skill `count`, `sessions`, `last_used`, `in_slash_mru`,
and the `unused_loaded` list are read from `usage.json` in the run dir — the
deterministic material `aa skills traces materialize` writes before launch. A skill in
`unused_loaded` (count 0 across the window, absent from slash MRU) is a retirement
candidate. The safety argument is what still does the job: another loaded copy or a
sibling skill that covers the same job. If nothing else does the job, the action is
`ask`, not `delete`. A skill that other loaded skills reference is an `ask` that
names the referrers; a bundled or git-tracked skill is never removed in place — it
is a `propose` of a user-skill override (bundled) or a pull request (git-tracked).

## 5. Gaps (a recurring need with no owner)

A job the user did by hand in two or more sessions that no loaded skill covers.
Gaps are for discussion; they carry no action id unless the user asks for a skill.

## Per-session record shape (mappers)

```
### <index> <session id> — <title>
- area: repo and top directories touched
- task type: feature | bug fix | debugging | ops/infra | research | config/harness | writing | other
- skills used: names from the session's `skills_loaded` (or none)
- instructions outside skills: quoted, with the owning skill or NEW
- friction: quoted
- stale skill signals: skill, quoted current line, quoted evidence
- gaps
```

End each mapper note with `## Batch candidates`:
`- [phrase|stale|gap] <text> | sessions: <ids> | owner: <skill or NEW>`,
duplicates merged within the batch.
