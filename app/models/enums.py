"""
Enums compartidos usados por múltiples dominios.
Importar desde aquí para evitar dependencias circulares.
"""

import enum


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "admin"
    GERENTE_COMERCIAL = "asistente"
    VENTAS = "vendedor"

    # Alias legacy para compatibilidad durante la transición RBAC.
    ADMIN = ADMINISTRADOR
    ASISTENTE = GERENTE_COMERCIAL
    VENDEDOR = VENTAS

    @classmethod
    def from_input(cls, value: "RolUsuario | str") -> "RolUsuario":
        if isinstance(value, cls):
            return value

        normalized = str(value).strip().lower()
        lookup = {
            "admin": cls.ADMINISTRADOR,
            "administrador": cls.ADMINISTRADOR,
            "asistente": cls.GERENTE_COMERCIAL,
            "gerente_comercial": cls.GERENTE_COMERCIAL,
            "gerente comercial": cls.GERENTE_COMERCIAL,
            "vendedor": cls.VENTAS,
            "ventas": cls.VENTAS,
        }
        try:
            return lookup[normalized]
        except KeyError as exc:
            raise ValueError(f"Rol no soportado: {value}") from exc

    @property
    def api_value(self) -> str:
        return {
            RolUsuario.ADMINISTRADOR: "administrador",
            RolUsuario.GERENTE_COMERCIAL: "gerente_comercial",
            RolUsuario.VENTAS: "ventas",
        }[self]


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
