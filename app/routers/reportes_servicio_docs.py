"""Endpoints del documento Reporte de Servicio (acta de servicio ejecutado).

⚠ NO confundir con `routers/reportes.py` ni con el dashboard analítico
`/spa/reportes-servicio`. Este router sirve el documento hijo de una
OrdenVenta — análogo a Remision pero para líneas de tipo servicio.
Prefix `/api/reportes-servicio-docs` para evitar colisión semántica.
"""

import logging
import re
from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from fpdf import FPDF
from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_all_staff, get_current_user

logger = logging.getLogger(__name__)


def _txt(value: Optional[str]) -> str:
    """fpdf2 base font is latin-1 only — strip incompatible chars."""
    if value is None:
        return ""
    return str(value).encode("latin-1", errors="replace").decode("latin-1")

router = APIRouter(
    prefix="/api/reportes-servicio-docs",
    tags=["ReportesServicio (documentos)"],
)


def _generar_folio_rs(db: Session) -> str:
    """Folio RS-YYYYMM-<NNNN> con consecutivo global por mes.

    Mismo patrón validado en `ventas.py::_generar_folio`: advisory lock
    transaccional + MAX(folio) + regex (tolera gaps y sufijos versionados).
    """
    hoy = datetime.utcnow()
    yyyymm = hoy.strftime("%Y%m")
    prefijo = "RS"

    # Advisory lock transaccional: serializa el cómputo entre llamadas concurrentes.
    lock_key = f"folio:{prefijo}:{yyyymm}"
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": lock_key})

    patron = f"{prefijo}-{yyyymm}-%"
    ultimo = (
        db.query(func.max(models.ReporteServicio.folio))
        .filter(models.ReporteServicio.folio.like(patron))
        .scalar()
    )
    consecutivo = 1
    if ultimo:
        m = re.match(rf"{re.escape(prefijo)}-{re.escape(yyyymm)}-(\d+)", ultimo)
        if m:
            consecutivo = int(m.group(1)) + 1
    return f"{prefijo}-{yyyymm}-{consecutivo:04d}"


def _serializar(r: models.ReporteServicio) -> dict:
    return {
        "id": r.id,
        "folio": r.folio,
        "orden_venta_id": r.orden_venta_id,
        "orden_venta_folio": r.orden_venta.folio if r.orden_venta else None,
        "cliente_nombre": (
            r.orden_venta.cliente.nombre_empresa
            if r.orden_venta and r.orden_venta.cliente
            else None
        ),
        "fecha_reporte": r.fecha_reporte.isoformat() if r.fecha_reporte else None,
        "tecnico_nombre": r.tecnico_nombre,
        "cliente_recibe_nombre": r.cliente_recibe_nombre,
        "recibido_at": r.recibido_at.isoformat() if r.recibido_at else None,
        "observaciones": r.observaciones,
        "creado_en": r.creado_en.isoformat() if r.creado_en else None,
    }


