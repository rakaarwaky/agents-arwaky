# Mirror / proxy alternative

Use this path instead of manual placement when a mirror or proxy is reachable.

**Goal:** `playwright install` succeeds via the mirror without touching the cache dir manually.

## Env var override

Set `PLAYWRIGHT_DOWNLOAD_HOST` before running `playwright install`:

```bash
export PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
python -m playwright install chromium
```

The env var is read by Playwright's download layer and replaces the
default CDN host for all browser downloads. It is preferred over manual
placement because the installer handles the marker files automatically.

## Completion

- `python -m playwright install chromium` exits 0 with downloads coming from the mirror host.
- `verify.md` passes against the resulting cache dir.
