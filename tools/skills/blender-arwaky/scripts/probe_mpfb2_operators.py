from __future__ import annotations

import bpy

namespace = getattr(bpy.ops, "mpfb", None)
print("MPFB_NAMESPACE", namespace)
print("MPFB_OPERATORS", sorted(name for name in dir(namespace) if not name.startswith("_")))
for name in sorted(name for name in dir(namespace) if not name.startswith("_")):
    operator = getattr(namespace, name)
    try:
        print("OPERATOR", name, operator.get_rna_type().name)
    except Exception as error:
        print("OPERATOR_ERROR", name, type(error).__name__, str(error))
