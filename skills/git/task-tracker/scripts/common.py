"""Shared constants and the gh runner for task-tracker scripts.

Stdlib only. ``gh()`` is used by PR 2's validate.py / ledger.py; scan.py
and classify.py are pure and do not import this module in PR 1.
"""

from __future__ import annotations

import subprocess

# gh CLI invocations never block a run longer than this.
GH_TIMEOUT = 30

# The gh CLI reports HTTP failures only through its stderr text (it exits 1
# for both API errors and local failures); these patterns classify the
# failure class.
_RATE_LIMIT_MARKERS = ("rate limit", "http 403", "http 429", "secondary rate limit")
_AUTH_MARKERS = ("http 401", "authentication failed", "token is invalid", "auth")


class GhRateLimited(Exception):
    """gh returned 403/429 with a retryable rate-limit header."""


class GhAuthError(Exception):
    """gh returned a permanent auth failure (401, bad token)."""


def gh(*args: str, timeout: int = GH_TIMEOUT) -> str:
    """Run the gh CLI; return trimmed stdout on success.

    Propagates gh's stderr into the raised exception. Raise GhRateLimited
    on 403/429, GhAuthError on 401, and RuntimeError for any other
    non-zero exit.

    gh reports HTTP status codes only via stderr text (the exit code is 1
    for every API error), so the failure class is matched against the
    stderr: any 403 response is treated as rate-limited per the design
    (retryable), and 401 / auth-setup failures are permanent.
    """
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout.strip()
    stderr = proc.stderr.strip()
    lowered = stderr.lower()
    if proc.returncode == 429 or any(marker in lowered for marker in _RATE_LIMIT_MARKERS):
        raise GhRateLimited(f"gh {' '.join(args)}: {stderr}")
    if any(marker in lowered for marker in _AUTH_MARKERS):
        raise GhAuthError(f"gh {' '.join(args)}: {stderr}")
    raise RuntimeError(f"gh {' '.join(args)} exited {proc.returncode}: {stderr}")
