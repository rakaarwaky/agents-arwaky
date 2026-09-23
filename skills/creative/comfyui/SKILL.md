---
name: comfyui
description: Generate images, video, and audio via diffusion workflows.
metadata:
  tags:
    - comfyui
    - image-generation
    - stable-diffusion
    - flux
    - sd3
    - wan-video
    - hunyuan-video
    - creative
    - generative-ai
    - video-generation
  related_skills:
    - stable-diffusion
  category: creative
---

# ComfyUI

Generate images, video, audio, and 3D content through ComfyUI using the
official `comfy-cli` for setup/lifecycle and direct REST/WebSocket API
for workflow execution.

Two layers: **comfy-cli** (install, server lifecycle, nodes, models) for
setup; **REST/WebSocket API + skill scripts** (param injection, monitoring,
download) for execution — the CLI barely executes workflows.

## What's in this skill

**Reference docs (`references/`):**

- `official-cli.md` — every `comfy ...` command, with flags
- `rest-api.md` — REST + WebSocket endpoints (local + cloud), payload schemas
- `workflow-format.md` — API-format JSON, common node types, param mapping
- `template-integrity.md` — converting `comfyui-workflow-templates` from
  editor format to API format. Load whenever starting from an official template.
- `setup-onboarding.md` — Local vs Cloud choice, install Paths A–E, models, nodes
- `advanced-operations.md` — image upload, cloud specifics, queue management

**Scripts (`scripts/`):**

| Script | Purpose |
|--------|---------|
| `hardware_check.py` | Probe GPU/VRAM/disk → recommend local vs Comfy Cloud |
| `comfyui_setup.sh` | Hardware check + comfy-cli + ComfyUI install + launch + verify |
| `extract_schema.py` | Read a workflow → list controllable params + model deps |
| `check_deps.py` | Check workflow against running server → list missing nodes/models |
| `auto_fix_deps.py` | Run check_deps then `comfy node install` / `comfy model download` |
| `run_workflow.py` | Inject params, submit, monitor, download outputs (HTTP or WS) |
| `run_batch.py` | Submit a workflow N times with sweeps, parallel up to your tier |
| `ws_monitor.py` | Real-time WebSocket viewer for executing jobs (live progress) |
| `health_check.py` | Verification checklist runner — comfy-cli + server + models + smoke test |
| `fetch_logs.py` | Pull traceback / status messages for a given prompt_id |

**Example workflows (`workflows/`):** SD 1.5, SDXL, Flux Dev, SDXL img2img,
SDXL inpaint, ESRGAN upscale, AnimateDiff video, Wan T2V. See
`workflows/README.md`.

## When to Use

- User asks to generate images with Stable Diffusion, SDXL, Flux, SD3, etc.
- User wants to run a specific ComfyUI workflow file
- User wants to chain generative steps (txt2img → upscale → face restore)
- User needs ControlNet, inpainting, img2img, or other advanced pipelines
- User asks to manage ComfyUI queue, check models, or install custom nodes
- User wants video/audio/3D generation via AnimateDiff, Hunyuan, Wan, AudioCraft, etc.

## Quick Start

### Detect environment

```bash
# What's available?
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Can this machine run ComfyUI locally? (GPU/VRAM/disk check)
python scripts/hardware_check.py
```

If nothing is installed, ask **Local vs Cloud first**
(see [references/setup-onboarding.md](references/setup-onboarding.md)) — but
always run the hardware check before a local install.

### One-line health check

```bash
python scripts/health_check.py
# → JSON: comfy_cli on PATH? server reachable? at least one checkpoint? smoke-test passes?
```

## Core Workflow

### Step 1: Get a workflow JSON in API format

From ComfyUI web UI (**Workflow → Export (API)**), this skill's `workflows/`
directory, or community downloads (re-export editor-format files via the UI).
Editor format (top-level `nodes`/`links` arrays) is **not directly executable**.
Node types and param mapping: [references/workflow-format.md](references/workflow-format.md).

### Step 2: See what's controllable

```bash
python scripts/extract_schema.py workflow_api.json --summary-only
python scripts/extract_schema.py workflow_api.json
```

### Step 3: Run with parameters

