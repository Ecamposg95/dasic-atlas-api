"""Router de catálogos SAT (CFDI 4.0) — sólo lectura.

Endpoints:
  GET /api/sat/forma-pago
  GET /api/sat/metodo-pago
  GET /api/sat/uso-cfdi
  GET /api/sat/regimen-fiscal
  GET /api/sat/objeto-imp
  GET /api/sat/impuesto
  GET /api/sat/tipo-factor
  GET /api/sat/tasa-o-cuota
  GET /api/sat/moneda
  GET /api/sat/tipo-comprobante
  GET /api/sat/clave-prod-serv?q=...&limit=20      (typeahead masivo)
  GET /api/sat/clave-unidad?q=...&limit=20         (typeahead masivo)

Los catálogos SAT son canon del SAT — no se editan desde la app. Todos los
endpoints requieren staff autenticado.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_all_staff

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sat", tags=["Catálogos SAT"])


# ---------------------------------------------------------------------------
# Catálogos pequeños (devuelven todo, son chicos)
# ---------------------------------------------------------------------------

@router.get("/forma-pago", response_model=list[schemas.SatFormaPagoResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_forma_pago(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatFormaPago)
    if activo is not None:
        q = q.filter(models.SatFormaPago.activo == activo)
    return q.order_by(models.SatFormaPago.codigo).all()


@router.get("/metodo-pago", response_model=list[schemas.SatMetodoPagoResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_metodo_pago(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatMetodoPago)
    if activo is not None:
        q = q.filter(models.SatMetodoPago.activo == activo)
    return q.order_by(models.SatMetodoPago.codigo).all()


@router.get("/uso-cfdi", response_model=list[schemas.SatUsoCfdiResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_uso_cfdi(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatUsoCfdi)
    if activo is not None:
        q = q.filter(models.SatUsoCfdi.activo == activo)
    return q.order_by(models.SatUsoCfdi.codigo).all()


@router.get("/regimen-fiscal", response_model=list[schemas.SatRegimenFiscalResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_regimen_fiscal(
    activo: Optional[bool] = True,
    persona_fisica: Optional[bool] = None,
    persona_moral: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.SatRegimenFiscal)
    if activo is not None:
        q = q.filter(models.SatRegimenFiscal.activo == activo)
    if persona_fisica is True:
        q = q.filter(models.SatRegimenFiscal.aplica_persona_fisica == True)  # noqa: E712
    if persona_moral is True:
        q = q.filter(models.SatRegimenFiscal.aplica_persona_moral == True)  # noqa: E712
    return q.order_by(models.SatRegimenFiscal.codigo).all()


@router.get("/objeto-imp", response_model=list[schemas.SatObjetoImpResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_objeto_imp(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatObjetoImp)
    if activo is not None:
        q = q.filter(models.SatObjetoImp.activo == activo)
    return q.order_by(models.SatObjetoImp.codigo).all()


@router.get("/impuesto", response_model=list[schemas.SatImpuestoResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_impuesto(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatImpuesto)
    if activo is not None:
        q = q.filter(models.SatImpuesto.activo == activo)
    return q.order_by(models.SatImpuesto.codigo).all()


@router.get("/tipo-factor", response_model=list[schemas.SatTipoFactorResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_tipo_factor(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatTipoFactor)
    if activo is not None:
        q = q.filter(models.SatTipoFactor.activo == activo)
    return q.order_by(models.SatTipoFactor.codigo).all()


@router.get("/tasa-o-cuota", response_model=list[schemas.SatTasaOCuotaResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_tasa_o_cuota(
    activo: Optional[bool] = True,
    impuesto: Optional[str] = None,
    retencion: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.SatTasaOCuota)
    if activo is not None:
        q = q.filter(models.SatTasaOCuota.activo == activo)
    if impuesto:
        q = q.filter(models.SatTasaOCuota.impuesto == impuesto)
    if retencion is not None:
        q = q.filter(models.SatTasaOCuota.es_retencion == retencion)
    return q.order_by(models.SatTasaOCuota.id_local).all()


@router.get("/moneda", response_model=list[schemas.SatMonedaResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_moneda(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatMoneda)
    if activo is not None:
        q = q.filter(models.SatMoneda.activo == activo)
    return q.order_by(models.SatMoneda.codigo).all()


@router.get("/tipo-comprobante", response_model=list[schemas.SatTipoComprobanteResponse],
            dependencies=[Depends(allow_all_staff)])
def listar_tipo_comprobante(activo: Optional[bool] = True, db: Session = Depends(get_db)):
    q = db.query(models.SatTipoDeComprobante)
    if activo is not None:
        q = q.filter(models.SatTipoDeComprobante.activo == activo)
    return q.order_by(models.SatTipoDeComprobante.codigo).all()


# ---------------------------------------------------------------------------
# Catálogos masivos — typeahead (requieren `q` con ≥2 chars)
# ---------------------------------------------------------------------------

@router.get("/clave-prod-serv", response_model=list[schemas.SatClaveProdServResponse],
            dependencies=[Depends(allow_all_staff)])
def buscar_clave_prod_serv(
    q: str = Query(..., min_length=2, description="Código o palabra clave"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Busca en c_ClaveProdServ (~52K). Match por código exacto/prefijo o
    LIKE en descripción y palabras_clave. Si la tabla está vacía (importer
    aún no corrido), devuelve []."""
    needle = q.strip()
    if not needle:
        return []
    pattern = f"%{needle}%"
    rows = (
        db.query(models.SatClaveProdServ)
          .filter(models.SatClaveProdServ.activo == True)  # noqa: E712
          .filter(or_(
              models.SatClaveProdServ.codigo.ilike(f"{needle}%"),
              models.SatClaveProdServ.descripcion.ilike(pattern),
              models.SatClaveProdServ.palabras_clave.ilike(pattern),
          ))
          .order_by(models.SatClaveProdServ.codigo)
          .limit(limit)
          .all()
    )
    return rows


