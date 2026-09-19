# Consolidated Plan: `modules/tools` — Unified Tool Lifecycle

> **Sources** (5 independent review passes over the merged `modules/tools` feature, 2026-09-19/20):
> - Architecture review (`tools_20260920-045414.md`)
> - UI/UX review (`tools_20260920-050540.md`)
> - DevOps/SRE review (`tools_20260920-051317.md`)
> - Business analyst review (`tools_20260920-051328.md`)
> - Tech lead review (`tools_20260920-051334.md`)
>
> Scope: 1 agent orchestrator, 4 verb capabilities, 12 per-tool adapter modules (13 tool ids), 2 contracts, 1 root container, 1 CLI surface, 2 taxonomy files. The 5 passes disagreed in places; conflicts are resolved explicitly in § Conflicts. Findings are deduplicated and re-prioritized as one plan.

## Executive Summary

The architecture is sound: contract-driven aggregate, capability injection, manifest SSOT, XDG hygiene, exit-code fidelity. The review found **one crash-grade wiring defect**, **one shared-state bug**, **multiple "nothing raises" contract leaks**, and **material doc-vs-code drift**. No automated tests exist for any of the four functional requirements.

**Consolidated P0 set (6 items — all must land before merge of `refactor/aes-tools`):**

| ID | Fix | Source findings |
|----|-----|----------------|
| P0-1 | Fix `9router` / `qwen-web` registry dispatch: verbs live on classes but registry registers modules → `AttributeError` on any lifecycle verb | Architect #1, Analyst B#3, TechLead CQ-1 |
| P0-2 | Replace class-level `_ADAPTERS` mutation with instance-level copy | Architect #2, Analyst B#2, DevOps R1, TechLead D-1 |
| P0-3 | Rewrite `cmd_run` to delegate to `orch.run_tool()`; delete duplicated cargo/uv/python `os.execvpe` dispatch | Architect #4/#17, UI/UX U1/C1, Analyst L#1, DevOps R4, TechLead E-6/D-2 |
| P0-4 | Fix MCP stdio deadlock in `RunnerCapability._execute` (`stdin=PIPE` on a stdio server hangs forever) | DevOps D1, TechLead P-2 |
| P0-5 | Fix CI entry-point drift (WS-08): `ci.yml` runs `python3 -m modules.cli check` but the entry moved to `modules/root_cli_entry.py` | DevOps CI1 |
| P0-6 | Execute clean-host lifecycle sweep: TOL-02 (exit-code fidelity 0/1/127 + sentinel 126) + TOL-03 (residual reporting); fill Scenario Evidence rows | DevOps D2/CI2, Analyst T#1, TechLead CQ-4 |

---

## P0 — Crash / CI / Release Blockers

### P0-1 `9router` / `qwen-web` registry dispatch (crash-grade)

`root_tools_container.py` registers the *modules* `_ninerouter` / `_qwen_web`, but their verb functions (`satisfied`, `install`, …) exist only as methods on `NinerouterAdapter` / `QwenWebAdapter` classes. Capabilities call `adapter.satisfied(spec, root)` as module attributes → `AttributeError` on every verb for both tools. Two distinct defects in one: (a) runtime crash, (b) AES404 violation (classes in utility-layer files — all 10 other adapters are module-level functions).

**Interim fix (same PR):** mirror the `_ANYTYPE_DAEMON` pattern —
```python
_NINEROUTER = _ninerouter.NinerouterAdapter()
TOOLS_REGISTRY["9router"] = SimpleNamespace(
    satisfied=_NINEROUTER.satisfied,
    install=_NINEROUTER.install,
    is_pin_satisfied=_NINEROUTER.is_pin_satisfied,
    update=_NINEROUTER.update,
    owned_paths=_NINEROUTER.owned_paths,
)
```
**Proper fix (follow-up, AES404):** convert both classes to module-level functions and register the modules directly.

**Smoke:** `aa tool install|update|uninstall|run` for both ids, no `AttributeError`.

### P0-2 `_ADAPTERS` shared-state mutation

`self._ADAPTERS.update(registry)` mutates the class-level dict; the comment claiming instance isolation is false. All instances share and accumulate registry entries.

