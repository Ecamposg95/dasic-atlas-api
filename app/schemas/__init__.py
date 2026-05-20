"""
Schemas — re-export central.

Organización por dominio:

  auth.py     → Token, TokenData, LoginRequest, UsuarioBase, UsuarioCreate, UsuarioResponse
  catalog.py  → Producto*, Promocion*, ProductoInfo
  clients.py  → Cliente*, Proveedor*
  finance.py  → Transaccion*
  sales.py    → OrdenVenta*, DetalleOrden*
"""

from app.schemas.auth import (  # noqa: F401
    Token,
    TokenData,
    LoginRequest,
    UsuarioBase,
    UsuarioCreate,
    UsuarioResponse,
)

from app.schemas.catalog import (  # noqa: F401
    ProductoBase,
    ProductoCreate,
    ProductoUpdate,
    ProductoResponseVendedor,
    ProductoResponseAdmin,
    ProductoInfo,
    PromocionBase,
    PromocionCreate,
    PromocionResponse,
    MarcaCreate,
    MarcaUpdate,
    MarcaResponse,
)

from app.schemas.clients import (  # noqa: F401
    ClienteBase,
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ProveedorBase,
    ProveedorCreate,
    ProveedorResponse,
)

from app.schemas.finance import (  # noqa: F401
    TransaccionCreate,
    TransaccionResponse,
)

from app.schemas.sales import (  # noqa: F401
    DetalleOrdenCreate,
    DetalleOrdenResponse,
    OrdenVentaCreate,
    OrdenVentaResponse,
)

from app.schemas.fx import TipoCambioDiaResponse  # noqa: F401
from app.schemas.inventory import (  # noqa: F401
    MovimientoStockResponse,
    AjusteManualIn,
    DisponibilidadResponse,
)

from app.schemas.sat import (  # noqa: F401
    SatFormaPagoResponse,
    SatMetodoPagoResponse,
    SatUsoCfdiResponse,
    SatRegimenFiscalResponse,
    SatObjetoImpResponse,
    SatImpuestoResponse,
    SatTipoFactorResponse,
    SatTasaOCuotaResponse,
    SatMonedaResponse,
    SatTipoComprobanteResponse,
    SatClaveProdServResponse,
    SatClaveUnidadResponse,
)

from app.schemas.services import (  # noqa: F401
    ServicioBase,
    ServicioCreate,
    ServicioUpdate,
    ServicioResponse,
)

from app.schemas.fantasmas import (  # noqa: F401
    ProductoFantasmaBase,
    ProductoFantasmaResponse,
    ProductoFantasmaUpdate,
)

__all__ = [
    # auth
    "Token", "TokenData", "LoginRequest",
    "UsuarioBase", "UsuarioCreate", "UsuarioResponse",
    # catalog
    "ProductoBase", "ProductoCreate", "ProductoUpdate",
    "ProductoResponseVendedor", "ProductoResponseAdmin", "ProductoInfo",
    "PromocionBase", "PromocionCreate", "PromocionResponse",
    # clients
    "ClienteBase", "ClienteCreate", "ClienteUpdate", "ClienteResponse",
    "ProveedorBase", "ProveedorCreate", "ProveedorResponse",
    # finance
    "TransaccionCreate", "TransaccionResponse",
    # sales
    "DetalleOrdenCreate", "DetalleOrdenResponse",
    "OrdenVentaCreate", "OrdenVentaResponse",
    # fx
    "TipoCambioDiaResponse",
    # inventory
    "MovimientoStockResponse", "AjusteManualIn", "DisponibilidadResponse",
    # sat
    "SatFormaPagoResponse", "SatMetodoPagoResponse", "SatUsoCfdiResponse",
    "SatRegimenFiscalResponse", "SatObjetoImpResponse", "SatImpuestoResponse",
    "SatTipoFactorResponse", "SatTasaOCuotaResponse", "SatMonedaResponse",
    "SatTipoComprobanteResponse", "SatClaveProdServResponse", "SatClaveUnidadResponse",
    # services
    "ServicioBase", "ServicioCreate", "ServicioUpdate", "ServicioResponse",
    # fantasmas
    "ProductoFantasmaBase", "ProductoFantasmaResponse", "ProductoFantasmaUpdate",
]
