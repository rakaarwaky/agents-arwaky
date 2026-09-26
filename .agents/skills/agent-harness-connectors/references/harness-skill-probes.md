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

