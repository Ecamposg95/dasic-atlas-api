"""c_TasaOCuota (CFDI 4.0) — Tasas o cuotas válidas por impuesto.

Cada entry: (id, impuesto, tipo_factor, valor, descripcion, es_retencion)
- valor en formato decimal: 0.160000 = 16%
- es_retencion: True si aplica a retenciones, False si a traslados

Sólo las tasas más comunes. Tasas IEPS específicas por producto (combustibles,
bebidas saborizadas) no incluidas — agregar si el cliente las necesita.
"""

# (id_local, impuesto, tipo_factor, valor, descripcion, es_retencion)
TASAS_O_CUOTAS: list[tuple[str, str, str, str, str, bool]] = [
    # IVA — Traslados
    ("IVA-T-0.16", "002", "Tasa", "0.160000", "IVA 16% — Tasa general", False),
    ("IVA-T-0.08", "002", "Tasa", "0.080000", "IVA 8% — Tasa frontera norte/sur", False),
    ("IVA-T-0.00", "002", "Tasa", "0.000000", "IVA 0% — Tasa cero", False),
    ("IVA-T-EX",   "002", "Exento", "0.000000", "IVA Exento", False),
    # IVA — Retenciones
    ("IVA-R-0.16",          "002", "Tasa", "0.160000",          "IVA Retención 16% (4/4)", True),
    ("IVA-R-0.106667",      "002", "Tasa", "0.106667",          "IVA Retención 2/3 (~10.67%)", True),
    ("IVA-R-0.04",          "002", "Tasa", "0.040000",          "IVA Retención 4% (autotransporte)", True),
    # ISR — Retenciones
    ("ISR-R-0.10",  "001", "Tasa", "0.100000", "ISR Retención 10% (servicios profesionales)", True),
    ("ISR-R-0.20",  "001", "Tasa", "0.200000", "ISR Retención 20% (arrendamiento)", True),
    ("ISR-R-0.21",  "001", "Tasa", "0.210000", "ISR Retención 21% (pago a residentes ext.)", True),
    ("ISR-R-0.25",  "001", "Tasa", "0.250000", "ISR Retención 25%", True),
    ("ISR-R-0.35",  "001", "Tasa", "0.350000", "ISR Retención 35%", True),
    # IEPS — Traslados (tasas más comunes; el SAT publica decenas)
    ("IEPS-T-0.06",    "003", "Tasa", "0.060000", "IEPS 6%", False),
    ("IEPS-T-0.07",    "003", "Tasa", "0.070000", "IEPS 7%", False),
    ("IEPS-T-0.08",    "003", "Tasa", "0.080000", "IEPS 8%", False),
    ("IEPS-T-0.265",   "003", "Tasa", "0.265000", "IEPS 26.5%", False),
    ("IEPS-T-0.30",    "003", "Tasa", "0.300000", "IEPS 30%", False),
    ("IEPS-T-0.53",    "003", "Tasa", "0.530000", "IEPS 53%", False),
    ("IEPS-T-1.60",    "003", "Tasa", "1.600000", "IEPS 160%", False),
    ("IEPS-T-EX",      "003", "Exento", "0.000000", "IEPS Exento", False),
]