```python
# agent_tools_orchestrator.py __init__
self._adapters: dict[str, object] = dict(registry)   # was: self._ADAPTERS.update(registry)
```
Remove the class-level `_ADAPTERS` declaration; update all `self._ADAPTERS` references to `self._adapters`.

### P0-3 `cmd_run` bypass (surface must delegate to aggregate)

The surface reimplements discovery + `os.execvpe` dispatch (cargo/uv/python branching), duplicating `RunnerCapability._exec_command`. Drift is already visible: it misses the `python3 -m <id>` fallback, sentinel-126, and MCP stdio handling, and uncaught `OSError` produces a raw traceback (violates FRD-004 "every failure path returns an int").

**Fix:** delete the inline exec logic entirely:
```python
def cmd_run(args: list[str], orch: IToolsAggregate) -> int:
    if not args:
        err("Missing tool name.")
        print("Usage: aa tool run <tool-name> [args...]")
        return 1
    spec = orch.resolve_spec(args[0])
    if spec is None:
        err(f"Tool '{args[0]}' not found in manifest.")
        print("Run 'aa tool list' to see all available tools.")
        return 1
    return orch.run_tool(spec, args[1:])            # exit-code fidelity + sentinel 126 live in the capability
```
Consequence: after this, the orchestrator passthroughs `executable_path()` / `find_executable()` / `execute()` used only by the old path become dead — see P1-4.

### P0-4 MCP stdio deadlock

`_execute` sets `stdin=PIPE, stdout=PIPE, stderr=STDOUT` for MCP specs and calls `subprocess.run`, which blocks until the server closes its pipes — a stdio MCP server never does, and output is never forwarded.

**Fix:** inherit parent stdio for all tools (`subprocess.run(argv, check=False)`); MCP harnesses spawn their servers themselves, `aa tool run <mcp>` is interactive use.

### P0-5 CI entry-point drift (WS-08)

`ci.yml` still runs `python3 -m modules.cli check`; the entry moved to `modules/root_cli_entry.py` and `modules.cli` no longer exposes that path. On merge the CI gate fails — or silently no-ops — on `main`.

**Fix in the same PR as the merge:** update the workflow entry point; verify `grep 'modules.cli check' .github/workflows/ci.yml` → 0 hits.

### P0-6 Clean-host lifecycle sweep

All four FR scenario rows in `BACKLOG.md` are `unverified`; TOL-02/TOL-03 are `QA` with no evidence; "clean host" is undefined and no reproducible recipe exists.

**Fix:**
1. Define clean host (e.g., Podman container from a base image with Python + git only); provide a provisioning script.
2. Run `install → update → run → uninstall` per tool; record commit + command output per Scenario Evidence row.
3. Assert at minimum: double-install no-op, exit codes 0/1/127 passthrough, sentinel 126 on vanished executable, unknown-id typed error, dry-run purity, active-daemon units become named residuals (never force-killed), no artifacts outside XDG dirs.

---

## P1 — "Nothing Raises" Contract & Data Integrity

### P1-1 Consistent error-folding in orchestrator verbs

`install()` folds a missing adapter into `InstallResult`, but `update()` / `uninstall()` let `ToolInstallError` from `_adapter_for` escape to the CLI.

```python
def update(self, spec: ToolSpec, dry_run: bool = False) -> UpdateResult:
    self._require(self._updater, "update")
    if find_tool(spec.id) is None:
        raise ToolUpdateError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
    try:
        adapter = self._adapter_for(spec)
    except ToolInstallError as e:
        return UpdateResult(False, spec.id, str(e))
    return self._updater.update(spec, adapter, dry_run=dry_run)
# uninstall(): same fold, plus wrap adapter.owned_paths() in the same guard
```

### P1-2 Verb-typed `_require` errors

`_require()` raises `ToolInstallError` for every verb. Map verb → error type:
```python
_VERB_ERRORS = {
    "install": ToolInstallError,
    "update": ToolUpdateError,
    "uninstall": ToolUninstallError,
    "run": ToolInstallError,  # no ToolRunError in taxonomy_core_error today
}
```

