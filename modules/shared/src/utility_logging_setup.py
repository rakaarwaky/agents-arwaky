"""UI helpers: colors/banner/log (Python).
Moved as-is from tools/lib/ui.py (logging domain)."""
from __future__ import annotations

import logging
import os
import re
import sys

# Structured logging (P1-O1): level + timestamp + correlation ID on log output
_logger = logging.getLogger("agents-arwaky")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _fmt = "%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s"
    _handler.setFormatter(logging.Formatter(_fmt, datefmt="%H:%M:%S"))

    class _CorrelationFilter(logging.Filter):
        def filter(self, record):
            """Attach the correlation id to every log record from the ARWAKY_CORRELATION_ID env var."""
            record.correlation_id = os.environ.get("ARWAKY_CORRELATION_ID", "-")
            return True

    _handler.addFilter(_CorrelationFilter())
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


def log_debug(msg):
    """Write a DEBUG-level message through the agents-arwaky logger."""


def log_info(msg):
    """Write an INFO-level message through the agents-arwaky logger."""


def log_warning(msg):
    """Write a WARNING-level message through the agents-arwaky logger."""


def set_verbosity(level: str = "info") -> None:
    """Set logger verbosity: debug|info|warning|error (global -v/-q)."""
    _logger.setLevel(getattr(logging, level.upper(), logging.INFO))


_color_override = None


def set_color_mode(enabled):
    """Override color detection. None = auto-detect."""
    global _color_override
    _color_override = enabled


def _color_enabled() -> bool:
    if _color_override is not None:
        return _color_override
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    return sys.stdout.isatty()


def _c(code: str) -> str:
    """Lazy color escape — evaluated at call time, not import time."""
    return f"\033[{code}m" if _color_enabled() else ""


# Lazy color accessors: evaluated at call time, not import time,
# so set_color_mode()/NO_COLOR/FORCE_COLOR always take effect.
def BOLD() -> str:
    """Return the ANSI escape for bold weight (empty when colour is disabled)."""
    return _c("1")


def DIM() -> str:
    """Return the ANSI escape for faint/dim weight."""
    return _c("2")


def GREEN() -> str:
    """Return the ANSI escape for green foreground."""
    return _c("0;32")


def BLUE() -> str:
    """Return the ANSI escape for blue foreground."""
    return _c("0;34")


def CYAN() -> str:
    """Return the ANSI escape for cyan foreground."""
    return _c("0;36")


def YELLOW() -> str:
    """Return the ANSI escape for yellow foreground."""
    return _c("0;33")


def RED() -> str:
    """Return the ANSI escape for red foreground."""
    return _c("0;31")


def RESET() -> str:
    """Return the ANSI escape that resets all attributes."""
    return _c("0")


def _term_width() -> int:
    """Current terminal width in columns, with a safe fallback."""
    try:
        import shutil
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


def banner() -> None:
    """Print the agents-arwaky ASCII-art banner (plain text on non-TTY)."""
    if not sys.stdout.isatty():
        # Non-TTY: plain text, avoid broken ASCII art in pipe/log.
        print("agents-arwaky — Unified Tool Orchestrator")
        print()
        return
    print(f"{CYAN()}{BOLD()}   ___                           _          {RESET()}")
    print(f"{CYAN()}{BOLD()}  / _ | _______    _____ _ / /____ __   {RESET()}")
    print(f"{CYAN()}{BOLD()} / __ |/ __/ _ \\/\\/ _ `/  '_/ // /   {RESET()}")
    print(f"{CYAN()}{BOLD()}/_/ |_/_/  \\_/\\_/\\_,_/_/\\_\\\\_, /    {RESET()}")
    print(f"{CYAN()}{BOLD()}                           /___/     {RESET()}")
    print(f"{DIM()} agents-arwaky Unified Tool Orchestrator (Python, per-tool){RESET()}")
    print()


def info(msg: str) -> None:
    """Print a cyan '==>' styled heading to stdout."""
    print(f"{CYAN()}==>{RESET()} {BOLD()}{msg}{RESET()}")


def sub(msg: str) -> None:
    """Print a blue '->' indented message to stdout."""
    print(f"  {BLUE()}->{RESET()} {msg}")


def ok(msg: str) -> None:
    """Print a green '[OK]' confirmation message to stdout."""
    print(f"  {GREEN()}[OK]{RESET()} {msg}")


def warn(msg: str) -> None:
    """Print a yellow '[WARN]' warning message to stdout."""
    print(f"  {YELLOW()}[WARN]{RESET()} {msg}")


def err(msg: str) -> None:
    """Print a red '[FAIL]' error message to stderr."""
    print(f"  {RED()}[FAIL]{RESET()} {msg}", file=sys.stderr)


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _harden_stdio() -> None:
    """Prevent UnicodeEncodeError crashes under C/POSIX (ASCII) locales."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")
        except (OSError, ValueError):
            pass


_harden_stdio()


def pad(s: str, width: int) -> str:
    """Pad a possibly-ANSI-colored string to width; truncate with ellipsis."""
    visible = _ANSI_RE.sub("", s)
    if len(visible) > width:
        overflow = len(visible) - width + 1
        s = s[: max(0, len(s) - overflow)] + RESET() + "…"
        visible = _ANSI_RE.sub("", s)
    return s + " " * max(0, width - len(visible))


def table_widths(available: int, weights: list[int]) -> list[int]:
    """Distribute available terminal width across columns by weight."""
    total_w = sum(weights)
    widths = []
    for i, w in enumerate(weights):
        if i == len(weights) - 1:
            widths.append(max(1, available - sum(widths)))
        else:
            widths.append(max(1, int(available * w / total_w)))
    return widths
