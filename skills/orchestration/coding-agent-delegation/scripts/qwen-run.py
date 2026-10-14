#!/usr/bin/env python3
"""Run a Qwen Code headless delegation task and print a compact verdict.

Usage:
  qwen-run.py <workdir> "<task prompt>" [--budget 15m] [--resume <session-id>]
              [--append-system-prompt "..."] [--bare] [--extra "<raw qwen flags>"]

Writes the raw JSON event stream to <workdir>/.qwen-run/last.json and prints:
result text, turns, files changed, per-tool denials, session id.
Exit code: 0 on success, 1 on suspected-incomplete run, 2 on usage/parse failure.
"""
import argparse, json, os, subprocess, sys, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("prompt")
    ap.add_argument("--budget", default=None, help="e.g. 15m -> --max-wall-time")
    ap.add_argument("--resume", default=None, help="qwen session id to continue")
    ap.add_argument("--append-system-prompt", dest="asp", default=None)
    ap.add_argument("--bare", action="store_true", help="skip ~/.qwen auto-discovery")
    ap.add_argument("--extra", default=None, help="raw extra flags string")
    a = ap.parse_args()

    wd = os.path.abspath(os.path.expanduser(a.workdir))
    cmd = ["qwen", "-y", "--output-format", "json"]
    if a.bare:
        cmd.append("--bare")
    if a.budget:
        cmd += ["--max-wall-time", a.budget]
    if a.asp:
        cmd += ["--append-system-prompt", a.asp]
    if a.resume:
        cmd += ["--resume", a.resume]
    if a.extra:
        cmd += a.extra.split()
    cmd += ["-p", a.prompt]

    out_dir = os.path.join(wd, ".qwen-run")
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, "last.json")
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=wd, capture_output=True, text=True)
    open(raw_path, "w").write(proc.stdout)
    if proc.returncode not in (0, 55):
        print(f"qwen exited {proc.returncode}\nstderr: {proc.stderr[-2000:]}", file=sys.stderr)

    try:
        events = json.loads(proc.stdout)
        last = events[-1]
        assert last.get("type") == "result"
    except Exception:
        print("could not parse qwen json result; raw at " + raw_path, file=sys.stderr)
        sys.exit(2)

    stats = last.get("stats", {})
    files = stats.get("files", {})
    tools = stats.get("tools", {}).get("byName", {})
    denied = {t: v.get("decisions", {}).get("reject", 0) for t, v in tools.items()
              if v.get("decisions", {}).get("reject", 0)}
    print("== qwen-run verdict ==")
    print(f"wall: {time.time()-t0:.0f}s | turns: {last.get('num_turns')} | "
          f"is_error: {last.get('is_error')} | exit: {proc.returncode}")
    print(f"files: +{files.get('totalLinesAdded',0)}/-{files.get('totalLinesRemoved',0)}")
    if denied:
        print(f"DENIED TOOLS (approval-mode problem?): {denied}")
    pd = last.get("permission_denials") or []
    if pd:
        print(f"permission_denials: {len(pd)}")
    print(f"session_id: {last.get('session_id')} (for --resume follow-ups)")
    print("-- result --")
    print(last.get("result", "")[:4000])
    ok = (not last.get("is_error")) and files.get("totalLinesAdded", 0) > 0
    print("-- verdict: " + ("LOOKS DONE (still verify with git diff + tests)"
                           if ok else "SUSPECT - nothing written or error; do not report done"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
