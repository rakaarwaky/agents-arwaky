"""Shared harness-domain: taxonomy + contracts for harness connectors."""
from modules.shared.src.harness.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.harness.contract_harness_protocol import IHarnessConnector
from modules.shared.src.harness.taxonomy_harness_vo import HarnessConfig

__all__ = ["HarnessConfig", "IHarnessAggregate", "IHarnessConnector"]
