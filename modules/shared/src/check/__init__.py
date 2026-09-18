"""Shared check-domain: contracts for repository verification."""
from modules.shared.src.check.contract_check_aggregate import ICheckAggregate
from modules.shared.src.check.contract_check_protocol import ICheckRunner

__all__ = ["ICheckAggregate", "ICheckRunner"]
