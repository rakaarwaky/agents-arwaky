---
name: long-running-background-tasks
description: "Supervise and report on jobs that keep running after launch."
version: 1.0.0
author: grok-bundled, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [background, watcher, monitor, ci, training, dev-server, process]
    category: devops
    related_skills: [hermes-plan, systematic-debugging]
---

# Working with long-running background tasks

Only submitting or queuing jobs is not sufficient to complete the task. The definition of done is
the job has completed successfully and you have verified that it produced all the expected outputs.
That means watching the job to ensure it is healthy, progressing, and working as intended — and
reporting where it stands counts as working on it.

## Tools available

Hermes maps the two watching patterns onto:

- **Deterministic predicate watching** — a background script that polls and stays silent until a
  condition fires. Launch with `terminal` (`background=true`), get a `session_id`, and check on it
  with `process_manage` (poll / wait / kill). Set `notify=true` for bounded jobs so you are woken
  exactly once when the process exits; use a `notify=['pattern']` list instead for long-running
  watchers that should wake on specific log lines (e.g. readiness) rather than exit.
- **Qualitative health reading** — a subagent that reads logs/system state on a fixed cadence.
  Use `delegate_task` (it reports back what changed, more thorough but more expensive). For a
  periodic prompt on a wall-clock schedule (every 10 min, 24 h loop) use `cronjob_manage`.
- **One-shot fixed waits** — a plain foreground `terminal` command with a high enough `timeout`.
  Do not use a background sleep loop to "wait N seconds".

Decide which of the two you need, sometimes both.

### monitor — deterministic, actionable events

- Use when the event is a predicate a script can evaluate — an API response, an exit code, a port
  answering, CI turning red, a PR becoming mergeable, a dev server coming up or going down.
- The script polls on a fixed cadence and stays silent until the predicate fires, so an idle job
  costs nothing. Wakeups are the expensive part; minimize their count while firing them fast.
- Typical wakeups: CI failing, a PR comment or merge conflict arriving, a PR becoming ready to
  merge, a service going down, a job reaching a terminal state.

### loop — qualitative health that needs reading

- Use when judging health requires reading logs and system information to detect failing, faulty,
  or stalled jobs: loss curves going unstable, a pipeline producing garbage, throughput quietly
  degrading, faulty nodes throwing CUDA errors.
- A subagent reads the logs on a fixed cadence (say every 10 min) and reports what changed. These
  cases are hard to describe deterministically, so a reader is better than a script.
- Examples: a training or data-processing job; monitoring a deployment's 4xx/5xx rates, response
  times, and resources.

## Good monitoring scripts

- Enumerate all terminal conditions first: for PRs that includes merged or closed; for jobs,
  completion or unrecoverable failure. Then enumerate the non-terminal wakeups (CI fail, comment
  types, merge conflicts, mergeable).
- Determine situations where the watcher has to update what it tracks (e.g. the latest commit hash
  changes as you push).
- Poll every 30 s. Lower intervals risk rate limits (especially GitHub with more than one watcher
  on the same token).
- Exit immediately on terminal conditions with `FAILED`, `DONE`, or `CANCELLED`; log
  `ACTION_REQUIRED` for wakeups. Fail as early as possible — emit `FAILED` the moment any required
  condition reaches terminal failure.
- Send all debug diagnostics (the watcher's own trace and the monitored job's output) to a file,
  so a log line can never be mistaken for DONE/FAILED/CANCELLED.
- Key every log file on the pid or session id of the thing being watched, since the paths are
  otherwise fixed and a second job of the same kind would clobber the first one's log.
- Write the script to a durable location (the scratch dir or the project) with a clear name such as
  `ci_watcher.sh` — not a throwaway temp path.

## Handling wake-ups

- Address errors or actionable events immediately. Read the logs and debug thoroughly before
  settling on a root cause — long-running processes are expensive. Resubmit once fixed:
  - For PRs: re-push the changes and restart CI if needed.
  - For jobs: requeue or relaunch.
  - Always point the watcher at the new PR/job afterwards.
- If several jobs are running, start debugging the moment any one fails, to minimize total
  wall-time.

## Restarts and cleanup

- Whenever you relaunch a job, update the watcher to track the new one.
- When you spawn a new watcher, kill the one it replaces — irrelevant wakeups are expensive.
- If a watcher is in a terminal state, kill the watcher and the job. Dangling processes such as
  unkilled broken training runs are expensive. Then address all issues.
- Do not leave detached workers, duplicate pollers, or orphaned watcher processes behind. Kill
  anything attached to a dead or superseded run.

## Examples

### Example: maintaining a dev server

You changed the frontend and want to test it while being notified if the server goes down. Start
the app as a background process:

```
terminal(
  command="echo $$; npm start > logs/dev_server_$$.log 2>&1",
  description="Start the dev server on :3000",
  background=true
)  # returns a session_id / pid
```

No terminal states, but two actionable events: `http://localhost:3000` coming up and going down.
You want the wakeup as soon as it is up so you can use it, and when it stops so you can fix the
code, restart, or free the port. Both down paths quote the tail of the server log so the wakeup
arrives with the error already in hand. Poll every 5 s — cheap, and you want a quick fix if it is
down.

