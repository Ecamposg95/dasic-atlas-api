"""Catálogos SAT (CFDI 4.0) — datos oficiales para semilla inicial.

Los catálogos pequeños (≤200 entries) viven aquí como constantes Python y
se siembran al arranque en `app/db/seeds.py::seed_sat_catalogos_pequenos`.
Los catálogos masivos (c_ClaveProdServ ~52K, c_ClaveUnidad ~2.4K) se cargan
vía endpoint admin con XLS oficial del SAT (Fase C).

Cada constante es una lista de tuplas `(codigo, descripcion[, extras...])`.
Versionado: datos a 2026-05 con base en las publicaciones del SAT vigentes
para CFDI 4.0. Si el SAT actualiza un catálogo, regenerar la constante y
correr de nuevo `run_all_seeds` (idempotente — solo inserta lo que falta).
"""

from app.data.sat.formas_pago import FORMAS_PAGO
from app.data.sat.metodos_pago import METODOS_PAGO
from app.data.sat.usos_cfdi import USOS_CFDI
from app.data.sat.regimenes_fiscales import REGIMENES_FISCALES
from app.data.sat.objetos_imp import OBJETOS_IMP
from app.data.sat.impuestos import IMPUESTOS
from app.data.sat.tipos_factor import TIPOS_FACTOR
from app.data.sat.tasas_o_cuotas import TASAS_O_CUOTAS
from app.data.sat.monedas import MONEDAS
from app.data.sat.tipos_comprobante import TIPOS_COMPROBANTE

__all__ = [
    "FORMAS_PAGO",
    "METODOS_PAGO",
    "USOS_CFDI",
    "REGIMENES_FISCALES",
    "OBJETOS_IMP",
    "IMPUESTOS",
    "TIPOS_FACTOR",
    "TASAS_O_CUOTAS",
    "MONEDAS",
    "TIPOS_COMPROBANTE",
]