@router.get("/clave-prod-serv/{codigo}", response_model=schemas.SatClaveProdServResponse,
            dependencies=[Depends(allow_all_staff)])
def obtener_clave_prod_serv(codigo: str, db: Session = Depends(get_db)):
    row = db.get(models.SatClaveProdServ, codigo)
    if not row:
        raise HTTPException(status_code=404, detail="Clave SAT no encontrada")
    return row


@router.get("/clave-unidad", response_model=list[schemas.SatClaveUnidadResponse],
            dependencies=[Depends(allow_all_staff)])
def buscar_clave_unidad(
    q: str = Query(..., min_length=1, description="Código, nombre o símbolo"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Busca en c_ClaveUnidad (~2.4K). Match por código (prefijo), nombre o
    símbolo. Si la tabla está vacía (importer aún no corrido), devuelve []."""
    needle = q.strip()
    if not needle:
        return []
    pattern = f"%{needle}%"
    rows = (
        db.query(models.SatClaveUnidad)
          .filter(models.SatClaveUnidad.activo == True)  # noqa: E712
          .filter(or_(
              models.SatClaveUnidad.codigo.ilike(f"{needle}%"),
              models.SatClaveUnidad.nombre.ilike(pattern),
              models.SatClaveUnidad.simbolo.ilike(pattern),
          ))
          .order_by(models.SatClaveUnidad.codigo)
          .limit(limit)
          .all()
    )
    return rows


@router.get("/clave-unidad/{codigo}", response_model=schemas.SatClaveUnidadResponse,
            dependencies=[Depends(allow_all_staff)])
def obtener_clave_unidad(codigo: str, db: Session = Depends(get_db)):
    row = db.get(models.SatClaveUnidad, codigo)
    if not row:
        raise HTTPException(status_code=404, detail="Clave Unidad SAT no encontrada")
    return row