### P1-3 Guard `satisfied()` in installer

`InstallerCapability.install` guards `adapter.install(...)` but calls `adapter.satisfied(...)` unguarded — a raising `satisfied` (e.g. the P0-1 `AttributeError`) escapes the verb:
```python
try:
    if adapter.satisfied(spec, root):
        return InstallResult(True, spec.id, "satisfied (no action needed)")
except Exception as e:
    return InstallResult(False, spec.id, f"satisfied-check failure: {e}")
```

### P1-4 Broader exception handling in daemon-stop (uninstaller)

`_stop_daemon` catches only `(ValueError, AttributeError)`; a host without `systemctl` raises `FileNotFoundError` into the CLI. Fix: gate `systemctl` probes behind `shutil.which("systemctl")`, and catch `(ValueError, AttributeError, KeyError, OSError)` in `_remove()`, folding each into a **named residual** (never a CLI exception).

### P1-5 `anytype` merged-id uninstall leaves live daemon (invariant breach)

Uninstalling the merged `anytype` id removes the `anytype-daemon` launcher (it is in `LAUNCHER_NAMES["anytype"]`) but never stops the daemon unit — unit handling is keyed only under `anytype-daemon`. A running container survives with its launcher deleted and no named residual.

```python
# taxonomy_tools_constant.py
DAEMON_UNIT_TOOLS = {"9router": "9router.service",
                     "anytype": "anytype-daemon.service",
                     "anytype-daemon": "anytype-daemon.service"}
DAEMON_NAMES = {"9router": "9router", "anytype": "anytype", "anytype-daemon": "anytype"}
```

### P1-6 Merged orchestrator methods outside the aggregate contract

`provision()`, `find_executable()`, `execute()` are public on `ToolsOrchestrator` but absent from `IToolsAggregate`; `RunnerCapability.discover()` / `.execute()` exist solely to serve them. With P0-3 done, these are dead: delete the three orchestrator methods and the public capability wrappers (keep `_discover` / `_execute` private). `IToolRunner` stays declaring only `run()`.

### P1-7 Extract shared adapter mechanics (single source of truth)

`update_submodule` (~80 lines), `generic_owned()` (~20 lines), and a ~100-line git-update block containing an **invalid git invocation** (`git log --count` — `--count` is a `rev-list` flag; the branch always fails silently) are copy-pasted into ~10–12 adapters. Every fix must fan out N times — operational hazard.

