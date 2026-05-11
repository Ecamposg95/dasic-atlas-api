"""
ORM models — re-export central.

Import de aquí para compatibilidad con el código existente.
Modelos organizados por dominio:

  enums.py      → RolUsuario, EstatusOrden, TipoMovimiento
  users.py      → Usuario
  catalog.py    → Producto, Promocion, Marca
  clients.py    → Cliente, Proveedor
  finance.py    → TransaccionCliente, TransaccionProveedor
  sales.py      → OrdenVenta, DetalleOrden
  purchases.py  → OrdenCompra, DetalleCompra
  quote_events.py → QuoteEvent
"""

from app.db import Base  # noqa: F401

from app.models.enums import (  # noqa: F401
    RolUsuario,
    EstatusOrden,
    TipoMovimiento,
    TipoLineaCotizacion,
    TipoMovimientoStock,
)
from app.models.users import Usuario  # noqa: F401
from app.models.catalog import Producto, Promocion, Marca  # noqa: F401
from app.models.clients import Cliente, Proveedor  # noqa: F401
from app.models.finance import (  # noqa: F401
    TransaccionCliente,
    TransaccionProveedor,
)
from app.models.sales import OrdenVenta, DetalleOrden  # noqa: F401
from app.models.purchases import OrdenCompra, DetalleCompra  # noqa: F401
from app.models.quote_events import QuoteEvent  # noqa: F401
from app.models.inventory import MovimientoStock  # noqa: F401
from app.models.fx import TipoCambioDia  # noqa: F401
from app.models.expenses import Gasto  # noqa: F401
from app.models.plantillas import PlantillaCotizacion  # noqa: F401

__all__ = [
    "Base",
    "RolUsuario", "EstatusOrden", "TipoMovimiento",
    "TipoLineaCotizacion", "TipoMovimientoStock",
    "Usuario",
    "Producto", "Promocion", "Marca",
    "Cliente", "Proveedor",
    "TransaccionCliente", "TransaccionProveedor",
    "OrdenVenta", "DetalleOrden",
    "OrdenCompra", "DetalleCompra",
    "QuoteEvent",
    "MovimientoStock",
    "TipoCambioDia",
    "Gasto",
    "PlantillaCotizacion",
]
