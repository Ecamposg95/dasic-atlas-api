"""Schemas Pydantic para catálogos SAT (CFDI 4.0).

Read-only: los catálogos no se editan desde la app (son canon SAT). Los
únicos creates posibles son via importer de Fase C para sat_clave_prodserv
y sat_clave_unidad, que se hacen en bulk y no necesitan schema POST público.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class _BaseSatCatalogoResponse(BaseModel):
    """Estructura común para los 8 catálogos simples (código + descripción)."""
    codigo: str
    descripcion: str
    activo: bool
    model_config = ConfigDict(from_attributes=True)


class SatFormaPagoResponse(_BaseSatCatalogoResponse):
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None


class SatMetodoPagoResponse(_BaseSatCatalogoResponse):
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None


class SatUsoCfdiResponse(_BaseSatCatalogoResponse):
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None


class SatRegimenFiscalResponse(_BaseSatCatalogoResponse):
    aplica_persona_fisica: bool
    aplica_persona_moral: bool
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None


class SatObjetoImpResponse(_BaseSatCatalogoResponse):
    pass


class SatImpuestoResponse(_BaseSatCatalogoResponse):
    aplica_traslado: bool
    aplica_retencion: bool


class SatTipoFactorResponse(_BaseSatCatalogoResponse):
    pass


class SatTasaOCuotaResponse(BaseModel):
    id_local: str
    impuesto: str
    tipo_factor: str
    valor: Decimal
    descripcion: str
    es_retencion: bool
    activo: bool
    model_config = ConfigDict(from_attributes=True)


class SatMonedaResponse(_BaseSatCatalogoResponse):
    decimales: str


class SatTipoComprobanteResponse(_BaseSatCatalogoResponse):
    pass


class SatClaveProdServResponse(_BaseSatCatalogoResponse):
    palabras_clave: Optional[str] = None
    incluir_iva_basico: bool = True
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None


class SatClaveUnidadResponse(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    simbolo: Optional[str] = None
    activo: bool
    model_config = ConfigDict(from_attributes=True)
