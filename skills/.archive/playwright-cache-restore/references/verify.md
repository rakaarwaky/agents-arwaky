# Verification

Run after placement or a mirror install to prove the cache is usable.

**Goal:** every cache dir reports both markers present, `playwright install chromium` exits 0 without downloading, and a headless Chromium actually launches.

## Commands

```bash
# All three markers present
for d in chromium-1243 chromium_headless_shell-1243 ffmpeg-1011; do
  ls ~/.cache/ms-playwright/$d/INSTALLATION_COMPLETE \
     ~/.cache/ms-playwright/$d/DEPENDENCIES_VALIDATED 2>/dev/null \
    && echo "$d OK" || echo "$d MISSING"
done

# playwright install exits 0 with no download attempt
python -m playwright install chromium
# Expected: exit 0, only BEWARE lines, no download

# Functional check: launch headless Chromium
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    print('OK:', b.version)
    b.close()
"
```

## Completion

- Every dir prints `OK` (no `MISSING` lines).
- `python -m playwright install chromium` exits 0 and downloads nothing.
- The launch check prints `OK: <version>`.
