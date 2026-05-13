"""c_TipoDeComprobante (CFDI 4.0)."""

TIPOS_COMPROBANTE: list[tuple[str, str]] = [
    ("I", "Ingreso"),
    ("E", "Egreso"),
    ("T", "Traslado"),
    ("N", "Nómina"),
    ("P", "Pago"),
]
