"""Set curado de claves de unidad SAT (c_ClaveUnidad) de uso frecuente.

El catálogo completo (~2.4K) requiere importer del XLS oficial del SAT; este
subconjunto da datos inmediatos al dropdown de captura. Códigos ≤ 3 chars
(la columna codigo es VARCHAR(3))."""

CLAVE_UNIDAD_COMUNES = [
    ("H87", "Pieza"),
    ("EA", "Elemento"),
    ("E48", "Unidad de servicio"),
    ("ACT", "Actividad"),
    ("XUN", "Unidad"),
    ("C62", "Uno"),
    ("KGM", "Kilogramo"),
    ("GRM", "Gramo"),
    ("MGM", "Miligramo"),
    ("TNE", "Tonelada"),
    ("LTR", "Litro"),
    ("MLT", "Mililitro"),
    ("MTR", "Metro"),
    ("CMT", "Centímetro"),
    ("MMT", "Milímetro"),
    ("KMT", "Kilómetro"),
    ("MTK", "Metro cuadrado"),
    ("MTQ", "Metro cúbico"),
    ("XBX", "Caja"),
    ("XPK", "Paquete"),
    ("XRO", "Rollo"),
    ("XBG", "Bolsa"),
    ("SET", "Juego"),
    ("PR", "Par"),
    ("DZN", "Docena"),
    ("HUR", "Hora"),
    ("DAY", "Día"),
    ("WEE", "Semana"),
    ("MON", "Mes"),
    ("ANN", "Año"),
    ("A9", "Tarifa"),
    ("E51", "Trabajo"),
]
