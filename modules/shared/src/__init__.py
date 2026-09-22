"""Shared flat module namespace — import via ``modules.shared.src.<module>``.

All shared taxonomy, contract, and utility modules live directly here:

- taxonomy_*: value objects + domain constants
- contract_*: capability protocol ABCs
- utility_*: stateless helpers / I/O utilities
"""
from modules.shared.src.contract_config_protocol import IConfigModifier, IConfigWriter
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDiagnosticRunner

__all__ = [
    "IConfigModifier",
    "IConfigWriter",
    "IDiagnosticRunner",
    "IDoctorAggregate",
]
