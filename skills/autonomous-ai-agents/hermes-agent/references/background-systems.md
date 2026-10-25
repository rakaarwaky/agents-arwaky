# Durable & Background Systems

Four systems run alongside the main conversation loop. Quick reference
here; full developer notes live in `AGENTS.md`, user-facing docs under
`website/docs/user-guide/features/`.

### Delegation (`delegate_task`)

Spawn a subagent with an isolated context + terminal session.

- **Single:** `delegate_task(goal, context)`.
- **Batch:** `delegate_task(tasks=[{goal, ...}, ...])` runs children in
  parallel, capped by `delegation.max_concurrent_children` (default 3).
- **Background:** `delegate_task(background=true)` returns a handle
  immediately and keeps the parent loop going; the child's result
  re-enters the conversation as a new turn when it finishes.
- **Roles:** `leaf` (default; cannot re-delegate) vs `orchestrator`
  (can spawn its own workers, bounded by `delegation.max_spawn_depth`).
- **Not durable.** A backgrounded child is still process-local — if the
  parent process exits, the child is lost. For work that must outlive
  the process, use `cronjob` or
  `terminal(background=True, notify_on_complete=True)`.

Config: `delegation.*` in `config.yaml`.

### Cron (scheduled jobs)

Durable scheduler — `cron/jobs.py` + `cron/scheduler.py`. Drive it via
the `cronjob` tool, the `hermes cron` CLI (`list`, `add`, `edit`,
`pause`, `resume`, `run`, `remove`), or the `/cron` slash command.

- **Schedules:** duration (`"30m"`, `"2h"`), "every" phrase
  (`"every monday 9am"`), 5-field cron (`"0 9 * * *"`), or ISO timestamp.
- **Per-job knobs:** `skills`, `model`/`provider` override, `script`
  (pre-run data collection; `no_agent=True` makes the script the whole
  job), `context_from` (chain job A's output into job B), `workdir`
  (run in a specific dir with its `AGENTS.md` / `CLAUDE.md` loaded),
  multi-platform delivery.
- **Invariants:** 3-minute hard interrupt per run, `.tick.lock` file
  prevents duplicate ticks across processes, cron sessions pass
  `skip_memory=True` by default, and cron deliveries are framed with a
  header/footer instead of being mirrored into the target gateway
  session (keeps role alternation intact).

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (skill lifecycle)

Background maintenance for agent-created skills. Tracks usage, marks
idle skills stale, archives stale ones, keeps a pre-run tar.gz backup
so nothing is lost.

- **CLI:** `hermes curator <verb>` — `status`, `usage`, `run`, `pause`,
  `resume`, `pin`, `unpin`, `archive`, `restore`, `list-archived`, `prune`,
  `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` mirrors the CLI.
- **Scope:** only touches skills with `created_by: "agent"` provenance.
  Bundled + hub-installed skills are off-limits. **Never deletes** —
  max destructive action is archive. Pinned skills are exempt from
  every auto-transition and every LLM review pass.
- **Cost:** the deterministic inactivity/prune sweep runs for free. The
  aux-model "consolidate overlapping skills into umbrellas" pass is
  **off by default** — opt in with `curator.consolidate: true` or
  `hermes curator run --consolidate`. Routine background curation costs
  zero tokens.
- **Telemetry:** sidecar at `~/.hermes/skills/.usage.json` holds
  per-skill `use_count`, `view_count`, `patch_count`,
  `last_activity_at`, `state`, `pinned`.

Config: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).
User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (multi-agent work queue)

Durable SQLite board for multi-profile / multi-worker collaboration.
Users drive it via `hermes kanban <verb>`; dispatcher-spawned workers
see a focused `kanban_*` toolset gated by `HERMES_KANBAN_TASK`, and
orchestrator profiles can opt into the broader `kanban` toolset. Normal
sessions still have zero `kanban_*` schema footprint unless configured.

