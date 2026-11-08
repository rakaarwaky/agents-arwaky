"""Skills-domain errors (AES governance layer).

The governance layer's error surface. All six error classes are
consumed across every module domain (discovery, design, storage,
maintenance, governance, observability), so their canonical
definitions live in ``shared.src.common.taxonomy_common_error``.
This module is empty of definitions; capabilities must import the
error hierarchy from the common layer directly.
"""
