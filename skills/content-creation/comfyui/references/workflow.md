# ComfyUI — Core Workflow

**Goal:** go from "user wants output" to "outputs on disk" in four steps:
get an API-format workflow, inspect it, run it, present results.

## Step 0: Quick start

```bash
# What's available?
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Can this machine run ComfyUI locally? (GPU/VRAM/disk check)
python scripts/hardware_check.py
```

If nothing is installed, ask **Local vs Cloud first**
(see [`setup-onboarding.md`](setup-onboarding.md)) — but always run the
hardware check before a local install.

### One-line health check

```bash
python scripts/health_check.py
# → JSON: comfy_cli on PATH? server reachable? at least one checkpoint? smoke-test passes?
```

## Step 1: Get a workflow JSON in API format

From the ComfyUI web UI (**Workflow → Export (API)**), this skill's
`workflows/` directory, or community downloads (re-export editor-format
files via the UI). Editor format (top-level `nodes`/`links` arrays) is
**not directly executable**. Node types and param mapping:
[`workflow-format.md`](workflow-format.md).

## Step 2: See what's controllable

```bash
python scripts/extract_schema.py workflow_api.json --summary-only
```

## Step 3: Run with parameters

`run_workflow.py` (`--workflow W --args JSON --output-dir D`, plus `--ws`
for live progress and `--input-image` for img2img/inpaint) and
`run_batch.py` (`--count N --randomize-seed --parallel P`) — full flag
examples: [`run-examples.md`](run-examples.md).

## Step 4: Present results

The scripts emit JSON to stdout describing every output file (`status`,
`prompt_id`, `outputs[]` with file/node/type).

## Verification checklist

Use `python scripts/health_check.py` to run the whole list at once. Manual:

- [ ] `hardware_check.py` verdict is `ok` OR the user explicitly chose Comfy Cloud
- [ ] `comfy --version` works; `curl HOST:PORT/system_stats` returns JSON
- [ ] At least one checkpoint installed (local) or listed via cloud models endpoint
- [ ] Workflow JSON is in API format; `check_deps.py` reports `is_ready: true`
- [ ] Test run with a small workflow completes; outputs land in `--output-dir`

## Completion

- `check_deps.py` reports `is_ready: true` for the chosen workflow.
- A test run completed and its outputs are on disk in `--output-dir`.
