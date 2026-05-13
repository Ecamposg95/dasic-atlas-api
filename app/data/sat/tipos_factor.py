"""c_TipoFactor (CFDI 4.0) — Tipo de factor para tasa/cuota.

Tasa: porcentaje (ej. 16%).
Cuota: monto fijo por unidad (ej. IEPS especial).
Exento: no causa impuesto.
"""

TIPOS_FACTOR: list[tuple[str, str]] = [
    ("Tasa", "Tasa porcentual aplicada al valor del concepto"),
    ("Cuota", "Cuota fija por unidad gravada"),
    ("Exento", "Concepto exento del impuesto"),
]
