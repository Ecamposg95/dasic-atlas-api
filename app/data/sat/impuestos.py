"""c_Impuesto (CFDI 4.0) — Tipos de impuesto.

Aplica para traslados y/o retenciones. Es flag indicativo:
si ambos True el impuesto puede usarse en ambos contextos.
"""

# (codigo, descripcion, traslado, retencion)
IMPUESTOS: list[tuple[str, str, bool, bool]] = [
    ("001", "ISR", False, True),       # solo retención
    ("002", "IVA", True, True),        # traslado y retención
    ("003", "IEPS", True, True),       # traslado y retención
]
