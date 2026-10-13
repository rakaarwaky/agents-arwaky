---
name: capability-di-seam
description: "Constructing capabilities_* without its injected adapter."
metadata:
  tags:
    - aes
    - capability
    - di
    - protocol
    - silent-failure
    - qwen-web-arwaky
---

# Capability DI Seam: Never Construct a Capability Without Its Concrete Adapter

A `capabilities_*` class in this AES layout owns a protocol-typed DI field
(e.g. `SessionHealthChecker.browser: IBrowserProtocol`). That field is
injected from the Root container or the Surface in normal operation.

## The Bug Class

When a Surface constructs the capability in-process — AES205: Surface
cannot import the Root container, so it must build the concrete adapter
itself — and leaves the DI field at its default (`None` / omitted kwarg),
every method that depends on the seam **silently short-circuits to a
default-sentinel value** instead of raising:

- `check_session` returns `False` → the pool state writer marks every
  session as LIMITED even when all are healthy.
- The command appears to run to completion; the error is a wrong
diagnosis, not a crash.

This has hit `cmd_health_check` (CLI) and `_run_session_health_check`
(TUI) at the same shape. The shape is general: any capability that
consumes a protocol-typed adapter where the adapter is the only real I/O
will fail silently when constructed without it.

## The Rule

When a Surface layer constructs a capability in-process:

1. **Always pass the concrete adapter** the capability needs:
   ```python
   checker = SessionHealthChecker(browser=BrowserAdapter(), timeout_seconds=10)
   ```
   Never `SessionHealthChecker()` — that is inert.
2. **The concrete adapter import belongs in the Surface**, not in the
capability. A lazy `from modules.browser.src... import BrowserAdapter`
inside a `capabilities_*` method is rejected by `lint-arwaky-cli`
AES201 FORBIDDEN_IMPORT (self-import between capabilities modules).
3. **Regression test shape**: patch the capability constructor to capture
the adapter kwarg; assert it is the expected concrete type; feed a fake
page seam so no real browser launch happens in CI:
   ```python
   def _ctor_spy(*args, **kwargs):
       captured['browser_arg'] = kwargs.get('browser')
       kwargs['browser'] = _fake_seam()      # no Chromium launch
       return SessionHealthChecker(**kwargs)

   with patch('...SessionHealthChecker', side_effect=_ctor_spy):
       rc = cmd_health_check(manager)
   assert isinstance(captured['browser_arg'], BrowserAdapter)
   ```
4. **Verify by behaviour, not by type only**: after the fix, run the
command against a known-good session and confirm the pool status does
not flip to LIMITED. A type assertion alone cannot catch a seam that
is wired but misconfigured.

## Pitfall: sync wrappers hide the inert state

`check_pool_sync` is a convenience method that fans out to
`check_session` per session. It does not add its own guard against an
inert checker — the sentinel `False` from `check_session` is silently
aggregated into the results list. The caller then writes
`mark_limited(session_id)` for every session, corrupting the pool state
on disk. Always check whether the called method has a `browser is None`
early-return before assuming it will raise on a misconfigured
construction.

## Where This Applies

- `modules/session/src/capabilities_session_health_checker.py` — `browser` field
- `modules/session/src/capabilities_session_rotation_adapter.py` — `health_checker` field
- Any future `capabilities_*` that consumes a protocol-typed adapter as its only real I/O path
