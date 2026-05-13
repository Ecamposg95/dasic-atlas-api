"""c_Moneda (CFDI 4.0) — Subset operacional ISO 4217.

El catálogo SAT incluye ~180 monedas. Aquí cargamos las que típicamente
usa una empresa industrial mexicana. Si se necesita otra, agregar y
re-sembrar.

Estructura: (codigo, descripcion, decimales, percent_variacion)
- decimales: precisión decimal de la moneda
- percent_variacion: tolerancia de variación de tipo de cambio según SAT
"""

MONEDAS: list[tuple[str, str, int]] = [
    ("MXN", "Peso Mexicano", 2),
    ("USD", "Dólar de los Estados Unidos de América", 2),
    ("EUR", "Euro", 2),
    ("CAD", "Dólar Canadiense", 2),
    ("GBP", "Libra Esterlina", 2),
    ("JPY", "Yen Japonés", 0),
    ("CNY", "Yuan Renminbi (China)", 2),
    ("BRL", "Real Brasileño", 2),
    ("ARS", "Peso Argentino", 2),
    ("COP", "Peso Colombiano", 2),
    ("CLP", "Peso Chileno", 0),
    ("PEN", "Sol Peruano", 2),
    ("CHF", "Franco Suizo", 2),
    ("XXX", "Los códigos asignados para las transacciones en que intervenga ninguna moneda", 0),
]
