"""Skills-design shared kernel — observability layer.

Logging setup, colors, banners, and structured log helpers for the skills
feature.
"""
from shared.src.observability.utility_logging_setup import (
    BOLD,
    CYAN,
    DIM,
    RED,
    RESET,
    banner,
    err,
    info,
)

__all__ = [
    "BOLD",
    "CYAN",
    "DIM",
    "RED",
    "RESET",
    "banner",
    "err",
    "info",
]
