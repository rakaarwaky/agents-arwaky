# Container image: bake once, run many times

## Slim the base

When the official image ships unused browsers, slim it. The
Playwright Python base is 2.41 GB because it bundles Chromium, Firefox,
WebKit, and ffmpeg. An adapter that only drives Chromium needs ~450 MB of
those. `python:3.12-slim` plus the one browser lands near 1.3 GB — 51%
smaller — and `podman build` caches the browser layer independently of
source changes, so the cost is paid once.

## Download browsers with `curl`, not the Playwright installer

The Node downloader has an internal 30 s stall timeout and hangs on slow
links even when the CDN is reachable. `curl --retry 5` at 1 MB/s is
reliable. Then write the marker file the installer checks so the first
launch skips the download:

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

## Install a prebuilt CLI at CI's release version

A locally installed linter is often several majors behind the release CI
downloads, and the version gap shows up as phantom violations:

```bash
lint-arwaky-cli version          # host: 2.0.0
# container, from releases/latest: 3.7.0 → reports 8 extra violations
```

Match the version, or the local run does not predict CI.

## Pick the base for its glibc

A release binary linked against glibc 2.38+ refuses to start on bookworm
(2.36). Debian trixie ships 2.41.

## Add `tini` as PID 1

When the app spawns browser or Node children; without it a headless run
exiting leaves zombies in the container.
