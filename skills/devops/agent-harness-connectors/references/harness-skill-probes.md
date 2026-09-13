# Harness skill-discovery probes (symlink evidence)

Evidence needed before flipping an adapter's `SKILL_LINK_VERIFIED` or trusting a
root skills symlink. Order of preference: deterministic dump > isolated-home
listing > LLM-turn ask (costs quota, can 401/429, answers are self-reports).

## hermes

Isolated home, no LLM, no risk to the real config:

```bash
mkdir -p /tmp/hf && ln -s /path/to/pack/skills /tmp/hf/skills
HERMES_HOME=/tmp/hf hermes skills list | grep -c enabled
```

Hermes walks skills with `os.walk(followlinks=True)` (agent/skill_utils.py) and
its `atomic_write_text` writes THROUGH the link into the pack — a pack
`git diff` after an edit via the link is the write-through proof.

## opencode

Deterministic, LLM-free, JSON out:

```bash
opencode debug skill > /tmp/oc.json   # or ~/.opencode/bin/opencode ...
python3 -c "import json;print(sorted(s['name'] for s in json.load(open('/tmp/oc.json'))))"
```

Scan roots: `~/.config/opencode/skill(s)/<name>/SKILL.md` (the root-link
target), plus project `.opencode/skill(s)/` and external `~/.claude/skills`,
`~/.agents/skills`. The binary is often NOT on PATH — it lives at
`~/.opencode/bin/opencode`; check there before concluding it is uninstalled.
Count entries before/after swapping the dir for a symlink to quantify the
result (built-in + global dumps can be huge; parse, never grep the human view).

## qwen code

LLM-turn probe (needs working router auth):

```bash
qwen --yolo -p "is there a skill named 'X'? answer YES or NO only"
```

Qwen scans the top level of `~/.qwen/skills/` — a symlinked skill DIR and a
symlinked skills ROOT are both followed. Name a skill that exists ONLY in the
pack (not in any copy-era snapshot at that path), or the YES proves nothing.

## antigravity (agy)

LLM-turn probe only — no deterministic skill listing subcommand
(`agy skills` is not a command). Quirks:

- `--print` is greedy: `agy --print 'prompt' --dangerously-skip-permissions`
  swallows the NEXT flag as the prompt. Bind it: `agy --print='...'`.
- Needs stdin detached (`</dev/null`) and a moment to boot its language server.
- Failures show as `error: interrupted`; check
  `~/.gemini/antigravity-cli/cli.log` for the real cause (e.g. quota
  RESOURCE_EXHAUSTED 429 with a reset ETA in the message).
- Canonical dir is `~/.gemini/config/skills`; the adapter mirrors it via
  symlinks at `~/.gemini/antigravity/skills` and
  `~/.gemini/antigravity-cli/skills` (pre-existing design — the mirror itself
  proves agy follows dir symlinks one hop out, but the ROOT at
  `config/skills` still needs its own probe).
- When quota blocks the probe, keep the gate False and record the exact
  flip procedure in the `SKILL_LINK_VERIFIED` comment; do not flip on
  borrowed evidence.
