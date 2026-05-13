"""c_MetodoPago (CFDI 4.0) — Método de pago.

PUE: pago en una sola exhibición.
PPD: pago en parcialidades o diferido.
"""

METODOS_PAGO: list[tuple[str, str]] = [
    ("PUE", "Pago en una sola exhibición"),
    ("PPD", "Pago en parcialidades o diferido"),
]
