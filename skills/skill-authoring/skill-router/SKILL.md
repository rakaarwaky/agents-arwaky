---
name: jev-skill-router
description: "Route tasks to a Hermes skill via the jev-router CLI."
version: 1.0.0
author: Raka
license: MIT
when-to-use: "Use when deciding which of Hermes's skills fits a task request — before manually scanning the skills list, or to verify a skill choice. Invoked by name in prompts, or when the user asks 'which skill handles X'."
argument-hint: "<task description> [--live]"
metadata:
  hermes:
    tags:
      - skill-routing
      - jev-router
      - typesafe
      - hermes
    related_skills:
      - hermes-agent
---

# Jev Skill Router

Wraps [`jev-agent-skill-router`](https://github.com/GodsBoy/jev-agent-skill-router) — a typed skill-selection layer built for Hermes profiles. Given a task description and the Hermes skill catalogue, it returns `route` (pick this skill), `no_skill` (handle it directly), or `review` (ambiguous — human decides).

## When to Use

- A task arrives and you need to pick the right Hermes skill without manually scanning all 67.
- Verifying a candidate skill choice before loading it with `skill_view`.
- Benchmarking which skill best fits a request, with a probabilistic (not hard) answer.
- User explicitly asks "which skill handles X?" or names `jev-skill-router`.

## sdc discover vs jev-router route — pick the right tool

| Tool | Purpose | Output | Use when |
|------|---------|--------|----------|
| `sdc discover <query>` | Search the skill-design pack catalogue | Scored table of top N matches | You want to browse which skills match a query |
| `jev-router route <request>` | Route to one skill (or none) | Single JSON `route` / `no_skill` / `review` | You want a go/no-go decision on which skill to use |

Use `sdc discover` when browsing; use `jev-router route` when you need a single recommended skill.

## Install (one-time)

Installed at `/home/raka/tools/jev-agent-skill-router` with a `uv` venv at `.venv`.
Catalogue at `/home/raka/tools/jev-agent-skill-router/hermes-catalogue.json` (67 skills, parsed from `skills/catalog.json`).

If the venv or catalogue is missing, run:
```bash
cd /home/raka/agents-arwaky/skills/skill-authoring/skill-router/jev-agent-skill-router
git pull && uv pip install -e .
# Rebuild catalogue when skills/catalog.json changes — see 'Rebuild catalogue' below
```

**After moving or copying the tool directory:** the `.venv/bin/jev-router` shebang hardcodes the old venv python path. Fix it with `patch` or rewrite line 1 to the new `.venv/bin/python` path, then run `uv pip install -e .` so `jev_router` imports resolve.

## Local Jev API endpoint

Live routing calls `https://api.typesafe.ai/v1/systemone` by default. To use a local Jev-compatible endpoint (e.g. 9Router on port 20128), set:

```bash
export JEV_ENDPOINT=http://localhost:20128/v1/systemone
export TYPESAFE_API_KEY=sk-...
```

`JEV_ENDPOINT` is read by `HttpTransport` in `src/jev_router/transport.py`. If the local endpoint is not Jev TypeSafe-compatible (returns HTTP 400 on Jev-format payloads), fall back to `--baseline` mode.

## Route a task

```bash
# Baseline (lexical, free, instant, no API key required)
cd /home/raka/agents-arwaky/skills/skill-authoring/skill-router/jev-agent-skill-router && \
  .venv/bin/jev-router route --baseline \
  --catalogue hermes-catalogue.json \
  --request "Create an Excel spreadsheet with pivot tables from sales data"

# Live (TypeSafe Jev LLM routing — requires TYPESAFE_API_KEY in env)
cd /home/raka/agents-arwaky/skills/skill-authoring/skill-router/jev-agent-skill-router && \
  .venv/bin/jev-router route \
  --catalogue hermes-catalogue.json \
  --request "Create an Excel spreadsheet with pivot tables from sales data"
```

Output is JSON. Read `outcome`, `selected_skill`, and `reason`. If `outcome=review`, fall back to manual skill selection. If `outcome=no_skill`, handle the task directly with general tools.

## TYPESAFE_API_KEY

Live routing calls `https://api.typesafe.ai/v1/systemone` with model `jev-1.13.0` (pinned). Get a key from typesafe.ai and set it in the shell:

```bash
export TYPESAFE_API_KEY=sk-...   # never in config.yaml — secret, belongs in .env or env
```

The repo has `.env.example` but the application does NOT read dotenv files — only the process environment variable.

## Rebuild catalogue

Hermes regenerates `skills/catalog.json` with `sdc catalog --build`. Re-parse it:

```bash
cd /home/raka/agents-arwaky/skills/skill-authoring/skill-router/jev-agent-skill-router
python3 - <<'EOF'
import json
from pathlib import Path
catalog_json = Path("skills/catalog.json").read_text()
data = json.loads(catalog_json)
skills = [
    {"name": s["name"], "description": f"[{s['category']}] {s['description']}"}
    for s in data.get("skills", [])
]
Path("hermes-catalogue.json").write_text(json.dumps(skills, indent=2))
print(f"{len(skills)} skills")
EOF
```

## Thresholds (live routing)

Tunable via CLI flags; defaults in `RouterConfig` (see `src/jev_router/policy.py`):

| Flag | Default | Meaning |
|---|---|---|
| `--confidence-threshold` | 0.70 | Minimum Choice confidence |
| `--probability-threshold` | 0.40 | Minimum winner probability |
| `--margin-threshold` | 0.10 | Minimum winner − runner-up gap |
| `--need-threshold` | 0.70 | Specialist-needed Noul floor |
| `--no-skill-threshold` | 0.30 | No-skill Noul ceiling |
| `--review-threshold` | 0.70 | Ambiguity Noul that forces review |
| `--fit-threshold` | 0.70 | Candidate-fit Noul floor |
| `--batch-size` | 8 | Candidates per Jev call |
| `--keep-per-batch` | 4 | Survivors per batch round |

Lower the confidence/probability thresholds to get more `route` outcomes; raise them to get more `review`.

## Evaluate against a labelled dataset

Use `--dataset examples/evaluation.json` (24 synthetic skills, 72 labelled requests) or your own JSON:

```bash
.venv/bin/jev-router evaluate \
  --catalogue hermes-catalogue.json \
  --dataset my-labels.json \
  --json .tmp/result.json --markdown .tmp/report.md
```

## Pitfalls

- Baseline is lexical (TF-IDF over skill names + descriptions). Fast and free but weaker than live Jev. Both are valid starting points.
- Live routing costs ~0.00001 USD per request (input tokens ~350 at $42/1B). Negligible per call.
- If a request is over 16,000 chars the library rejects it. Summarise first.
- `outcome=review` with `reason=api_error` means TypeSafe call failed — check `TYPESAFE_API_KEY` and network. Retry or fall back to baseline.
- **Live mode does NOT work with 9Router (port 20128) or OpenRouter `/v1/systemone`** — they return HTTP 400/401 because they expect OpenAI-format payloads, not Jev TypeSafe format (`questions` with choice/noul types, `answers` with probabilities). Always test live mode before relying on it; fall back to `--baseline` if it errors.
- The router selects a skill name. Hermes still loads it with `skill_view(name)` — the router does not execute the skill.
- 67-skill catalogue (Nov 2026): default batch_size=8, keep=4 → ~2–3 rounds of parallel Jev calls per request. Each round adds ~400ms. Expect ~1.5s per live route at default settings.

## Grok Build Hook Setup (automatic skill suggestion)

Hermes has no per-user-message hook. Grok Build's `PreToolUse` hook can run the skill router before each tool call and inject a skill recommendation as `additionalContext` that the model sees. `UserPromptSubmit` does NOT work for this — Grok Build rejects `decision: "allow"` and discards `additionalContext` for allowing hooks on that event.

Files:

- `/home/raka/.grok/hooks/jev-skill-router.json` — hook registration (event: `PreToolUse`, matcher: `run_terminal_command|write_file|patch|search_replace`)
- `/home/raka/.grok/scripts/jev-skill-router.sh` — hook script that reads hook input from stdin, runs `jev-router route --baseline`, returns `additionalContext` with the skill recommendation

Verify with: `/hooks-list` or `/hooks` in Grok Build. If the hook isn't loaded, run `/hooks-trust` then reload.

## Hermes Hook Setup

Hermes also has no per-user-message hook. Use `pre_tool_call` in `~/.hermes/config.yaml` (set via `hermes config set` CLI — file tools refuse to write config.yaml directly), and approve the hook script in `~/.hermes/shell-hooks-allowlist.json` with `command`, `event`, and `script_mtime_at_approval` fields.
