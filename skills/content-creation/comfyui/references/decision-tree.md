# ComfyUI — Decision Tree

**Goal:** map "user says X" to the right command without re-deriving the
two-layer model (CLI for lifecycle, scripts for execution).

## Mapping

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

Full command flags: [`official-cli.md`](official-cli.md). Endpoints and
payloads: [`rest-api.md`](rest-api.md).

## Setup & Onboarding (summary)

1. **Ask Local vs Cloud first** — Cloud needs only an API key; local needs a
   real GPU.
2. **Local**: hardware check → Path B (Desktop), C (Portable), D (comfy-cli,
   best for agents), or E (manual).
3. **Post-install**: download a checkpoint, install custom nodes, run
   `health_check.py` + a smoke workflow.

Full walkthrough: [`setup-onboarding.md`](setup-onboarding.md).

## Pitfalls (summary)

1. **API format required** — re-export editor-format workflows via the UI.
2. **Server must be running** — `comfy launch --background`, verify via
   `/system_stats`.
3. **Exact model names** — case-sensitive with extension; use
   `comfy model list`.
4. **Missing custom nodes** — `check_deps.py` finds them,
   `auto_fix_deps.py` installs.
5. **Cloud free tier is read-only** — API execution needs a paid
   subscription.
6. **Video workflows need longer timeouts** (`--timeout 1800`); untrusted
   workflow JSON is arbitrary code — inspect first.

## Completion

- The chosen command matches the user's phrasing in the mapping table and is
  runnable (server up, deps satisfied, or cloud tier correct).
