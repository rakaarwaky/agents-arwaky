# Verify both runtimes

**Goal:** both the host and container gate runs are green, and the
container really has the browser, not just the Python package.

Run both runtimes and confirm they reach the same gates:

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

## Completion

- `bash scripts/ci.sh` and `bash scripts/ci.sh --container` both exit
  0.
- The container launch prints `Chromium OK — viewport: ...`.
