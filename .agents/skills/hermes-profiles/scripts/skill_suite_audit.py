#!/usr/bin/env python3
"""Audit a Hermes skills tree: index-window, triggers, prose length, slop words, usage.

Usage: python3 skill_suite_audit.py <path/to/skills>   # e.g. ~/agents-arwaky/skills
Read-only. The root may be any path in the symlink chain (a profile's skills/, the hub
root, or the pack); it is resolved first so the walk and the usage file mean the same
thing from whichever path is passed. Skips .hub/ and .curator_backups/.
Reads use/view counts from <root>/.usage.json (that file lives at the hub/pack root and
is shared through the chain -- keys: use_count, view_count, patch_count, last_used_at;
there is no load_count).
"""
import json
import pathlib
import re
import sys

MAX_INDEX = 57          # description chars visible in the skill index
BIG_BODY = 12000        # SKILL.md chars; beyond this, split into references/
LONG_LINE = 400         # single prose line that is genuinely hard to follow

BANNED = [
    "delve", "foster", "leverage", "utilize", "facilitate", "empower",
    "streamline", "robust", "cutting-edge", "paradigm shift", "game changer",
    "tapestry", "realm", "beacon", "multifaceted", "meticulous", "intricate",
    "paramount", "transformative", "elevate", "embark", "supercharge", "harness",
    "ever-evolving",
]
PHRASES = [
    "it's worth noting", "at the end of the day", "when it comes to", "at its core",
    "in today's world", "the reality is", "the truth is", "going forward",
    "let's dive in", "marks a pivotal", "a testament to", "plays a vital role",
    "studies show", "experts agree", "what nobody tells", "the part everyone",
    "here's the thing", "let me be clear", "not only",
]


def frontmatter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    body = text[m.end():]
    try:
        import yaml
        return (yaml.safe_load(m.group(1)) or {}), body
    except ImportError:
        fm = dict(re.findall(r"^(name|description):\s*(.+)$", m.group(1), re.M))
        return fm, body


def prose_lines(body):
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s[0] in "#|->`!* " or len(s) < 60:
            continue
        if not re.search(r"[.!?]\s*$", s) and ":" not in s:
            continue
        yield s


def main():
    root = pathlib.Path(sys.argv[1]).expanduser()
    if not root.is_dir():
        sys.exit("not a directory: %s" % root)
    # Accept any path in the symlink chain (profiles/<p>/skills -> ~/.hermes/skills -> the
    # pack). Resolve once so rglob never has to follow a symlinked root, and fall back to
    # the hub root for .usage.json when the given root has none of its own.
    root = root.resolve()
    usage = {}
    for uj in (root / ".usage.json", pathlib.Path("~/.hermes/skills/.usage.json").expanduser()):
        if uj.exists():
            usage = json.loads(uj.read_text())
            break
    rows = []
    for p in sorted(root.rglob("SKILL.md")):
        if ".hub" in p.parts or ".curator_backups" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        fm, body = frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        # Layout is <category>/<skill>/SKILL.md, so the dir above the file is the name.
        name = str(fm.get("name") or p.parent.name)
        desc = str(fm.get("description") or "").strip().strip("\"")
        u = usage.get(name) or {}
        hits = []
        for w in BANNED + PHRASES:
            for m in re.finditer(re.escape(w), body, re.I):
                line = body[:m.start()].count("\n")
                snippet = body.splitlines()[line].strip()[:120]
                hits.append((w, line + 1, snippet))
        longest = max((len(s) for s in prose_lines(body)), default=0)
        flags = []
        if len(desc) > MAX_INDEX:
            flags.append("DESC_TRUNC(%dch)" % len(desc))
        if desc and not re.search(r"^##\s*(When to Use|Triggers?|Use this when|Scope)\b",
                                  body, re.M):
            flags.append("NO_TRIGGER_SECTION")
        if len(body) > BIG_BODY:
            flags.append("BIG_BODY(%dB)" % len(body))
        if longest > LONG_LINE:
            flags.append("LONG_LINE(%dch)" % longest)
        if not u.get("use_count") and not u.get("view_count"):
            flags.append("UNUSED")
        rows.append((rel, name, flags, hits, u.get("use_count", 0),
                     (u.get("last_used_at") or "")[:10]))   # null is legal in .usage.json

    print("skills audited: %d   (usage entries: %d)" % (len(rows), len(usage)))
    for rel, name, flags, hits, uses, last in rows:
        if not flags and not hits:
            continue
        print("\n%-55s use=%s last=%s" % (rel, uses, last or "-"))
        if flags:
            print("   flags: " + ", ".join(flags))
        for w, ln, snip in hits[:6]:
            print("   word '%s' @L%d: %s" % (w, ln, snip))
        if len(hits) > 6:
            print("   ... %d more hits" % (len(hits) - 6))
    print("\nclean (no flags, no word hits):")
    clean = [r[0] for r in rows if not r[2] and not r[3]]
    for rel in clean:
        print("   ", rel)
    if not clean:
        print("    (none)")


if __name__ == "__main__":
    main()