```bash
#!/usr/bin/env bash
# Log paths are keyed on the server pid so two dev servers cannot clobber each other.
PID=$1 URL=http://localhost:3000 DIR="$PWD/logs"
LOG="$DIR/dev_server_$PID.log"
up() { curl -fsS -o /dev/null --max-time 5 "$URL" 2>>"$DIR/watch_dev_server_$PID.log"; }
why() { tail -20 "$LOG" | tr -d '\r' | tr '\n' ' '; }

until up; do
  kill -0 "$PID" 2>/dev/null || { echo "FAILED: pid $PID exited before $URL came up: $(why)"; exit 1; }
  sleep 5
done
echo "ACTION_REQUIRED: $URL is up"

while :; do
  sleep 5
  up || { echo "ACTION_REQUIRED: $URL is down: $(why)"; until up; do sleep 5; done; }
done
```

Spawn it with `terminal` (`background=true`, `notify=['ACTION_REQUIRED']` so each actionable line
wakes you), then track it with `process_manage` poll/wait. On the first wakeup the app is ready.
If it later goes down: read `logs/dev_server_<pid>.log` for the compile error or port conflict,
fix it; if the server survived, hot reload picks the fix up and the watcher recovers on its own;
if the process died, restart it and relaunch a fresh watcher against the new pid, killing the old
one.

The dev-server watcher script is bundled at `scripts/watch_dev_server.sh`.

### Example: PR monitoring

PR watching stops when the PR is merged or closed, and wakes on:

- Comments (four kinds: inline review threads, review bodies, conversation comments, commit
  comments) — decide with the user which to address automatically and store the decision for later
  sessions.
- Failing CI — usually fixable in code; for flaky CI just re-run it.
- Merge conflicts.
- The PR becoming ready to merge — CI green, no conflicts, reviews complete, no blockers, no open
  inline threads. That wakeup is `kind: mergeable`. Tell the user they can merge now. It is not
  terminal; keep watching until merge or close.

The bundled script `scripts/watch_pr.py` needs an authenticated `gh` CLI (`gh auth login`) and
`python3`. Default poll is 30 s; a lower poll rate may hit GitHub rate limits at higher
concurrency. Transport errors (timeouts, resets, DNS) retry with backoff and jitter and do not
print a line.

```
terminal(
  command='python3 <skill>/scripts/watch_pr.py "https://github.com/<owner>/<repo>/pull/123"',
  description="Watch PR 123",
  background=true,
  notify=true
)
```

### Example: training monitoring

For a long training job, the terminal conditions are failure or completion. Many issues cannot be
caught deterministically, so use a subagent to run a script for the high-level update, then scan
the logs for errors such as faulty nodes or CUDA warnings. The bundled `scripts/watch_training.py`
parses nanoGPT stdout out of a Slurm run directory — run it with `--help` for every flag and the
run-directory / log-line layout it expects.

Launch a periodic reader with `cronjob_manage` on a 10 min interval with a prompt like:

```
Keep an eye on the nanoGPT run nanogpt_owt_124m_r1 (slurm job 1234567) and tell me what changed
since last time. Worktree ~/worktrees/nanogpt-owt-124m.

1. python3 <skill>/scripts/watch_training.py --run-name nanogpt_owt_124m_r1 --job-id 1234567 --target-val 3.00

How to report:
- Start with the job's state and if it changed, e.g. "still RUNNING" or "PENDING -> RUNNING".
- Copy the ISSUES line and the STATUS line from the script exactly as written, numbers and all.
- If the state didn't change, say so in one line and stop.
- If the job finished or died, give the state and exit code, the last ISSUES, and run:
    sacct -j 1234567 -D -X -P -o JobID,State,ExitCode,DerivedExitCode,Elapsed,NodeList,FailedNode
    tail -20 ~/train_logs/slurm-nanogpt_owt_124m_r1-1234567.out
Keep <=10 lines: state, progress and eta, loss trend, then anything that smells like training going
unstable (loss spiking, NaN, val loss creeping back up) or the cluster misbehaving (a drained or
failing node, OOM, NCCL errors, a preemption, iters suddenly slower than usual).
```

Also spawn a monitor (a `terminal` background process) that is woken on state transitions, e.g.:

```
while :; do
  s=$(sacct -nXP -j 1234567 -o State | head -1); s=${s%% *}; s=${s:-PENDING}
  if [ "$s" != "$prev" ]; then
    case $s in
      COMPLETED) echo "DONE: 1234567"; exit;;
      PENDING|RUNNING|CONFIGURING|COMPLETING|REQUEUED|SUSPENDED|RESIZING)
        [ -n "$prev" ] && echo "ACTION_REQUIRED: 1234567 $prev -> $s";;
      *) echo "FAILED: 1234567 $s"; exit 1;;
    esac
  fi
  prev=$s; sleep 30
done
```

When the monitor reports the job completed, cancel the monitor and the periodic reader, then
determine next steps: if it succeeded, present the results; if it failed, debug thoroughly, fix,
and relaunch with fresh watchers. Always relaunch so the user's time isn't wasted — but understand
the issue before resubmitting, since training jobs are expensive.

## Verification

- The watcher is a live background process (confirm with `process_manage` poll) keyed to the right
  pid/session, not a stale one.
- Terminal conditions terminate the watcher cleanly; no orphaned poller remains after the job ends.
- A wakeup you received named the actionable event and carried the log evidence that justified it.
