from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta
from jinja2 import Environment, BaseLoader

from app import models
from app import schemas
from app.dependencies import get_current_active_organization
from app.db import get_db
from app.security import allow_all_staff, get_current_user

router = APIRouter(prefix="/api/ventas", tags=["Ventas y Cotizaciones"])

DEFAULT_QUOTE_VALIDITY_DAYS = 15


def _user_initials(usuario: "models.Usuario") -> str:
    nombre = (usuario.nombre or usuario.email or "USR").strip()
    parts = [p for p in nombre.split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "USR"


def _generar_folio(
    db: Session,
    organization_id: str,
    tipo_orden: "models.EstatusOrden",
    vendedor: "models.Usuario",
) -> str:
    """COT-YYYYMM-USR-NNNN (NNNN = consecutivo del usuario en el mes)."""
    ahora = datetime.utcnow()
    yyyymm = ahora.strftime("%Y%m")
    iniciales = _user_initials(vendedor)
    prefijo = "COT" if tipo_orden == models.EstatusOrden.COTIZACION else "VTA"
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    consecutivo = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.vendedor_id == vendedor.id,
            models.OrdenVenta.fecha_creacion >= inicio_mes,
        )
        .count()
        + 1
    )
    return f"{prefijo}-{yyyymm}-{iniciales}-{consecutivo:04d}"


def _normalize_currency(moneda: str | None) -> str:
    moneda_normalizada = (moneda or "MXN").upper()
    if moneda_normalizada not in {"MXN", "USD"}:
        raise HTTPException(400, "Moneda inválida. Usa MXN o USD.")
    return moneda_normalizada


def _resolve_exchange_rate(moneda: str, tipo_cambio: Decimal | None) -> Decimal:
    if moneda == "MXN":
        return Decimal("1.0")
    if tipo_cambio is None or tipo_cambio <= 0:
        raise HTTPException(400, "Tipo de cambio inválido para cotizaciones en USD")
    return Decimal(tipo_cambio)


def _convert_cost_to_quote_currency(
    costo_compra: Decimal,
    moneda_compra: str,
    moneda_cotizacion: str,
    tipo_cambio: Decimal,
) -> Decimal:
    moneda_origen = _normalize_currency(moneda_compra)
    if moneda_origen == moneda_cotizacion:
        return Decimal(costo_compra)
    if moneda_origen == "USD" and moneda_cotizacion == "MXN":
        return Decimal(costo_compra) * tipo_cambio
    if moneda_origen == "MXN" and moneda_cotizacion == "USD":
        return Decimal(costo_compra) / tipo_cambio
    raise HTTPException(400, "No se pudo convertir la moneda del producto")


def _currency_symbol(moneda: str) -> str:
    return "US$" if moneda == "USD" else "$"