**Fix:** create `modules/tools/src/utility_tool_mechanics.py` (the BACKLOG change log already claims this file exists — it doesn't, which is itself a doc defect to reconcile). Move the shared blocks there; adapters call the single source. Fix the git flag to `git rev-list --count` in one place. If AES404 forbids utility→utility imports for this one file, whitelist it explicitly.

### P1-8 Real timestamp in updater transition records

`_record()` writes `"recorded_at": "now"` as a literal string — the audit trail is unusable:
```python
"recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
```
Also: replace the fragile `"already at pin" in update_result.message` string-sniffing skip with an explicit flag (e.g. `moved: bool`) on `UpdateResult`.

### P1-9 Subprocess timeouts + bounded retry

No timeouts on adapter `run()` helpers (`npm ci`, `bun install`, `pnpm install/run build`, `cargo build --release`, `playwright install chromium` can hang indefinitely; only `_version_probe` 60 s and rustup bootstrap are bounded). Add a wall-clock cap (env-overridable, e.g. `ARWAKY_BUILD_TIMEOUT`, default 1800 s for builds / 120 s for probes), catch `TimeoutExpired` and fold into the result. Add bounded retry (2 attempts, exponential backoff, shared free function — no tenacity dependency) around network-bound steps (git fetch, registry installs, browser downloads).

### P1-10 Dry-run contract is unreachable

FRD-001/002/003 specify `dry_run` for every verb and the capabilities implement it, but `IToolsAggregate` has no `dry_run` parameter and the orchestrator hardcodes `dry_run=False` — no UI affordance. Thread `dry_run: bool = False` through contract → orchestrator → capability; parse `--dry-run` in all three surface verbs.

### P1-11 Daemon launcher `AGENTS_ARWAKY_ROOT` validation (security)

Generated launchers do `root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", ...))` then `sys.path.insert(0, str(root))` — a hostile/typo env var redirects module resolution to attacker-controlled code. Validate the hint contains the `config/manifest.json` anchor (mirror `repo_root()` semantics); otherwise fall back to the baked root. Applies to `_write_daemon_launcher` (anytype), `_write_9router_launcher` (9router), and `write_uv_launchers` (mnemosyne/workspace).

### P1-12 rustup bootstrap integrity (supply chain)

`curl https://sh.rustup.rs | sh -y` executes an unauthenticated remote script on cargo-less hosts. Pin and verify the `rustup-init` binary checksum, or make bootstrap opt-in and require a preinstalled toolchain in CI. Same treatment: `_preflight_build_deps` silently runs `sudo -n apt-get install -y` — make it opt-in (`ARWAKY_ALLOW_SUDO=1`) and print the exact command; Playwright browser install is unpinned — pin the package version in the submodule.

### P1-13 `cmd_update all` hides failures

Per-tool errors print but the command exits 0 with `ok("Update finished.")`. Collect failed ids; exit 1 and list them, mirroring `cmd_install`.

### P1-14 Single-tool uninstall has no confirmation

`--all` requires typing `uninstall`, but a single-tool `uninstall` executes immediately. Add `_confirm(f"Uninstall '{target}'? [y/N]: ")` with the same TTY/`--yes` policy as `--all` (skip with `--yes`; block in non-TTY without `--yes`).

### P1-15 Decide WS-05 (live daemon secrets)

No decided home for `anytype.env` / `ninerouter.env`: a fresh clone has no daemon credentials, so `aa anytype start` fails post-install. Decide the single XDG path (`$XDG_CONFIG_HOME/agents-arwaky/*.env`), ship `.env.example` templates, and validate presence with an actionable message in `aa doctor`.

### P1-16 Scope `cmd_install` submodule init

Every single-tool install runs repo-wide `git submodule update --init vendor/ internal/` (seconds of network I/O, and a hard prerequisite that aborts the whole install on failure — FRD does not specify this coupling). For a single target, init only the target's `spec.path` submodule (or skip when `src/.git` already exists); keep the repo-wide init for `all`. Document the prerequisite in FR-001.

---

## P2 — UX, Observability, Documentation

### P2-1 ANSI / terminal-width fixes in `cmd_list`

- **L1:** `pad(cat_color + tool.category + RESET(), w_cat)` counts escape bytes in `pad()` → column misalignment. Pad the plain text first, then colorize: `color + pad(tool.category, w_cat) + RESET()`.
- **L2:** `available = max(60, term_w - 2)` forces a 60-column table on narrow terminals (splits, tmux, phones) and wraps. Below ~62 cols fall back to a compact one-line-per-tool layout.
- **A1:** gate all color helpers on `sys.stdout.isatty()` + `NO_COLOR` in `utility_logging_setup` (single choke point); keep `--json` color-free.
- **A3:** add `--quiet` (ids only) for scripted use.

### P2-2 CLI affordances

- **A2:** intercept `-h/--help` before target resolution in every subcommand (today `aa tool install --help` reports `Tool '--help' not found in manifest`).
- **U5:** long builds (e.g. `cargo build --release`) print one `>>> Building…` line then silence — emit heartbeat/phase lines or stream cargo progress so "working" is distinguishable from "hung".

### P2-3 Unify adapter output (two visual dialects)

Surface uses `ok/err/warn/info/banner` helpers; all 13 adapters emit raw `print()` with ad-hoc prefixes (`>>>`, `[ok]`, `[skip]`, `[update]`, `->`). Route adapter progress through `utility_logging_setup` (or a `phase()/step()` pair added there) so prefix/color/TTY policy lives in one place. Standardize result wording to `<tool>: <state> (<detail>)`.

### P2-4 Health probe robustness

`_version_probe` resolves via PATH, but the just-written launcher lives in `~/.local/bin` which is not guaranteed on PATH; a probe miss degrades to a bare `"installed"` with no health evidence. Probe `bin_home() / spec.binary` first, PATH second; on probe failure say so explicitly in `InstallResult.message`. Also: the probe does not check version *agreement* against the manifest pin despite the FRD claiming it — either implement the comparison or reword the FRD to "presence check". Extend install stamps to node/bun/pnpm tools (anytype, codegraph, context7, fetch, ponytail) so every tool has a uniform `.arwaky-install.json` rollback/audit record.

### P2-5 Launcher name single-source (drift hazard)

Launcher/alias names live in two places: each adapter's `LAUNCHERS` list (install writes from it) and `taxonomy_tools_constant.LAUNCHER_NAMES` (uninstall removes from it). Drift means silent uninstall residuals. Derive one from the other (adapters expose `LAUNCHER_NAMES`; the constant table aggregates them).

### P2-6 Documentation / spec reconciliation (FRD, BACKLOG, PRD)

The doc layer contradicts the tree in at least six places; fix all in one pass:

| Doc defect | Fix |
|------------|-----|
| FRD System Overview + API Contract reference deleted `AdapterBase` (`utility_adapter_base.py`) | Rewrite: adapters are plain modules of stateless verb functions (daemon-backed: merged module namespaces), typed `object`; mechanics via `utility_tool_mechanics` free functions. Remove the `AdapterBase` row. |
| FRD claims "13 `utility_*_adapter.py` files" | 12 files cover the 13-tool registry (`anytype` + `anytype-daemon` share one merged module). Correct the count and the measurement command. |
| Capability docstrings cite phantom FR-005…FR-008 (FRD defines FR-001…FR-004 only) | installer→FR-001, updater→FR-002, uninstaller→FR-003, runner→FR-004; delete phantom refs. |
| FRD API Contract leaves `root` precedence undocumented | Document: explicit `root` > constructor `root` > `repo_root()`. |
| FRD Test Scenarios: no scenario has `Kind: Automated`; BACKLOG TOL-04 marked In Progress while the tree already has the 4-file fold | Evidence TOL-04 with a commit hash and mark Done; promote at least FR-001 (install idempotence) and FR-004 (exit-code fidelity) to automated tests. |
| BACKLOG change log claims bodies live in `utility_tool_mechanics.py` which does not exist; PRD Goal 5 "1 tool = 0 new modules" vs FRD "1 adapter file per tool"; skill exclusion from the tools lifecycle unexplained | Create the mechanics file (P1-7) and reconcile the log; restate Goal 5 as "1 manifest entry + 1 adapter file, zero orchestrator/capability edits"; add the skill-exclusion note to FRD § Assumptions. |
| Legacy updater state path `state_home()/agents-arwaky/updater/<id>.json` undocumented after the 4-module merge | Document as a stable contract in FRD (or migrate with a one-time copy). |
| Two `__init__.py` export sets differ (top-level re-exports `ToolsOrchestrator` + legacy `ToolOrchestrator` alias; `src/__init__.py` only `create_tools_feature`) | Converge on one surface; remove the `ToolOrchestrator` alias after `grep -r "ToolOrchestrator" --include="*.py"` outside tools shows zero references (P3). |
| `taxonomy_xdg_atomic_io` in shared exports I/O functions (`ensure_bin_home`, `remove_tool_artifacts`, `atomic_write_text`) — AES §5 forbids infrastructure in taxonomy | File the rename `taxonomy_xdg_atomic_io.py` → `utility_xdg_atomic_io.py` against `modules/shared`; tools import paths update only. |

### P2-7 Test infrastructure

- Unit tests for each capability with mock adapters (create `FakeDaemonAggregate` test double for the daemon path).
- Integration test for orchestrator dispatch with a stub registry.
- CLI smoke tests: `aa tool list`, `aa tool run --help`.
- Gate the next release on the four FR scenario rows having automated evidence (P0-6).

### P2-8 CI hardening

- Add `pip-audit` and `bandit -r modules/ -ll` (non-blocking first, then blocking).
- Add changelog generation from Change Log sections at release time.
- Keep the existing gates: compileall + ruff + JSON validation.

---

## P3 — Deferred / Low-risk

- [ ] Remove `ToolOrchestrator` backwards-compat alias after confirming zero external references. *(P3)*
- [ ] `ExitCode` / `ToolQuery` NewTypes are nominal-only; either wrap at the boundary (`return ExitCode(code)`) or drop them.
- [ ] Parallel `install all` / `update all` via `ThreadPoolExecutor` for independent (non-daemon) tools; keep daemon tools sequential (container-isolation invariant). Revisit fetch pre-pass parallelism only if tool count grows.
- [ ] Lazy `importlib` adapter resolution if the registry grows beyond ~30 modules.
- [ ] `--full` descriptions / `aa tool show <id>` for the truncated table column.
- [ ] `version.txt` ↔ manifest sync automation (PRD P2 release-engineering item).

---

## Conflicts Between the 5 Passes — Resolutions

| Disagreement | Passes | Resolution |
|--------------|--------|------------|
| **`cmd_run`: wrap `os.execvpe` in try/except (keep process replacement) vs delete it entirely** | DevOps R4 / TechLead E-6 propose the `try/except OSError → 126` wrapper; Architect #4 / UI-UX U1 / Analyst L#1 propose full delegation to `orch.run_tool()` | **Delete and delegate.** Process replacement (`execvpe`) is not a TTY requirement here; delegation restores exit-code fidelity, sentinel 126, MCP stdio handling, and the `python3 -m` fallback in one shot and removes the DRY violation permanently. The execvpe wrapper is the weaker fix. |
| **Fix the `git log --count` flag in ~10 inlined copies vs consolidate first** | DevOps R2 notes the consolidation; Architect #18/#19 propose extracting | **Consolidate first (P1-7), then fix the flag once.** Patching 10 copies is exactly the hazard that produced the bug. |
| **P0-1: convert classes to module functions vs `SimpleNamespace` wrapper** | Architect / Analyst prefer the AES404 module-function conversion; TechLead's fixed code uses `SimpleNamespace` over an instance | **Two-phase:** `SimpleNamespace` wiring in the merge PR (crash fix, zero convention risk), module-level function conversion as the AES404 follow-up. |
| **Adapter file count 12 vs 13** | All passes agree after correction | 12 files, 13 ids. Docs fixed in P2-6. |
| **TOL-04 status** | DevOps CI3: "In Progress mid-release risks invalidating TOL-01 evidence"; Architect #13: "already done, close it" | Evidence the current 4-file state with a commit hash, mark TOL-04 Done, and re-run the full gate (compileall + `aa check` + import smoke). |
| **`recorded_at` "now"** | Architect #20, DevOps O1, Analyst L#3, TechLead CQ-2 — all agree | ISO-8601 UTC timestamp (P1-8). |
| **`_ADAPTERS` rename** | Architect #2 renames to `self._adapters`; TechLead D-1 keeps the name `self._ADAPTERS = dict(registry)` | Use the instance-level rename `self._adapters` (cleaner; single diff, and the class attribute is removed anyway). |

## Sequencing & Gate

1. **PR 1 (merge-blocking):** P0-1 (interim `SimpleNamespace`), P0-2, P0-3, P0-4, P0-5, plus P1-1/2/3/4 (they are small and protect the same "nothing raises" contract). Gate: compileall + import smoke + `aa check` + P0-1 smoke commands.
2. **PR 2:** P0-6 clean-host sweep (provisioning recipe + evidence rows) — after PR 1 lands, so evidence reflects the fixed tree.
3. **PR 3:** P1 batch (P1-5 … P1-16).
4. **PR 4:** P2 batch + P3 items as capacity allows.
5. Every PR closes with `aa check` green; scenario evidence rows filled with commit + output.

## Severity Legend

| Level | Meaning |
|-------|---------|
| P0 | Crash, CI break, release blocker. Fix before merge. |
| P1 | Contract violation, security hardening, data-integrity. Fix this cycle. |
| P2 | UX, observability, docs, test infra. Fix this cycle or explicitly defer. |
| P3 | Suggestion. Deferrable. |
