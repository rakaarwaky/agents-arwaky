---
name: comfyui
description: "Generate images, video, and audio via ComfyUI diffusion workflows."
when-to-use: "Use when the user wants to generate images, video, or audio via ComfyUI diffusion workflows — Stable Diffusion, SDXL, Flux, SD3, AnimateDiff, Hunyuan, Wan, or ControlNet/inpainting/img2img pipelines; also to install, launch, or health-check ComfyUI."
argument-hint: "<hardware_check|setup|run_workflow|run_batch|ws_monitor|health_check|fetch_logs|check_deps|auto_fix_deps|extract_schema|comfy> [--workflow W --args '{}' --output-dir D --count N --randomize-seed --parallel P --ws --input-image PATH]"
---

# ComfyUI

You generate images, video, and audio through ComfyUI using the official
`comfy-cli` for setup/lifecycle and the REST/WebSocket API plus the shipped
scripts for workflow execution.

## Global Rules

- **Two layers.** `comfy-cli` owns install, server lifecycle, nodes, and
  models; the REST/WebSocket API plus the skill scripts own execution,
  parameter injection, monitoring, and downloads — the CLI barely executes
  workflows.
- **API format is required.** Editor-format workflow JSON (top-level
  `nodes`/`links`) is not directly executable; re-export via the web UI
  (**Workflow → Export (API)**). Node types and param mapping:
  [`references/workflow-format.md`](references/workflow-format.md); converting
  official editor templates:
  [`references/template-integrity.md`](references/template-integrity.md).
- **Scripts own the fragile bits.** Scripts in `scripts/` handle credential
  and dependency errors themselves; run `health_check.py` as the single
  end-to-end verification instead of piecing the checklist together.
- **Untrusted workflow JSON is arbitrary code.** Inspect any community or
  downloaded workflow before running it.
- **Video and cloud.** Video workflows need longer timeouts
  (`--timeout 1800`); the cloud free tier is read-only — API execution needs a
  paid subscription.
- **Completion.** `health_check.py` reports every gate green, a test run with
  a small workflow completes, and its outputs land in `--output-dir`.

## Routing

| Step                     | Reference                                                                                          | Purpose                                                                                          |
| ------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Setup & onboarding       | [`references/setup-onboarding.md`](references/setup-onboarding.md)                                 | Ask Local vs Cloud first, install Paths A–E, model and node install.                             |
| Advanced operations      | [`references/advanced-operations.md`](references/advanced-operations.md)                           | Image upload, cloud endpoint quirks, queue management.                                           |
| Core workflow            | [`references/workflow.md`](references/workflow.md)                                                  | Get an API-format workflow, see what's controllable, run with parameters, present results.       |
| CLI reference            | [`references/official-cli.md`](references/official-cli.md)                                         | Every `comfy ...` command and flag.                                                              |
| REST/WS reference        | [`references/rest-api.md`](references/rest-api.md)                                                 | REST + WebSocket endpoints (local and cloud), payload schemas.                                   |
| Workflow format          | [`references/workflow-format.md`](references/workflow-format.md)                                    | API-format JSON, common node types, parameter mapping.                                           |
| Template integrity       | [`references/template-integrity.md`](references/template-integrity.md)                              | Converting official editor-format templates to API format.                                       |
| Run examples             | [`references/run-examples.md`](references/run-examples.md)                                         | `run_workflow.py` and `run_batch.py` flag examples.                                               |
| Decision tree            | [`references/decision-tree.md`](references/decision-tree.md)                                        | "User says X → run Y" mapping across CLI, scripts, and REST.                                     |
| Scripts                  | [`scripts/`](scripts/) (helper: `scripts/_common.py`)                                              | `hardware_check.py`, `comfyui_setup.sh`, `extract_schema.py`, `check_deps.py`, `auto_fix_deps.py`, `run_workflow.py`, `run_batch.py`, `ws_monitor.py`, `health_check.py`, `fetch_logs.py`. |
| Example workflows        | [`workflows/`](workflows/README.md)                                                                 | SD 1.5, SDXL, Flux Dev, SDXL img2img/inpaint, ESRGAN upscale, AnimateDiff video, Wan T2V.        |