@router.get("/", dependencies=[Depends(allow_all_staff)])
def listar(
    orden_venta_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 500:
        raise HTTPException(400, "page o page_size inválido")
    query = db.query(models.ReporteServicio)
    if orden_venta_id:
        query = query.filter(models.ReporteServicio.orden_venta_id == orden_venta_id)
    rows = (
        query
        .order_by(desc(models.ReporteServicio.creado_en))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "page": page,
        "page_size": page_size,
        "items": [_serializar(r) for r in rows],
    }


@router.post("/", dependencies=[Depends(allow_all_staff)])
def crear(
    payload: schemas.ReporteServicioCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(models.OrdenVenta.id == payload.orden_venta_id)
        .first()
    )
    if not orden:
        raise HTTPException(404, "Orden de venta no encontrada")

    tiene_servicios = any(
        (d.tipo_linea == "servicio_catalogo" or d.servicio_id is not None)
        for d in orden.detalles
    )
    if not tiene_servicios:
        raise HTTPException(400, "La cotización no tiene líneas de servicio")

    try:
        nuevo = models.ReporteServicio(
            folio=_generar_folio_rs(db),
            orden_venta_id=orden.id,
            tecnico_nombre=payload.tecnico_nombre,
            cliente_recibe_nombre=payload.cliente_recibe_nombre,
            observaciones=payload.observaciones,
            creado_por_id=current_user.id,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return _serializar(nuevo)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("reportes_servicio_docs.crear falló")
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")


@router.get("/{id}", dependencies=[Depends(allow_all_staff)])
def detalle(id: int, db: Session = Depends(get_db)):
    r = (
        db.query(models.ReporteServicio)
        .filter(models.ReporteServicio.id == id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Reporte no encontrado")
    return _serializar(r)


def _render_reporte_servicio_pdf(r: models.ReporteServicio, db: Session) -> bytes:
    """Render acta de servicio ejecutado. Look sobrio profesional."""
    orden = r.orden_venta
    cliente = orden.cliente if orden else None

    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Encabezado de la empresa
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, _txt("DASIC INDUSTRIAL"), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 4, _txt("Reporte de Servicio"), ln=1)
    pdf.ln(2)

    # Caja con folio + fecha
    pdf.set_draw_color(180, 180, 180)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 7, _txt(f"Folio: {r.folio or '-'}"), border=1, fill=True)
    fecha_txt = r.fecha_reporte.strftime("%d/%m/%Y") if r.fecha_reporte else "-"
    pdf.cell(95, 7, _txt(f"Fecha: {fecha_txt}"), border=1, fill=True, ln=1)
    if orden:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, _txt(f"Cotización origen: {orden.folio or orden.id}"), ln=1)
    pdf.ln(3)

    # Datos del cliente
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _txt("Cliente"), ln=1)
    pdf.set_font("Helvetica", "", 9)
    if cliente:
        pdf.cell(0, 5, _txt(cliente.nombre_empresa or "-"), ln=1)
        if cliente.rfc_tax_id:
            pdf.cell(0, 5, _txt(f"RFC: {cliente.rfc_tax_id}"), ln=1)
        contacto_bits = []
        if cliente.email:
            contacto_bits.append(cliente.email)
        if cliente.telefono:
            contacto_bits.append(cliente.telefono)
        if contacto_bits:
            pdf.cell(0, 5, _txt(" · ".join(contacto_bits)), ln=1)
    else:
        pdf.cell(0, 5, _txt("(sin cliente)"), ln=1)
    pdf.ln(3)

    # Técnico
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _txt("Técnico responsable"), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _txt(r.tecnico_nombre or "(no especificado)"), ln=1)
    pdf.ln(3)

    # Servicios ejecutados
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _txt("Servicios ejecutados"), ln=1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 6, _txt("Cant."), border=1, fill=True, align="C")
    pdf.cell(35, 6, _txt("Código"), border=1, fill=True, align="L")
    pdf.cell(135, 6, _txt("Descripción"), border=1, fill=True, ln=1)
    pdf.set_font("Helvetica", "", 9)

    if orden:
        lineas = [
            d for d in orden.detalles
            if d.tipo_linea == "servicio_catalogo" or d.servicio_id is not None
        ]
    else:
        lineas = []

    if not lineas:
        pdf.cell(0, 6, _txt("(sin líneas de servicio en la cotización)"), ln=1)
    else:
        for d in lineas:
            codigo = "-"
            descripcion = "-"
            if d.servicio is not None:
                codigo = getattr(d.servicio, "codigo", None) or "-"
                descripcion = getattr(d.servicio, "nombre", None) or d.descripcion_libre or "-"
            else:
                codigo = d.sku_libre or "-"
                descripcion = d.descripcion_libre or "-"

            x_start = pdf.get_x()
            y_start = pdf.get_y()
            pdf.cell(15, 6, _txt(str(d.cantidad or 0)), border=1, align="C")
            pdf.cell(35, 6, _txt(codigo)[:25], border=1, align="L")
            pdf.multi_cell(135, 6, _txt(descripcion), border=1, align="L")
            # Restablece posición para próxima fila
            if pdf.get_y() < y_start + 6:
                pdf.set_xy(x_start, y_start + 6)
    pdf.ln(3)

    # Observaciones
    if r.observaciones:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, _txt("Observaciones"), ln=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _txt(r.observaciones))
        pdf.ln(3)

    # Recepción / firmas
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 9)
    col_w = 90
    y_firmas = pdf.get_y()
    pdf.cell(col_w, 5, _txt("_" * 40), align="C")
    pdf.cell(col_w, 5, _txt("_" * 40), align="C", ln=1)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_w, 4, _txt("Técnico"), align="C")
    pdf.cell(col_w, 4, _txt("Cliente recibe"), align="C", ln=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(col_w, 4, _txt(r.tecnico_nombre or "(nombre)"), align="C")
    pdf.cell(col_w, 4, _txt(r.cliente_recibe_nombre or "(nombre)"), align="C", ln=1)

    if r.recibido_at:
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, _txt(f"Recepción confirmada: {r.recibido_at.strftime('%d/%m/%Y %H:%M')}"), align="R", ln=1)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


@router.get("/{id}/pdf", dependencies=[Depends(allow_all_staff)])
def descargar_pdf(id: int, db: Session = Depends(get_db)):
    r = (
        db.query(models.ReporteServicio)
        .filter(models.ReporteServicio.id == id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Reporte no encontrado")
    pdf_bytes = _render_reporte_servicio_pdf(r, db)
    filename = f"{r.folio or f'RS-{r.id}'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{id}/recepcion", dependencies=[Depends(allow_all_staff)])
def registrar_recepcion(
    id: int,
    cliente_recibe_nombre: str,
    db: Session = Depends(get_db),
):
    r = (
        db.query(models.ReporteServicio)
        .filter(models.ReporteServicio.id == id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Reporte no encontrado")
    if r.recibido_at:
        raise HTTPException(409, "El reporte ya tiene recepción registrada")

    try:
        r.cliente_recibe_nombre = cliente_recibe_nombre
        r.recibido_at = datetime.utcnow()
        db.commit()
        db.refresh(r)
        return _serializar(r)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("reportes_servicio_docs.registrar_recepcion falló")
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")
