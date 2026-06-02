"""
Enums compartidos usados por múltiples dominios.
Importar desde aquí para evitar dependencias circulares.
"""

import enum


class RolUsuario(str, enum.Enum):
    SUPERADMIN = "superadmin"          # plataforma cross-tenant
    ADMINISTRADOR = "admin"            # admin del tenant
    GERENTE_COMERCIAL = "asistente"
    VENTAS = "vendedor"
    OPERATIVO = "operativo"            # rol genérico operativo (almacén/soporte)

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
            "superadmin": cls.SUPERADMIN,
            "super_admin": cls.SUPERADMIN,
            "super-admin": cls.SUPERADMIN,
            "admin": cls.ADMINISTRADOR,
            "administrador": cls.ADMINISTRADOR,
            "asistente": cls.GERENTE_COMERCIAL,
            "gerente_comercial": cls.GERENTE_COMERCIAL,
            "gerente comercial": cls.GERENTE_COMERCIAL,
            "vendedor": cls.VENTAS,
            "ventas": cls.VENTAS,
            "operativo": cls.OPERATIVO,
            "operations": cls.OPERATIVO,
            "almacen": cls.OPERATIVO,
            "soporte": cls.OPERATIVO,
        }
        try:
            return lookup[normalized]
        except KeyError as exc:
            raise ValueError(f"Rol no soportado: {value}") from exc

    @property
    def api_value(self) -> str:
        return {
            RolUsuario.SUPERADMIN: "superadmin",
            RolUsuario.ADMINISTRADOR: "administrador",
            RolUsuario.GERENTE_COMERCIAL: "gerente_comercial",
            RolUsuario.VENTAS: "ventas",
            RolUsuario.OPERATIVO: "operativo",
        }[self]

    @property
    def is_admin_tier(self) -> bool:
        return self in {RolUsuario.SUPERADMIN, RolUsuario.ADMINISTRADOR}

    @property
    def is_operativo(self) -> bool:
        return self in {RolUsuario.GERENTE_COMERCIAL, RolUsuario.VENTAS, RolUsuario.OPERATIVO}


class EstatusOrden(str, enum.Enum):
    COTIZACION = "cotizacion"
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    CANCELADA = "cancelada"

    @classmethod
    def _missing_(cls, value):
        # Tolera valores legacy en la DB (mayúsculas, espacios) normalizando
        # a lowercase y matcheando por value o por nombre. Evita que un row
        # con estatus viejo tire queries enteras (.all()) que cargan OrdenVenta.
        if isinstance(value, str):
            v = value.strip().lower()
            for miembro in cls:
                if miembro.value == v or miembro.name.lower() == v:
                    return miembro
        return None


class TipoMovimiento(str, enum.Enum):
    CARGO = "cargo"
    ABONO = "abono"


class TipoLineaCotizacion(str, enum.Enum):
    PRODUCTO_CATALOGO = "producto_catalogo"
    PRODUCTO_FANTASMA = "producto_fantasma"
    SERVICIO = "servicio"


class TipoMovimientoStock(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"
    RESERVA = "reserva"
    LIBERACION = "liberacion"
