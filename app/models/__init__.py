"""
ORM models — re-export central.

Import de aquí para compatibilidad con el código existente.
Los modelos están organizados por dominio en archivos separados:

  enums.py      → RolUsuario, EstatusOrden, TipoMovimiento, BranchType
  nucleus.py    → Organization, Branch, UserOrganization
  users.py      → Usuario
  catalog.py    → Producto, Promocion
  clients.py    → Cliente, Proveedor
  finance.py    → TransaccionCliente, TransaccionProveedor
  sales.py      → OrdenVenta, DetalleOrden
  purchases.py  → OrdenCompra, DetalleCompra
"""

# Rexport de Base (necesario para Alembic)
from app.db import Base  # noqa: F401

# Enums
from app.models.enums import (  # noqa: F401
    RolUsuario,
    EstatusOrden,
    TipoMovimiento,
    BranchType,
)

# Nucleus (multi-tenancy)
from app.models.nucleus import (  # noqa: F401
    Organization,
    Branch,
    UserOrganization,
)

# Users
from app.models.users import Usuario  # noqa: F401

# Catalog
from app.models.catalog import Producto, Promocion  # noqa: F401

# Clients & Suppliers
from app.models.clients import Cliente, Proveedor  # noqa: F401

# Finance
from app.models.finance import (  # noqa: F401
    TransaccionCliente,
    TransaccionProveedor,
)

# Sales
from app.models.sales import OrdenVenta, DetalleOrden  # noqa: F401

# Purchases
from app.models.purchases import OrdenCompra, DetalleCompra  # noqa: F401

__all__ = [
    "Base",
    # enums
    "RolUsuario", "EstatusOrden", "TipoMovimiento", "BranchType",
    # nucleus
    "Organization", "Branch", "UserOrganization",
    # users
    "Usuario",
    # catalog
    "Producto", "Promocion",
    # clients
    "Cliente", "Proveedor",
    # finance
    "TransaccionCliente", "TransaccionProveedor",
    # sales
    "OrdenVenta", "DetalleOrden",
    # purchases
    "OrdenCompra", "DetalleCompra",
]
