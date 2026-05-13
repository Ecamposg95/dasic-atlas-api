"""Modelos de catálogos SAT (CFDI 4.0).

Los 10 catálogos pequeños se siembran desde `app/data/sat/*.py` en cada
arranque (idempotente, ver `app/db/seeds.py::seed_sat_catalogos_pequenos`).
Los catálogos masivos (`SatClaveProdServ`, `SatClaveUnidad`) se cargan vía
endpoint admin con XLS oficial del SAT — su modelo vive aquí pero la tabla
se llena en Fase C del plan.

Convención: PK es el `codigo` (VARCHAR) — el SAT mismo lo define como tal y
así los joins desde Cliente/Producto/OrdenVenta son por código natural,
sin necesidad de FK a un id sintético.
"""

from sqlalchemy import Boolean, Column, Date, DateTime, DECIMAL, String, Text
from sqlalchemy.sql import func

from app.db import Base


# ---------------------------------------------------------------------------
# Catálogos pequeños (≤ 200 entries, seedeados desde Python)
# ---------------------------------------------------------------------------

class SatFormaPago(Base):
    """c_FormaPago — Forma en que se realiza el pago."""
    __tablename__ = "sat_forma_pago"

    codigo = Column(String(3), primary_key=True)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    vigencia_desde = Column(Date, nullable=True)
    vigencia_hasta = Column(Date, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatMetodoPago(Base):
    """c_MetodoPago — PUE / PPD."""
    __tablename__ = "sat_metodo_pago"

    codigo = Column(String(3), primary_key=True)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    vigencia_desde = Column(Date, nullable=True)
    vigencia_hasta = Column(Date, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatUsoCfdi(Base):
    """c_UsoCFDI — Uso que el receptor le dará al comprobante."""
    __tablename__ = "sat_uso_cfdi"

    codigo = Column(String(5), primary_key=True)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    vigencia_desde = Column(Date, nullable=True)
    vigencia_hasta = Column(Date, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatRegimenFiscal(Base):
    """c_RegimenFiscal — Régimen tributario del contribuyente."""
    __tablename__ = "sat_regimen_fiscal"

    codigo = Column(String(3), primary_key=True)
    descripcion = Column(Text, nullable=False)
    aplica_persona_fisica = Column(Boolean, nullable=False, default=False)
    aplica_persona_moral = Column(Boolean, nullable=False, default=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    vigencia_desde = Column(Date, nullable=True)
    vigencia_hasta = Column(Date, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatObjetoImp(Base):
    """c_ObjetoImp — Objeto del impuesto por concepto."""
    __tablename__ = "sat_objeto_imp"

    codigo = Column(String(2), primary_key=True)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatImpuesto(Base):
    """c_Impuesto — ISR (001), IVA (002), IEPS (003)."""
    __tablename__ = "sat_impuesto"

    codigo = Column(String(3), primary_key=True)
    descripcion = Column(Text, nullable=False)
    aplica_traslado = Column(Boolean, nullable=False, default=False)
    aplica_retencion = Column(Boolean, nullable=False, default=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatTipoFactor(Base):
    """c_TipoFactor — Tasa / Cuota / Exento."""
    __tablename__ = "sat_tipo_factor"

    codigo = Column(String(10), primary_key=True)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatTasaOCuota(Base):
    """c_TasaOCuota — Tasas y cuotas válidas por impuesto.

    A diferencia de los catálogos por código simple, aquí el id es sintético
    porque la combinación (impuesto, valor, retencion) define la entrada.
    """
    __tablename__ = "sat_tasa_o_cuota"

    id_local = Column(String(30), primary_key=True)  # ej. "IVA-T-0.16"
    impuesto = Column(String(3), nullable=False, index=True)
    tipo_factor = Column(String(10), nullable=False)
    valor = Column(DECIMAL(7, 6), nullable=False)
    descripcion = Column(Text, nullable=False)
    es_retencion = Column(Boolean, nullable=False, default=False, index=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatMoneda(Base):
    """c_Moneda — ISO 4217 + decimales SAT."""
    __tablename__ = "sat_moneda"

    codigo = Column(String(3), primary_key=True)
    descripcion = Column(Text, nullable=False)
    decimales = Column(String(2), nullable=False, default="2")
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatTipoDeComprobante(Base):
    """c_TipoDeComprobante — I/E/T/N/P."""
    __tablename__ = "sat_tipo_comprobante"

    codigo = Column(String(2), primary_key=True)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Catálogos masivos (Fase C — el modelo vive aquí; la tabla se llena vía importer)
# ---------------------------------------------------------------------------

class SatClaveProdServ(Base):
    """c_ClaveProdServ — ~52K productos y servicios SAT.

    Búsqueda fuzzy vía pg_trgm + índice GIN (creado en migración Fase C).
    """
    __tablename__ = "sat_clave_prodserv"

    codigo = Column(String(8), primary_key=True)
    descripcion = Column(Text, nullable=False)
    palabras_clave = Column(Text, nullable=True)
    incluir_iva_basico = Column(Boolean, nullable=False, default=True)
    vigencia_desde = Column(Date, nullable=True)
    vigencia_hasta = Column(Date, nullable=True)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SatClaveUnidad(Base):
    """c_ClaveUnidad — ~2.4K unidades de medida SAT (UN/CEFACT)."""
    __tablename__ = "sat_clave_unidad"

    codigo = Column(String(3), primary_key=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    simbolo = Column(String(20), nullable=True)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
