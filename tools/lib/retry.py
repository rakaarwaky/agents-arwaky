"""Generic retry utility — stateless, domain-agnostic (P4-A5)."""
from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_api(
    func: Callable[[], T],
    max_retries: int = 4,
    delay: float = 1.0,
    is_transient: Callable[[Exception], bool] | None = None,
) -> T:
    """Retry a callable with exponential backoff + jitter.

    Only transient errors are retried (controlled by ``is_transient``);
    permanent errors propagate immediately. Raises the last error on
    exhaustion.
    """
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as exc:  # generic retry by design
            last_err = exc
            if is_transient is not None and not is_transient(exc):
                raise
            if attempt < max_retries:
                wait = min(delay * (2 ** attempt) + random.uniform(0, 1), 10)
                time.sleep(wait)
    assert last_err is not None
    raise last_err