# --- PLANTILLA PDF PROFESIONAL (DISEÑO FINAL) ---
PDF_TEMPLATE_VENTA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ tipo_doc }} {{ orden.folio }}</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; padding: 40px; font-size: 14px; }
        .container { max-width: 800px; margin: 0 auto; }
        
        /* HEADER */
        .header { display: flex; justify-content: space-between; border-bottom: 3px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 30px; }
        .logo-area { width: 60%; }
        .company-name { font-size: 32px; font-weight: 900; color: #1e3a8a; margin: 0; letter-spacing: -1px; }
        .company-details { font-size: 12px; color: #555; line-height: 1.4; margin-top: 5px; }
        
        .doc-info { width: 35%; text-align: right; }
        .doc-title { font-size: 24px; font-weight: bold; color: #333; text-transform: uppercase; margin-bottom: 5px; }
        .doc-meta { font-size: 13px; color: #666; line-height: 1.6; }
        
        /* CLIENTE */
        .client-section { background: #f1f5f9; padding: 15px; border-radius: 8px; margin-bottom: 30px; border-left: 5px solid #3b82f6; display: flex; }
        .client-col { width: 50%; }
        .label { font-size: 10px; font-weight: bold; text-transform: uppercase; color: #64748b; margin-bottom: 2px; }
        .value { font-weight: bold; color: #1e293b; margin-bottom: 8px; font-size: 14px; }
        .sub-value { font-size: 13px; color: #475569; }

        /* TABLA */
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th { background: #1e3a8a; color: white; padding: 10px; text-align: left; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }
        td { padding: 12px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
        tr:nth-child(even) { background: #f8fafc; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .meta-text { color: #0f766e; font-size: 10px; display: block; }

        /* TOTALES */
        .totals-container { display: flex; justify-content: flex-end; margin-bottom: 30px; }
        .totals-box { width: 40%; }
        .total-row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 14px; color: #475569; }
        .grand-total { font-size: 20px; font-weight: bold; color: #1e3a8a; border-top: 2px solid #1e3a8a; padding-top: 10px; margin-top: 5px; }

        /* CONDICIONES */
        .terms-box { border-top: 1px solid #cbd5e1; padding-top: 20px; margin-top: 40px; font-size: 11px; color: #475569; }
        .terms-title { font-weight: bold; text-transform: uppercase; margin-bottom: 10px; color: #1e3a8a; }
        .bank-info { background: #eff6ff; padding: 10px; border-radius: 6px; margin-top: 10px; display: inline-block; width: 100%; box-sizing: border-box; }
        
        .footer { margin-top: 40px; text-align: center; font-size: 10px; color: #94a3b8; }
    </style>
</head>
<body onload="window.print()">
    <div class="container">
        <div class="header">
            <div class="logo-area">
                <div class="company-name">DASIC ERP</div>
                <div class="company-details">
                    Soluciones Industriales S.A. de C.V.<br>
                    RFC: DAS-010101-ABC<br>
                    Av. Revolución 123, Ciudad de México<br>
                    contacto@dasic.com | (55) 5555-5555
                </div>
            </div>
            <div class="doc-info">
                <div class="doc-title">{{ tipo_doc }}</div>
                <div class="doc-meta">
                    Folio: <strong style="color: #000;">{{ orden.folio }}</strong><br>
                    Fecha: {{ orden.fecha_creacion.strftime('%d/%m/%Y') }}<br>
                    Vendedor: {{ orden.vendedor.nombre }}
                </div>
            </div>
        </div>

        <div class="client-section">
            <div class="client-col">
                <div class="label">Cliente</div>
                <div class="value">{{ orden.cliente.nombre_empresa }}</div>
                <div class="sub-value">{{ orden.cliente.rfc_tax_id or "XAXX010101000" }}</div>
                <div class="sub-value">{{ orden.cliente.direccion or "Domicilio Conocido" }}</div>
            </div>
            <div class="client-col">
                <div class="label">Contacto</div>
                <div class="value">{{ orden.cliente.contacto_nombre }}</div>
                <div class="sub-value">{{ orden.cliente.email }}</div>
                <div class="sub-value">Tel: {{ orden.cliente.telefono }}</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th width="15%">SKU</th>
                    <th width="45%">Descripción</th>
                    <th width="10%" class="text-center">Cant.</th>
                    <th width="15%" class="text-right">P. Unitario</th>
                    <th width="15%" class="text-right">Total</th>
                </tr>
            </thead>
            <tbody>
                {% for item in orden.detalles %}
                <tr>
                    <td style="font-weight: bold; color: #475569;">{{ (item.producto.sku_comercial if item.producto else item.sku_libre) or "—" }}</td>
                    <td>
                        {{ item.producto.nombre if item.producto else (item.descripcion_libre or "Producto especial") }}
                        {% if item.utilidad_aplicada and item.utilidad_aplicada > 0 %}
                            <span class="meta-text">Utilidad {{ item.utilidad_aplicada|int }}%</span>
                        {% endif %}
                    </td>
                    <td class="text-center">{{ item.cantidad }}</td>
                    <td class="text-right">{{ simbolo_moneda }}{{ "{:,.2f}".format(item.precio_unitario) }}</td>
                    <td class="text-right font-bold text-slate-700">{{ simbolo_moneda }}{{ "{:,.2f}".format(item.subtotal) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-container">
            <div class="totals-box">
                <div class="total-row">
                    <span>Subtotal:</span>
                    <span>{{ simbolo_moneda }}{{ "{:,.2f}".format(orden.total) }}</span>
                </div>
                <div class="total-row">
                    <span>IVA (16%):</span>
                    <span>{{ simbolo_moneda }}{{ "{:,.2f}".format(iva) }}</span>
                </div>
                <div class="total-row grand-total">
                    <span>TOTAL:</span>
                    <span>{{ simbolo_moneda }}{{ "{:,.2f}".format(gran_total) }}</span>
                </div>
            </div>
        </div>

        <div class="terms-box">
            <div class="terms-title">Términos y Condiciones Comerciales</div>
            <ul>
                <li>Precios expresados en <strong>{{ etiqueta_moneda }} ({{ orden.moneda }})</strong>. Sujetos a cambio sin previo aviso.</li>
                {% if orden.moneda == "USD" %}
                <li>Tipo de cambio referencia: <strong>{{ "{:,.4f}".format(orden.tipo_cambio) }} MXN por USD</strong>. Pago en USD o en MXN al T.C. del día de pago.</li>
                {% endif %}
                <li>Vigencia de la cotización: <strong>{{ vigencia_dias }} días naturales</strong>.</li>
                <li>Tiempo de entrega sujeto a disponibilidad de stock.</li>
                <li>{{ orden.observaciones or "Sin observaciones adicionales." }}</li>
            </ul>

            <div class="bank-info">
                {% if orden.moneda == "USD" %}
                <strong>DATOS BANCARIOS (USD):</strong> Solicite datos de cuenta en dólares al ejecutivo de cuenta.
                {% else %}
                <strong>DATOS BANCARIOS (MXN):</strong> BBVA Bancomer | DASIC S.A. DE C.V. | Cuenta: 0123 4567 89
                {% endif %}
            </div>
        </div>

        <div class="footer">
            www.dasic.com | Soluciones integrales para la industria
        </div>
    </div>
</body>
</html>
"""

# --- 1. CREAR ORDEN (POST) ---
@router.post("/", response_model=schemas.OrdenVentaResponse, dependencies=[Depends(allow_all_staff)])
def crear_orden(
    orden_data: schemas.OrdenVentaCreate,
    tipo_orden: models.EstatusOrden = models.EstatusOrden.COTIZACION,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    cliente = (
        db.query(models.Cliente)
        .filter(
            models.Cliente.organization_id == organization_id,
            models.Cliente.id == orden_data.cliente_id,
        )
        .first()
    )
    if not cliente: raise HTTPException(404, "Cliente no encontrado")

    moneda_cotizacion = _normalize_currency(orden_data.moneda)
    tipo_cambio = _resolve_exchange_rate(moneda_cotizacion, orden_data.tipo_cambio)

    try:
        folio = _generar_folio(db, organization_id, tipo_orden, current_user)

        nueva_orden = models.OrdenVenta(
            organization_id=organization_id,
            folio=folio,
            cliente_id=cliente.id,
            vendedor_id=current_user.id,
            estatus=tipo_orden,
            observaciones=orden_data.observaciones,
            moneda=moneda_cotizacion,
            tipo_cambio=tipo_cambio,
            fecha_vencimiento=datetime.utcnow() + timedelta(days=DEFAULT_QUOTE_VALIDITY_DAYS),
            total=0,
        )
        db.add(nueva_orden)
        db.flush()

        total_orden = Decimal(0)

        for item in orden_data.detalles:
            producto = None
            costo_origen = Decimal(item.costo_unitario or 0)
            moneda_origen_linea = (item.moneda_origen or "MXN").upper()
            sku_libre = (item.sku_libre or "").strip() or None
            descripcion_libre = (item.descripcion_libre or "").strip() or None

            if item.producto_id:
                producto = (
                    db.query(models.Producto)
                    .filter(models.Producto.id == item.producto_id)
                    .first()
                )
                if not producto:
                    raise HTTPException(404, f"Producto {item.producto_id} no existe")

                if tipo_orden != models.EstatusOrden.COTIZACION:
                    if producto.stock_actual < item.cantidad:
                        raise HTTPException(400, f"Stock insuficiente para {producto.sku}")
                    producto.stock_actual -= item.cantidad

                moneda_origen_linea = (
                    item.moneda_origen or producto.moneda_compra or "MXN"
                ).upper()
                costo_origen = Decimal(producto.costo_compra or 0)
            else:
                if not descripcion_libre:
                    raise HTTPException(
                        400,
                        "Producto fantasma requiere descripción y costo unitario.",
                    )
                if costo_origen <= 0:
                    raise HTTPException(
                        400,
                        "Producto fantasma requiere costo unitario > 0.",
                    )

            costo_base = _convert_cost_to_quote_currency(
                costo_origen,
                moneda_origen_linea,
                moneda_cotizacion,
                tipo_cambio,
            )
            utilidad_pct = Decimal(item.utilidad or 0)
            precio_final = costo_base * (Decimal("1.0") + (utilidad_pct / Decimal("100")))

            subtotal = precio_final * item.cantidad
            total_orden += subtotal

            db.add(models.DetalleOrden(
                organization_id=organization_id,
                orden_id=nueva_orden.id,
                producto_id=producto.id if producto else None,
                sku_libre=sku_libre,
                descripcion_libre=descripcion_libre,
                moneda_origen_linea=moneda_origen_linea,
                costo_base_linea=costo_origen.quantize(Decimal("0.01")),
                cantidad=item.cantidad,
                precio_unitario=precio_final.quantize(Decimal("0.01")),
                utilidad_aplicada=utilidad_pct,
                descuento_aplicado=Decimal(item.descuento or 0),
                subtotal=subtotal
            ))

        nueva_orden.total = total_orden.quantize(Decimal("0.01"))
        
        # Deuda (Solo si es venta directa)
        if tipo_orden == models.EstatusOrden.PENDIENTE:
            total_con_iva = total_orden * Decimal("1.16")
            deuda = models.TransaccionCliente(
                organization_id=organization_id,
                cliente_id=cliente.id,
                tipo=models.TipoMovimiento.CARGO,
                monto=total_con_iva,
                descripcion=f"Venta {folio}",
                referencia_id=nueva_orden.id
            )
            db.add(deuda)
            cliente.saldo_actual += total_con_iva

        db.commit()
        db.refresh(nueva_orden)
        return nueva_orden

    except Exception as e:
        db.rollback()
        raise e

# --- 2. EDITAR COTIZACIÓN (PUT) ---
@router.put("/{id}", response_model=schemas.OrdenVentaResponse, dependencies=[Depends(allow_all_staff)])
def actualizar_orden(
    id: int,
    orden_update: schemas.OrdenVentaCreate,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db)
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden: raise HTTPException(404, "Orden no encontrada")
    
    if orden.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Solo se pueden editar cotizaciones, no ventas cerradas.")

    moneda_cotizacion = _normalize_currency(orden_update.moneda)
    tipo_cambio = _resolve_exchange_rate(moneda_cotizacion, orden_update.tipo_cambio)

    try:
        # Actualizar cabecera
        orden.cliente_id = orden_update.cliente_id
        orden.observaciones = orden_update.observaciones
        orden.moneda = moneda_cotizacion
        orden.tipo_cambio = tipo_cambio
        orden.fecha_vencimiento = datetime.utcnow() + timedelta(days=DEFAULT_QUOTE_VALIDITY_DAYS)
        
        # Borrar detalles viejos
        db.query(models.DetalleOrden).filter(
            models.DetalleOrden.organization_id == organization_id,
            models.DetalleOrden.orden_id == id,
        ).delete()
        
        total_orden = Decimal(0)

        # Insertar nuevos
        for item in orden_update.detalles:
            producto = None
            costo_origen = Decimal(item.costo_unitario or 0)
            moneda_origen_linea = (item.moneda_origen or "MXN").upper()
            sku_libre = (item.sku_libre or "").strip() or None
            descripcion_libre = (item.descripcion_libre or "").strip() or None

            if item.producto_id:
                producto = (
                    db.query(models.Producto)
                    .filter(models.Producto.id == item.producto_id)
                    .first()
                )
                if not producto:
                    raise HTTPException(404, f"Producto {item.producto_id} no encontrado")
                moneda_origen_linea = (
                    item.moneda_origen or producto.moneda_compra or "MXN"
                ).upper()
                costo_origen = Decimal(producto.costo_compra or 0)
            else:
                if not descripcion_libre:
                    raise HTTPException(400, "Producto fantasma requiere descripción.")
                if costo_origen <= 0:
                    raise HTTPException(400, "Producto fantasma requiere costo unitario > 0.")

            costo_base = _convert_cost_to_quote_currency(
                costo_origen,
                moneda_origen_linea,
                moneda_cotizacion,
                tipo_cambio,
            )
            utilidad_pct = Decimal(item.utilidad or 0)
            precio_final = costo_base * (Decimal("1.0") + (utilidad_pct / Decimal("100")))

            subtotal = precio_final * item.cantidad
            total_orden += subtotal

            db.add(models.DetalleOrden(
                organization_id=organization_id,
                orden_id=orden.id,
                producto_id=producto.id if producto else None,
                sku_libre=sku_libre,
                descripcion_libre=descripcion_libre,
                moneda_origen_linea=moneda_origen_linea,
                costo_base_linea=costo_origen.quantize(Decimal("0.01")),
                cantidad=item.cantidad,
                precio_unitario=precio_final.quantize(Decimal("0.01")),
                utilidad_aplicada=utilidad_pct,
                descuento_aplicado=Decimal(item.descuento or 0),
                subtotal=subtotal
            ))

        orden.total = total_orden.quantize(Decimal("0.01"))
        db.commit()
        db.refresh(orden)
        return orden

    except Exception as e:
        db.rollback()
        raise e

# --- 2.5 RECOTIZAR (CREAR NUEVA VERSIÓN) ---
@router.post("/{id}/recotizar", response_model=schemas.OrdenVentaResponse, dependencies=[Depends(allow_all_staff)])
def recotizar(
    id: int,
    organization_id: str = Depends(get_current_active_organization),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea una nueva versión de la cotización clonando partidas. La original
    queda archivada (no se modifica) y se devuelve la nueva versión."""
    origen = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not origen:
        raise HTTPException(404, "Cotización origen no encontrada")
    if origen.estatus not in (models.EstatusOrden.COTIZACION, models.EstatusOrden.CANCELADA):
        raise HTTPException(400, "Sólo cotizaciones se pueden recotizar")

    raiz_id = origen.cotizacion_origen_id or origen.id
    siguiente_version = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            ((models.OrdenVenta.cotizacion_origen_id == raiz_id) | (models.OrdenVenta.id == raiz_id)),
        )
        .count()
        + 1
    )

    folio_nuevo = _generar_folio(db, organization_id, models.EstatusOrden.COTIZACION, current_user)
    folio_versionado = f"{folio_nuevo}-V{siguiente_version}"

    nueva = models.OrdenVenta(
        organization_id=organization_id,
        folio=folio_versionado,
        cliente_id=origen.cliente_id,
        vendedor_id=current_user.id,
        estatus=models.EstatusOrden.COTIZACION,
        observaciones=origen.observaciones,
        moneda=origen.moneda,
        tipo_cambio=origen.tipo_cambio,
        total=origen.total,
        fecha_vencimiento=datetime.utcnow() + timedelta(days=DEFAULT_QUOTE_VALIDITY_DAYS),
        cotizacion_origen_id=raiz_id,
        version=siguiente_version,
    )
    db.add(nueva)
    db.flush()

    for det in origen.detalles:
        db.add(models.DetalleOrden(
            organization_id=organization_id,
            orden_id=nueva.id,
            producto_id=det.producto_id,
            sku_libre=det.sku_libre,
            descripcion_libre=det.descripcion_libre,
            moneda_origen_linea=det.moneda_origen_linea,
            costo_base_linea=det.costo_base_linea,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            utilidad_aplicada=det.utilidad_aplicada,
            descuento_aplicado=det.descuento_aplicado,
            subtotal=det.subtotal,
        ))

    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/{id}/versiones", dependencies=[Depends(allow_all_staff)])
def listar_versiones(
    id: int,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
):
    base = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not base:
        raise HTTPException(404, "Cotización no encontrada")
    raiz_id = base.cotizacion_origen_id or base.id

    versiones = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            ((models.OrdenVenta.cotizacion_origen_id == raiz_id) | (models.OrdenVenta.id == raiz_id)),
        )
        .order_by(models.OrdenVenta.version.asc())
        .all()
    )
    return [
        {
            "id": v.id,
            "folio": v.folio,
            "version": v.version,
            "estatus": v.estatus,
            "total": v.total,
            "moneda": v.moneda,
            "fecha": v.fecha_creacion,
        }
        for v in versiones
    ]


# --- 3. CONVERTIR COTIZACIÓN A VENTA (POST) ---
@router.post("/{id}/convertir", dependencies=[Depends(allow_all_staff)])
def convertir_cotizacion(
    id: int,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden or orden.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Orden no válida para conversión")

    try:
        # Descontar Stock
        for det in orden.detalles:
            if det.producto.stock_actual < det.cantidad:
                raise HTTPException(400, f"Stock insuficiente para {det.producto.sku}")
            det.producto.stock_actual -= det.cantidad
        
        # Cambiar Estatus y Folio
        orden.estatus = models.EstatusOrden.PENDIENTE
        orden.folio = orden.folio.replace("COT", "VTA")
        
        # Generar Deuda
        total_con_iva = orden.total * Decimal("1.16")
        db.add(models.TransaccionCliente(
            organization_id=organization_id,
            cliente_id=orden.cliente_id,
            tipo=models.TipoMovimiento.CARGO,
            monto=total_con_iva,
            descripcion=f"Venta {orden.folio} (Desde Cotización)",
            referencia_id=orden.id
        ))
        orden.cliente.saldo_actual += total_con_iva
        
        db.commit()
        return {"mensaje": "Convertido exitosamente", "nuevo_folio": orden.folio}
    except Exception as e:
        db.rollback()
        raise e

# --- 4. LISTAR HISTORIAL ---
@router.get("/historial", dependencies=[Depends(allow_all_staff)])
def listar_historial(
    limit: int = 50,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
):
    ordenes = db.query(models.OrdenVenta)\
        .filter(models.OrdenVenta.organization_id == organization_id)\
        .order_by(desc(models.OrdenVenta.fecha_creacion))\
        .limit(limit).all()

    ahora = datetime.utcnow().date()

    return [{
        "id": o.id,
        "folio": o.folio,
        "fecha": o.fecha_creacion,
        "fecha_vencimiento": o.fecha_vencimiento,
        "cliente": o.cliente.nombre_empresa,
        "total": o.total,
        "moneda": o.moneda,
        "tipo_cambio": o.tipo_cambio,
        "estatus": o.estatus,
        "version": o.version or 1,
        "cotizacion_origen_id": o.cotizacion_origen_id,
        "edad_dias": max((ahora - o.fecha_creacion.date()).days, 0) if o.fecha_creacion else 0,
        "dias_restantes": (o.fecha_vencimiento.date() - ahora).days if o.fecha_vencimiento else None,
        "esta_vencida": bool(o.fecha_vencimiento and o.fecha_vencimiento.date() < ahora),
    } for o in ordenes]

# --- 5. DETALLE JSON (PARA EDICIÓN) ---
@router.get("/{id}/detalle-json", dependencies=[Depends(allow_all_staff)])
def obtener_detalle_orden(
    id: int,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden: raise HTTPException(404)
    
    detalles = []
    for d in orden.detalles:
        detalles.append({
            "producto": {
                "id": d.producto.id,
                "sku": d.producto.sku_comercial or "—",
                "sku_interno": d.producto.sku,
                "nombre": d.producto.nombre,
            },
            "cantidad": d.cantidad,
            "precio_unitario": d.precio_unitario,
            "utilidad_aplicada": d.utilidad_aplicada,
            "descuento_aplicado": d.descuento_aplicado,
            "subtotal": d.subtotal
        })
        
    return {
        "id": orden.id,
        "folio": orden.folio,
        "cliente_id": orden.cliente_id,
        "observaciones": orden.observaciones,
        "moneda": orden.moneda,
        "tipo_cambio": orden.tipo_cambio,
        "detalles": detalles
    }

# --- 6. GENERAR PDF ---
@router.get("/{id}/pdf", response_class=HTMLResponse, dependencies=[Depends(allow_all_staff)])
def generar_pdf(
    id: int,
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden: raise HTTPException(404)

    iva = orden.total * Decimal("0.16")
    gran_total = orden.total + iva
    tipo_doc = (
        "COTIZACIÓN" if orden.estatus == models.EstatusOrden.COTIZACION else "NOTA DE VENTA"
    )
    simbolo_moneda = _currency_symbol(orden.moneda)
    etiqueta_moneda = "Dólares Americanos" if orden.moneda == "USD" else "Moneda Nacional"
    vigencia_dias = (
        max((orden.fecha_vencimiento.date() - orden.fecha_creacion.date()).days, 0)
        if orden.fecha_vencimiento and orden.fecha_creacion
        else DEFAULT_QUOTE_VALIDITY_DAYS
    )

    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_VENTA).render(
        orden=orden,
        iva=iva,
        gran_total=gran_total,
        tipo_doc=tipo_doc,
        simbolo_moneda=simbolo_moneda,
        etiqueta_moneda=etiqueta_moneda,
        vigencia_dias=vigencia_dias,
    )
