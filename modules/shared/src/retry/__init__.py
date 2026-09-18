"""Retry utility — stateless, domain-agnostic (P4-A5).\n\nMoved from common.retry.\n"""
from __future__ import annotations

from modules.shared.src.retry.utility_retry import retry_api

__all__ = ["retry_api"]
