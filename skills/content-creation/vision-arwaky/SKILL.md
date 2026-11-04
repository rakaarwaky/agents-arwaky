---
name: vision-arwaky
description: "Unified image and video intelligence for computer vision, OCR, video analysis, object tracking, and MCP integrations."
when-to-use: "Use when the user needs computer vision — image analysis, OCR, screenshot comparison, video info/frame extraction, scene/motion detection, object tracking, or smart-video understanding via CLI or MCP."
argument-hint: "<init|analyze|ocr|compare|video-info|extract-frames|check-corruption|detect-scenes|detect-motion|track|analyze-video> [--image PATH|--image1 PATH|--image2 PATH|--video PATH|--prompt TEXT|--lang CODE|--bbox X,Y,W,H]"
---

# Vision Arwaky

You drive Vision Arwaky, a Python computer-vision toolkit exposed through a
CLI (`va` / `vision-arwaky-cli`), an MCP server (`vision-arwaky-mcp`), and a
TUI config interface (`vision-arwaky-tui`).

## Global Rules

- **Entry points.** `va` (or `vision-arwaky-cli`) runs every command;
  `vision-arwaky-mcp` starts the MCP server over stdio;
  `vision-arwaky-tui` starts the TUI config interface. During development
  use `uv run <command>` when the project is managed by `uv`.
- **MCP tools.** The MCP server exposes six tools: `vision_init`,
  `vision_execute`, `vision_list_commands`, `vision_help`, `vision_status`,
  `vision_cancel`. The entry point is `modules/root_mcp_entry.py`, and the
  action surface is `modules/mcp/src/surface_mcp_action.py`. Command details:
  `internal/vision-arwaky/modules/mcp/FRD.md`.
- **External VLM backend.** `analyze` and `analyze-video` use a configured
  external OpenAI-compatible vision endpoint and fall back to deterministic
  processing when no LLM response is available. Supported config:

  ```yaml
  backend: external
  external:
    url: "http://localhost:8080/v1"
    model: "llava"
  ```

  The repo does not bundle a model; set credentials via `LLAMA_API_KEY` or
  `~/.config/vision-arwaky/config.yaml`; never commit an API key.
- **System deps.** `tesseract` for OCR; `ffmpeg` + `ffprobe` for video;
  headless OpenCV runtime for image and video. Install on Debian/Ubuntu:
  `sudo apt-get install -y ffmpeg libgl1 tesseract-ocr`.
- **XDG layout.** Keep machine-specific paths and credentials out of version
  control: `~/.config/vision-arwaky/config.yaml` (`$XDG_CONFIG_HOME`),
  `~/.local/share/vision-arwaky` (data & venv), `~/.cache/vision-arwaky`
  (cache), `~/.local/state/vision-arwaky` (logs & state), `~/.local/bin`
  (executables). Use `LLAMA_API_URL`, `LLAMA_API_KEY`, and `LLAMA_MODEL`
  for env overrides.
- **Documentation levels.** The `vision-arwaky` repository carries three
  documentation tiers — `PRD.md` (product problem, goals, scope, metrics,
  risks), per-feature `FRD.md` files (shared/system/image/video/cli/mcp),
  and `README.md` (install, commands, config, testing, contribution).
- **Current limitations.** VLM analysis needs a reachable external vision
  endpoint. OCR needs the `tesseract` binary. Video needs `ffmpeg`. Object
  tracking uses OpenCV trackers, not a deep-learning detector. Smart-video
  analysis samples a bounded representative set of frames rather than
  sending every frame to the VLM.
- **Completion.** The requested command returned the expected JSON or file;
  for VLM commands the external endpoint was reachable (or the
  deterministic fallback produced the expected output).

## Routing

| Step              | Reference                                                                                          | Purpose                                                                                   |
| ----------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| CLI (workspace)   | run `va init [target_dir]` — initialize workspace (XDG symlinks + `.agents/skills/vision-arwaky/SKILL.md`).       | `init`                                                                                      |
| CLI (image)       | `analyze --image PATH [--prompt TEXT]`, `ocr --image PATH [--lang CODE]`, `compare --image1 P1 --image2 P2`    | Image analysis, OCR, screenshot diff.                                                       |
| CLI (video)       | `video-info`, `extract-frames`, `check-corruption`, `detect-scenes`, `detect-motion`, `track --bbox X,Y,W,H`, `analyze-video` | Video metadata, frame extraction, integrity, scene/motion events, object tracking, smart-video VLM summary. |
| Smart video       | scene-change + motion + uniform sampling; caps frames at 12; bounded summary prompt; per-frame VLM fallback; removes temp frames. | Owned by `analyze-video`.                                                                    |
| Documentation map | `internal/vision-arwaky/` — `PRD.md`, `README.md`, and `modules/{shared,system,image,video,cli,mcp}/FRD.md`.      | Full product, install, and FRD-level specs.                                                   |
