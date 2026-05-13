"""c_FormaPago (CFDI 4.0) — Forma de pago.

Fuente: catálogo oficial del SAT. 22 entries vigentes.
Estructura: (codigo, descripcion)
"""

FORMAS_PAGO: list[tuple[str, str]] = [
    ("01", "Efectivo"),
    ("02", "Cheque nominativo"),
    ("03", "Transferencia electrónica de fondos"),
    ("04", "Tarjeta de crédito"),
    ("05", "Monedero electrónico"),
    ("06", "Dinero electrónico"),
    ("08", "Vales de despensa"),
    ("12", "Dación en pago"),
    ("13", "Pago por subrogación"),
    ("14", "Pago por consignación"),
    ("15", "Condonación"),
    ("17", "Compensación"),
    ("23", "Novación"),
    ("24", "Confusión"),
    ("25", "Remisión de deuda"),
    ("26", "Prescripción o caducidad"),
    ("27", "A satisfacción del acreedor"),
    ("28", "Tarjeta de débito"),
    ("29", "Tarjeta de servicios"),
    ("30", "Aplicación de anticipos"),
    ("31", "Intermediario de pagos"),
    ("99", "Por definir"),
]
