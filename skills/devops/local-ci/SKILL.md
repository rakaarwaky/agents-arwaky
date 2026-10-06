---
name: local-ci
description: Reproduce remote CI gates on the developer machine, in a container, or both. Use when building a ci.sh, mirroring .github/workflows, or when GitHub Actions is quota-blocked.
metadata:
  tags:
    - ci
    - local
    - docker
    - podman
    - quality-gates
    - self-lint
    - architecture
    - aes
  related_skills:
    - setup-ci-quality-gates
    - lint-arwaky
    - testing-suite
  triggers:
    - local ci
    - run ci locally
    - ci.sh
    - mirror workflow
    - reproduce gates
    - offline ci
    - self-hosted runner
---

# Local CI Gates

Build a local script that runs the same gates as `.github/workflows/`, so
CI is reproducible without a network round-trip and merge is not blocked by a
hosted-runner quota, a billing block, or an outage. The remote workflow stays
the source of truth; the local script is a mirror of it.

This is the local half of `setup-ci-quality-gates` (which covers the remote
half: workflow, ruleset, auto-merge, review bots).

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

The image holds every dependency, so `podman run` does no network work. A
warm container starts in under a second; the first build is the only slow
step.

**Slim the base when the official image ships unused browsers.** The
Playwright Python base is 2.41 GB because it bundles Chromium, Firefox,
WebKit, and ffmpeg. An adapter that only drives Chromium needs ~450 MB of
those. `python:3.12-slim` plus the one browser lands near 1.3 GB — 51%
smaller — and `podman build` caches the browser layer independently of
source changes, so the cost is paid once.

**Download browsers with `curl`, not the Playwright installer.** Its Node
downloader has an internal 30 s stall timeout and hangs on slow links even
when the CDN is reachable. `curl --retry 5` at 1 MB/s is reliable. Then write
the marker file the installer checks so the first launch skips the download:

```dockerfile
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN install_browser() { \
        local dir="$1" url="$2"; \
        mkdir -p "${PLAYWRIGHT_BROWSERS_PATH}/${dir}" && \
        curl -fSL --retry 5 --retry-delay 5 -o /tmp/pw.zip "${url}" && \
        unzip -qo /tmp/pw.zip -d "${PLAYWRIGHT_BROWSERS_PATH}/${dir}" && \
        rm -f /tmp/pw.zip && \
        touch "${PLAYWRIGHT_BROWSERS_PATH}/${dir}/INSTALLATION_COMPLETE" \
              "${PLAYWRIGHT_BROWSERS_PATH}/${dir}/DEPENDENCIES_VALIDATED"; \
    } && \
    install_browser "chromium-${REVISION}" "${CHROME_URL}" && \
    install_browser "chromium_headless_shell-${REVISION}" "${HEADLESS_URL}"
```

Both binaries are required: `headless=True` launches the headless shell, a
separate download from full Chromium. Omitting it produces
`Executable doesn't exist at .../chrome-headless-shell-linux64/chrome-headless-shell`.

**Install a prebuilt CLI from the same release the remote job uses.** A
locally installed linter is often several majors behind the release CI
downloads, and the version gap shows up as phantom violations:

```bash
lint-arwaky-cli version          # host: 2.0.0
# container, from releases/latest: 3.7.0 → reports 8 extra violations
```

Match the version, or the local run does not predict CI.

**Pick the base for its glibc, not just its size.** A release binary linked
against glibc 2.38+ refuses to start on bookworm (2.36). Debian trixie ships
2.41.

**Add `tini` as PID 1** when the app spawns browser or Node children;
without it a headless run exiting leaves zombies in the container.

## 5. Verify both runtimes before trusting either

```bash
bash scripts/ci.sh                 # host
bash scripts/ci.sh --container     # container
```

Then confirm the container really has the browser, not just the Python
package:

```bash
podman run --rm --entrypoint <interpreter> <image> -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto('about:blank')
    print('Chromium OK — viewport:', page.viewport_size)
"
```

`--entrypoint` is required: an image whose `ENTRYPOINT` is the app binary
will interpret your `-c` as a subcommand.

## Pitfalls

- **Linter version drift.** The single most common false failure. Pin the
  local binary to the version the workflow downloads.
- **Read-only source mount.** `uv sync` and pytest both write into the tree.
  Mount `:Z` without `:ro`.
- **`ENTRYPOINT` shadowing.** `podman exec` and `podman run` both inherit it;
  use `--entrypoint` to reach a shell.
- **`podman exec --entrypoint` is not a flag.** The running container's
  entrypoint is irrelevant to `exec`; only the command after the container
  name matters.
- **Exit code from the count, not the parser.** Grep `Total: N` for the log
  line, but trust the linter's own exit code. A parse failure should fail the
  gate, never pass it.
- **Skipped test directories.** Copy the full path list from the workflow.
- **Bandit vs tests.** Exclude test dirs and gate on medium severity, or
  the signal drowns.

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
