"""
Enums compartidos usados por múltiples dominios.
Importar desde aquí para evitar dependencias circulares.
"""

import enum


class RolUsuario(str, enum.Enum):
    ADMIN = "admin"
    ASISTENTE = "asistente"
    VENDEDOR = "vendedor"


class EstatusOrden(str, enum.Enum):
    COTIZACION = "cotizacion"
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    CANCELADA = "cancelada"


class TipoMovimiento(str, enum.Enum):
    CARGO = "cargo"
    ABONO = "abono"


class BranchType(str, enum.Enum):
    HQ = "HQ"
    PLANT = "PLANT"
    WAREHOUSE = "WAREHOUSE"
    OFFICE = "OFFICE"
