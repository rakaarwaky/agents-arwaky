# pdb recipes (full detail)

## Recipe 1: Local breakpoint

Easiest. Edit the file:

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

Run the code normally. You land at the `breakpoint()` line with full access to locals.

**Don't forget to remove `breakpoint()` before committing.** Use `git diff` or a pre-commit grep:
```bash
rg -n 'breakpoint\(\)' --type py
```

## Recipe 2: Launch a script under pdb (no source edits)

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```

## Recipe 3: Debug a pytest test

Use `terminal` and the canonical runner for noninteractive diagnostics:
```bash
# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

`scripts/run_tests.sh` captures each file in a separate subprocess, so `--pdb` or `--trace` cannot provide an interactive prompt there. For an interactive debugger only, use the independent development/test interpreter prepared in Recipe 5 (never a production generation):
```bash
.venv/bin/python -m pytest tests/foo_test.py::test_bar --pdb
```

This bypasses the hermetic-env guarantees — fine for debugging, but re-run under the wrapper to confirm before pushing.

## Recipe 4: Post-mortem on any exception

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Or wrap a whole script:
```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

Or set a global hook in a repl/jupyter:
```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```

## Recipe 5: Remote debug with debugpy (attach to running process)

For long-lived processes: Hermes gateway, tui_gateway, a daemon, a process that's already misbehaving and can't be restarted clean.

### Setup

For Hermes, use a separate development checkout and data home, not a live production generation. Follow the [PM developer workflow](https://hermes-agent.nousresearch.com/docs/reference/package-management#developer-workflow) and activate that checkout — PowerShell: `. .\activate.ps1`. The declared `dev` extra includes debugpy, which PM activation does not sync (`all` excludes it).

Through `terminal`, build a fresh, caller-owned debug/test environment with the prepared checkout's Python:

```bash
source ./activate
python -m pm.build_env --source . --out .venv --group dev --group test
.venv/bin/python -c "import debugpy; print(debugpy.__file__)"
```

The output must not already exist. Stop its processes and intentionally remove only that disposable environment before rebuilding. Keep the same isolated `HERMES_HOME` for the debug target. `.venv/bin/python` is this explicitly built debug environment, not a guessed application venv, and the patterns below run through it. Do not add debugpy to a running production environment; reproduce there only with an already-prepared debug target or arrange a restart in the development environment.

### Pattern A: Source-edit — process waits for debugger at launch

Add near the top of the entry point (or inside the function you want to debug):

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

Start the process; it blocks on `wait_for_client()`.

### Pattern B: No source edit — launch with `-m debugpy`

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

Equivalent for module entry:
```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

### Pattern C: Attach to an already-running process

Needs the PID and debugpy preinstalled in the target's environment:
```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

Some kernels/security configs block the ptrace-based injection (`/proc/sys/kernel/yama/ptrace_scope`). Fix with:
```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

### Connecting a client from the terminal

The easiest terminal-side DAP client is VS Code CLI or a small script. From inside Hermes you have two practical options:

**Option 1: DAP client script** — not an official feature, but a tiny DAP client script:

```python
# ~/.hermes/cache/scratch/dap_client.py
import socket, json, itertools, time, sys

HOST, PORT = "127.0.0.1", 5678
s = socket.create_connection((HOST, PORT))
seq = itertools.count(1)

def send(msg):
    msg["seq"] = next(seq)
    body = json.dumps(msg).encode()
    s.sendall(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

def recv():
    header = b""
    while b"\r\n\r\n" not in header:
        header += s.recv(1)
    length = int(header.decode().split("Content-Length:")[1].split("\r\n")[0].strip())
    body = b""
    while len(body) < length:
        body += s.recv(length - len(body))
    return json.loads(body)

send({"type": "request", "command": "initialize", "arguments": {"adapterID": "python"}})
print(recv())
send({"type": "request", "command": "attach", "arguments": {}})
print(recv())
send({"type": "request", "command": "setBreakpoints",
      "arguments": {"source": {"path": sys.argv[1]},
                    "breakpoints": [{"line": int(sys.argv[2])}]}})
print(recv())
send({"type": "request", "command": "configurationDone"})
# ... loop reading events and sending continue/stepIn/etc.
```

This is fine for one-off automation but painful as an interactive UX.

**Option 2: Attach from VS Code / Cursor / Zed** — if the user has one open, they can add a `launch.json`:

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "<hermes-agent-repo>" }
  ]
}
```

**Option 3: Ditch DAP, use `remote-pdb`** — usually what you actually want from a terminal agent:

For an independently owned Python project, declare `remote-pdb` in that project's development dependencies and prepare its debug environment through the project's package manager. This is not a Hermes SDK install recipe. For Hermes, prefer the declared debugpy dependency; the remote-pdb examples below require a separately declared, freshly built debug environment, never an in-place pip install into the selected application generation.

In your code:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

Then from the terminal:
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

`remote-pdb` is the cleanest agent-friendly choice when `debugpy`'s DAP protocol is overkill. Use `debugpy` only when you actually need IDE integration.
