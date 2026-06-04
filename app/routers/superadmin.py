"""Consola super-admin: configuración en runtime + auditoría global."""
import json
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models
from app.db import get_db
from app.security import get_current_user
from app.security.jwt import allow_superadmin
from app.core.runtime_config import EDITABLE_KEYS, effective_summary

router = APIRouter(prefix="/api/superadmin", tags=["Super-Admin"])


class ConfigSet(BaseModel):
    clave: str
    valor: str | None  # null = borra el override (vuelve al default)


def _validar(clave: str, valor: str | None) -> None:
    if clave not in EDITABLE_KEYS:
        raise HTTPException(400, f"Clave no editable: {clave}")
    if valor is None:
        return
    if clave == "iva_rate":
        try:
            v = Decimal(str(valor))
        except (InvalidOperation, ValueError):
            raise HTTPException(400, "iva_rate debe ser número (ej. 0.16)")
        if v < 0 or v > 1:
            raise HTTPException(400, "iva_rate debe estar entre 0 y 1")
    elif clave == "quote_validity_days":
        try:
            n = int(valor)
        except (ValueError, TypeError):
            raise HTTPException(400, "quote_validity_days debe ser entero")
        if n < 1:
            raise HTTPException(400, "quote_validity_days debe ser ≥ 1")


@router.get("/config", dependencies=[Depends(allow_superadmin)])
def get_config(db: Session = Depends(get_db)):
    return {"items": effective_summary(db)}


@router.put("/config", dependencies=[Depends(allow_superadmin)])
def set_config(
    payload: ConfigSet,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    _validar(payload.clave, payload.valor)
    row = db.query(models.PlatformConfig).filter(models.PlatformConfig.clave == payload.clave).first()
    if payload.valor is None:
        if row:
            db.delete(row)
    else:
        if row:
            row.valor = payload.valor
            row.actualizado_por_id = current_user.id
        else:
            db.add(models.PlatformConfig(clave=payload.clave, valor=payload.valor, actualizado_por_id=current_user.id))
    db.commit()
    return {"items": effective_summary(db)}


# ---------------------------------------------------------------------------
# Auditoría global (Módulo B): agrega eventos ya registrados, read-only.
# ---------------------------------------------------------------------------

class AuditEvent(BaseModel):
    fuente: Literal["cotizacion", "fusion_cliente"]
    fecha: datetime
    usuario: str | None
    usuario_id: int | None
    accion: str
    entidad: str
    detalle: str
    link: str | None


def _accion_quote(canal: str | None, estatus: str | None, meta: dict) -> str:
    c = (canal or "").upper()
    if c == "NOTE":
        acc = str(meta.get("accion") or "").lower()
        return "Cotización recotizada" if "recotiz" in acc else "Cotización editada"
    if c == "EMAIL":
        return "Email falló" if (estatus or "").upper() == "FAILED" else "Email enviado"
    if c == "WHATSAPP":
        return "WhatsApp registrado"
    if c == "IA":
        return "Sugerencia IA"
    return f"Evento {c or '—'}"


def _detalle_quote(ev, meta: dict) -> str:
    if ev.asunto:
        return ev.asunto
    ta, tn = meta.get("total_anterior"), meta.get("total_nuevo")
    if ta is not None and tn is not None:
        return f"Total {ta} → {tn}"
    if meta.get("sugerencia"):
        return str(meta["sugerencia"])[:160]
    return ""


def _normalize_quote_event(ev, folio_map: dict, nombre_map: dict) -> AuditEvent:
    try:
        meta = json.loads(ev.metadata_json) if ev.metadata_json else {}
        if not isinstance(meta, dict):
            meta = {}
    except Exception:
        meta = {}
    folio = folio_map.get(ev.orden_id)
    return AuditEvent(
        fuente="cotizacion",
        fecha=ev.creado_en,
        usuario=(nombre_map.get(ev.creado_por_id) or "—") if ev.creado_por_id else "—",
        usuario_id=ev.creado_por_id,
        accion=_accion_quote(ev.canal, ev.estatus, meta),
        entidad=folio or f"Cotización #{ev.orden_id}",
        detalle=_detalle_quote(ev, meta),
        link=f"/spa/seguimiento?orden={ev.orden_id}",
    )


def _normalize_merge_log(row, nombre_map: dict) -> AuditEvent:
    detalle = (
        f"{row.loser_nombre or 'Empresa'} "
        f"(RFC {row.loser_rfc or '—'}, saldo {row.loser_saldo if row.loser_saldo is not None else 0}, "
        f"{row.n_ordenes or 0} órdenes) → survivor #{row.survivor_id}"
    )
    return AuditEvent(
        fuente="fusion_cliente",
        fecha=row.merged_at,
        usuario=(nombre_map.get(row.merged_by_id) or "—") if row.merged_by_id else "—",
        usuario_id=row.merged_by_id,
        accion="Empresas fusionadas",
        entidad=f"Empresa #{row.survivor_id}",
        detalle=detalle,
        link=f"/spa/clientes?id={row.survivor_id}",
    )


@router.get("/audit", dependencies=[Depends(allow_superadmin)])
def get_audit(
    db: Session = Depends(get_db),
    fuente: Optional[Literal["cotizacion", "fusion_cliente"]] = None,
    usuario_id: Optional[int] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    # --- quote_events ---
    if fuente in (None, "cotizacion"):
        q = db.query(models.QuoteEvent)
        if usuario_id is not None:
            q = q.filter(models.QuoteEvent.creado_por_id == usuario_id)
        if desde is not None:
            q = q.filter(models.QuoteEvent.creado_en >= datetime.combine(desde, time.min))
        if hasta is not None:
            q = q.filter(models.QuoteEvent.creado_en <= datetime.combine(hasta, time.max))
        qrows = q.all()
        orden_ids = {e.orden_id for e in qrows}
        folio_map: dict = {}
        if orden_ids:
            for oid, folio in (
                db.query(models.OrdenVenta.id, models.OrdenVenta.folio)
                .filter(models.OrdenVenta.id.in_(orden_ids))
                .all()
            ):
                folio_map[oid] = folio
    else:
        qrows, folio_map = [], {}

    # --- cliente_merge_log ---
    if fuente in (None, "fusion_cliente"):
        m = db.query(models.ClienteMergeLog)
        if usuario_id is not None:
            m = m.filter(models.ClienteMergeLog.merged_by_id == usuario_id)
        if desde is not None:
            m = m.filter(models.ClienteMergeLog.merged_at >= datetime.combine(desde, time.min))
        if hasta is not None:
            m = m.filter(models.ClienteMergeLog.merged_at <= datetime.combine(hasta, time.max))
        mrows = m.all()
    else:
        mrows = []

    # --- resolución batch de nombres (sin N+1) ---
    uids = {e.creado_por_id for e in qrows if e.creado_por_id} | {
        r.merged_by_id for r in mrows if r.merged_by_id
    }
    nombre_map: dict = {}
    if uids:
        for uid, nombre in (
            db.query(models.Usuario.id, models.Usuario.nombre)
            .filter(models.Usuario.id.in_(uids))
            .all()
        ):
            nombre_map[uid] = nombre

    eventos = [_normalize_quote_event(e, folio_map, nombre_map) for e in qrows]
    eventos += [_normalize_merge_log(r, nombre_map) for r in mrows]

    # Orden fecha desc. server_default garantiza fecha no-nula.
    eventos.sort(key=lambda x: x.fecha, reverse=True)
    total = len(eventos)
    start = (page - 1) * page_size
    items = eventos[start : start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