- **CLI verbs (common):** `init`, `create`, `list` (alias `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Less common: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Worker/orchestrator toolset:** `kanban_show`, `kanban_complete`,
  `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`,
  `kanban_link`; profiles that explicitly enable the `kanban` toolset
  outside a dispatcher-spawned task also get `kanban_list` and
  `kanban_unblock` for board routing.
- **Dispatcher** runs inside the gateway by default
  (`kanban.dispatch_in_gateway: true`) — reclaims stale claims,
  promotes ready tasks, atomically claims, spawns assigned profiles.
  Auto-blocks a task after `failure_limit` consecutive spawn failures
  (default 2; configurable via `kanban.failure_limit` or per-task
  `max_retries`).
- **Isolation:** board is the hard boundary (workers get
  `HERMES_KANBAN_BOARD` pinned in env); tenant is a soft namespace
  within a board for workspace-path + memory-key isolation.

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban

## Supervising long-running background jobs

Definition of done for any background job (training run, dev server, CI watcher, long
`terminal` process): the job completed successfully **and** you verified it produced the
expected outputs. Submitting it is not enough — watching it, interpreting wakeups, and
reporting where it stands all count as working on it.

### Two watching patterns

- **Deterministic predicate watching** — a background script polls and stays silent until a
  condition fires. Launch with `terminal` (`background=true`), get a `session_id`, track with
  `process_manage` (poll / wait / kill). `notify=true` wakes you once on exit;
  `notify=['pattern']` wakes on specific log lines (readiness, `ACTION_REQUIRED`).
- **Qualitative health reading** — a subagent reads logs/system state on a fixed cadence.
  Use `delegate_task` for one-off deep reads; `cronjob_manage` for a recurring prompt on a
  wall-clock schedule (every 10 min, 24 h loop).

Use whichever fits; often both (script for state transitions, subagent for log quality).

### Choosing: monitor vs loop

- **monitor (deterministic):** the event a script can evaluate — an API response, exit code,
  port answering, CI turning red, PR becoming mergeable, dev server up/down. Poll every
  30 s; lower risks rate limits. Stay silent until the predicate fires; wakeups are the
  expensive part, so minimize their count while firing them fast.
- **loop (qualitative health):** judging health needs reading logs — loss curves going
  unstable, a pipeline producing garbage, throughput quietly degrading, faulty nodes.
  A subagent reads on a fixed cadence (say every 10 min) and reports what changed.

### Good monitoring scripts

- Enumerate all terminal conditions first (PR: merged or closed; job: completion or
  unrecoverable failure), then the non-terminal wakeups (CI fail, comment types, merge
  conflicts, mergeable).
- Track state that moves as you work (e.g. the latest commit hash changes on push) — the
  watcher must re-anchor.
- Exit immediately on terminal conditions with `FAILED`, `DONE`, or `CANCELLED`; log
  `ACTION_REQUIRED` for wakeups. Fail early — emit `FAILED` the moment any required
  condition reaches terminal failure.
- Send all debug diagnostics (watcher trace + monitored job's output) to a file, so a log
  line can never be mistaken for DONE/FAILED/CANCELLED.
- Key every log file on the pid or session id of the thing being watched — otherwise a
  second job of the same kind clobbers the first.
- Write the script to a durable location (scratch dir or project) with a clear name such
  as `ci_watcher.sh` — not a throwaway temp path.

### Handling wake-ups

- Address actionable events immediately. Read the logs and debug thoroughly before settling
  on a root cause — long-running processes are expensive. Resubmit once fixed:
  - PRs: re-push the changes and restart CI if needed.
  - Jobs: requeue or relaunch.
  - Always point the watcher at the new PR/job afterwards.
- If several jobs run in parallel, start debugging the moment any one fails to minimize
  total wall-time.

### Restarts and cleanup

- Relaunch a job ⇒ update the watcher to track the new one.
- Spawn a new watcher ⇒ kill the one it replaces — irrelevant wakeups are expensive.
- Watcher in a terminal state ⇒ kill the watcher and the job. Dangling processes (unkilled
  broken training runs) are expensive.
- Leave no detached workers, duplicate pollers, or orphaned watcher processes behind.

### Bundled watcher scripts

- `scripts/watch_dev_server.sh` — dev-server up/down predicate.
- `scripts/watch_pr.py` — GitHub PR state (needs `gh` CLI).
- `scripts/watch_training.py` — nanoGPT/Slurm run stdout
  parsing (run with `--help` for every flag and the run-directory layout it expects).

Launch: `terminal(command="python3 scripts/watch_pr.py <url>", background=true, notify=true)`,
then track with `process_manage` poll/wait.

### Verification

- The watcher is a live background process keyed to the right pid/session, not a stale one
  (confirm with `process_manage` poll).
- Terminal conditions terminate the watcher cleanly; no orphaned poller remains after the
  job ends.
- A wakeup you received named the actionable event and carried the log evidence that
  justified it.