```bash
# Local (defaults to http://127.0.0.1:8188)
python scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "a beautiful sunset over mountains", "seed": -1, "steps": 30}' \
  --output-dir ./outputs

# Cloud (export API key once; scripts route to /api automatically)
export COMFY_CLOUD_API_KEY="comfyui-..."
python scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs

# Real-time progress via WebSocket (requires `pip install websocket-client`)
python scripts/run_workflow.py --workflow flux_dev.json --args '{"prompt": "..."}' --ws

# img2img / inpaint: --input-image uploads + references automatically
python scripts/run_workflow.py \
  --workflow sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it watercolor", "denoise": 0.6}'

# Batch / sweep: 8 random seeds, parallel up to cloud tier limit
python scripts/run_batch.py \
  --workflow sdxl.json \
  --args '{"prompt": "abstract"}' \
  --count 8 --randomize-seed --parallel 3 \
  --output-dir ./outputs/batch
```

`-1` for `seed` (or `--randomize-seed`) generates a fresh random seed per run.

### Step 4: Present results

The scripts emit JSON to stdout describing every output file (`status`,
`prompt_id`, `outputs[]` with file/node/type).

## Decision Tree

| User says | Tool | Command |
|-----------|------|---------|
| "install ComfyUI" | comfy-cli | `bash scripts/comfyui_setup.sh` |
| "start / stop ComfyUI" | comfy-cli | `comfy launch --background` / `comfy stop` |
| "install X node / model" | comfy-cli | `comfy node install <name>` / `comfy model download --url ...` |
| "is everything ready?" | script | `health_check.py` |
| "what can I change here?" | script | `extract_schema.py W.json` |
| "check / fix deps" | script | `check_deps.py` / `auto_fix_deps.py W.json` |
| "generate an image" | script | `run_workflow.py --workflow W --args '{...}'` |
| "8 variations" | script | `run_batch.py --count 8 --randomize-seed ...` |
| "live progress / error" | script | `ws_monitor.py` / `fetch_logs.py <prompt_id>` |
| "queue / cancel / free VRAM" | REST | `curl HOST:8188/queue`, `/interrupt`, `/free` |

Full command flags: [references/official-cli.md](references/official-cli.md).
Endpoints and payloads: [references/rest-api.md](references/rest-api.md).

## Setup & Onboarding (summary)

1. **Ask Local vs Cloud first** — Cloud needs only an API key; local needs a real GPU.
2. **Local**: hardware check → Path B (Desktop), C (Portable), D (comfy-cli, best for agents), or E (manual).
3. **Post-install**: download a checkpoint, install custom nodes, run `health_check.py` + a smoke workflow.

Full walkthrough: [references/setup-onboarding.md](references/setup-onboarding.md).

## Pitfalls (summary)

1. **API format required** — re-export editor-format workflows via the UI.
2. **Server must be running** — `comfy launch --background`, verify via `/system_stats`.
3. **Exact model names** — case-sensitive with extension; use `comfy model list`.
4. **Missing custom nodes** — `check_deps.py` finds them, `auto_fix_deps.py` installs.
5. **Cloud free tier is read-only** — API execution needs a paid subscription.
6. **Video workflows need longer timeouts** (`--timeout 1800`); untrusted workflow JSON is arbitrary code — inspect first.

## Verification Checklist

Use `python scripts/health_check.py` to run the whole list at once. Manual:

- [ ] `hardware_check.py` verdict is `ok` OR the user explicitly chose Comfy Cloud
- [ ] `comfy --version` works; `curl HOST:PORT/system_stats` returns JSON
- [ ] At least one checkpoint installed (local) or listed via cloud models endpoint
- [ ] Workflow JSON is in API format; `check_deps.py` reports `is_ready: true`
- [ ] Test run with a small workflow completes; outputs land in `--output-dir`

## References

| File | Read it when |
|------|--------------|
| `references/setup-onboarding.md` | Setting up ComfyUI (Local vs Cloud, install paths, models, nodes) |
| `references/advanced-operations.md` | Image upload, cloud endpoint quirks, queue management |
| `references/official-cli.md` | Full `comfy ...` command flags |
| `references/rest-api.md` | REST + WebSocket endpoints and payload schemas |
| `references/workflow-format.md` | API-format JSON, node types, param mapping |
| `references/template-integrity.md` | Converting official templates from editor to API format |

## Scripts

- `_common.py`
