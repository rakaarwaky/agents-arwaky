# Local CI: reproduce the gates locally

Merged from the former `local-ci` skill into `setup-ci-quality-gates`.

## Local CI Gates

Build a local script that runs the same gates as `.github/workflows/`, so
CI is reproducible without a network round-trip and merge is not blocked by a
hosted-runner quota, a billing block, or an outage. The remote workflow stays
the source of truth; the local script is a mirror of it.

## Architecture overview

```text
.github/workflows/ci.yml          # source of truth
        │
        │  same commands, two runtimes
        ▼
┌──────────────────────────┬────────────────────────────────────┐
│ scripts/ci.sh (host)     │ scripts/ci.sh --container         │
│ uv/venv on the machine   │ container with everything baked in │
│ ~2 min, no setup         │ ~1 min warm, 0 downloads          │
│ fails on missing dep     │ fails on missing browser          │
└──────────────────────────┴────────────────────────────────────┘
```

Both paths call the same `run_gate` helper and print the same pass/fail
lines, so a green local run predicts a green remote run.

## When to use

- GitHub Actions refuses to start jobs: billing block, spending limit, quota
  exhausted. The annotation reads *"The job was not started because recent
  account payments have failed or your spending limit needs to be
  increased."* Jobs show `steps=0` and an empty `runner_name` — proof the
  runner was never allocated, not that the code failed.
- You want merge to stop depending on a hosted runner at all.
- A self-hosted runner is the alternative: it also removes the quota, but
  costs a VM and keeps the workflow YAML as the only definition. A local
  script is cheaper and makes the gates readable.

Do not use this to skip gates. The script runs the same checks; it only
removes the network dependency.

## 1. Inventory the remote gates first

Read the workflow and copy the commands verbatim. Do not paraphrase.

```bash
grep -nE "^  [a-z0-9-]+:$|    name:|      - name:" .github/workflows/ci.yml
```

For qwen-web-arwaky the seven gates are: Format, Lint (ruff + mypy), Build,
Tests (pytest), Self-Lint, template hygiene, and Bandit. Copy the pytest
invocation's **full path list** — CI usually lists thirteen test directories,
and a local script that only runs `tests/` silently skips modules.

A local-only gate worth adding: security scan with tests excluded. Running
Bandit across `modules/` including test files reports thousands of `B101`
(assert) findings and buries the real ones.

```bash
bandit -r modules/ -x '*/tests/*,*/test/*' --severity-level medium --confidence-level medium
```

## 2. Write the script with a gate helper

Structure: a `run_gate` helper that captures output to a log, prints the
last lines on failure, and counts failures without aborting — so one broken
gate still lets the others report.

```bash
#!/usr/bin/env bash
set -euo pipefail

FAILURES=0
run_gate() {
    local name="$1"; shift
    info "Gate: ${name}"
    if "$@" >"/tmp/ci_${name// /_}.log" 2>&1; then
        ok "${name} passed"
    else
        warn "${name} failed (last lines:)"
        tail -8 "/tmp/ci_${name// /_}.log" || true
        FAILURES=$((FAILURES + 1))
    fi
}
```

Exit non-zero when `FAILURES > 0`, so a pre-push hook can call it.

## 3. Make the two runtimes explicit

Detect whether the script is running inside the container rather than
threading a flag through every gate. The container has its venv at
`/opt/venv` and its package installed, so host-mode setup work must be
skipped.

```bash
IN_CONTAINER=0
if [[ -d /opt/venv && -f /opt/venv/bin/<entrypoint> ]]; then
    IN_CONTAINER=1
fi

if [[ "${IN_CONTAINER}" -eq 0 ]]; then
    command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
    uv sync --no-dev
fi
```

The dispatch that reaches the container:

```bash
if [[ "${1:-}" == "--container" ]]; then
    podman ps --format '{{.Names}}' | grep -q '^<container>' \
        || fail "container '<container>' is not running"
    podman exec <container> bash /root/src/scripts/ci.sh
    exit $?
fi
```

The exec path runs the same file with no flag, so container mode falls
through to the shared gate body. Mount the source tree read-write — pytest
fixtures and tool caches write into the tree, and a `:ro` mount turns
`uv sync` into `Read-only file system (os error 30)`.

```bash
VOLUMES="-v ${REPO_ROOT}:/root/src:Z \
         -v ${VOLUME_DIR}/share:/root/.local/share/<app>:Z \
         -v ${VOLUME_DIR}/state:/root/.local/state/<app>:Z \
         -v ${VOLUME_DIR}/config:/root/.config/<app>:Z"
```

## 4. Container image: bake once, run many times

See `references/container-image.md` for base-image slimming, browser
download via `curl`, marker files, prebuilt CLI pinning, glibc base
choice, and `tini` as PID 1.

## 5. Verify both runtimes before trusting either

See `references/verify-runtimes.md` for the host/container verification
commands and the browser-launch proof.

## Pitfalls

- **Linter version drift.** Pin the local binary to the version the workflow downloads.
- **Read-only source mount.** Mount `:Z` without `:ro`.
- **`ENTRYPOINT` shadowing.** Use `--entrypoint` to reach a shell.
- **`podman exec --entrypoint` is not a flag.** Only the command after the container name matters.
- **Exit code from the count, not the parser.** Trust the linter's own exit code.
- **Skipped test directories.** Copy the full path list from the workflow.
- **Bandit vs tests.** Exclude test dirs, gate on medium severity.

## Checklist — add local CI to a repo

- [ ] Read `.github/workflows/ci.yml`; list every job and its exact command
- [ ] `scripts/ci.sh` with a `run_gate` helper; exits non-zero on failure
- [ ] `IN_CONTAINER` detection skips host setup inside the container
- [ ] `--container` flag dispatches through `podman exec` to the same file
- [ ] Source tree mounted read-write at a known path inside the container
- [ ] `Containerfile` bakes deps, browsers, and the linter at CI's version
- [ ] Both runtimes green; browser launch verified, not assumed
- [ ] Security scan excludes tests and gates on medium severity
- [ ] Remote workflow untouched — the script mirrors it, it does not replace it
