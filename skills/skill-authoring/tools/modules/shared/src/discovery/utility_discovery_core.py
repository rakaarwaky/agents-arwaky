"""Cross-process locking primitive (AES utility layer).

Holds ``cross_process_lock`` — the fcntl/msvcrt lock primitive that
``utility_skills_mutation.atomic_write_json`` uses to serialize
concurrent JSON writers. The tree-walking and frontmatter-parsing
helpers live in ``utility_discovery_tree``; both sibling utility
files remain independent (AES201) and import only from the taxonomy
layer.
"""

from __future__ import annotations

__all__ = [
    "cross_process_lock",
]


def cross_process_lock(handle: object) -> None:
    """Take an exclusive, blocking cross-process lock on *handle*.

    Uses ``fcntl.flock`` on POSIX and ``msvcrt.locking`` on Windows.
    The caller is responsible for unlocking; see the consumers'
    ``_with_lock`` / ``_unlock_file`` wrappers.
    """
    try:
        import fcntl as _fcntl
    except ImportError:  # pragma: no cover - POSIX only
        _fcntl = None
    try:
        import msvcrt as _msvcrt
    except ImportError:  # pragma: no cover - Windows only
        _msvcrt = None

    if _fcntl is not None:
        _fcntl.flock(handle.fileno(), _fcntl.LOCK_EX)
    elif _msvcrt is not None:
        handle.flush()
        _msvcrt.locking(handle.fileno(), _msvcrt.LK_LOCK, (1 << 31) - 1)
