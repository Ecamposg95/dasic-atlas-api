from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from jinja2 import Environment, BaseLoader
from pydantic import BaseModel, EmailStr, Field

from app import models
from app import schemas
from app.core.config import get_settings
from app.db import get_db
from app.security import allow_all_staff, get_current_user
from app.services.email_service import (
    EmailDeliveryError,
    send_quote_email,
    smtp_configured,
)
from app.services.ai_service import sugerir_proximo_paso
from app.models.enums import TipoMovimientoStock
from app.services.stock_service import (
    aplicar_movimiento,
    consumir_reservas_a_salida,
    liberar_reservas_cotizacion,
    reservar_para_cotizacion,
    reservas_activas,
)


def _check_owner_or_403(orden: "models.OrdenVenta", current_user: "models.Usuario", action: str = "read") -> None:
    """Bloquea acciones de VENTAS sobre cotizaciones que no son suyas. Admin/Gerente pasan."""
    from app.security.permissions import is_owner_scoped
    if is_owner_scoped(current_user, action, "cotizacion"):
        if orden.vendedor_id != current_user.id:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")


def _resolve_tipo_linea(item, producto: "models.Producto | None") -> str:
    """Determina tipo_linea efectivo. Producto del catálogo marcado es_servicio
    fuerza 'servicio'. Si no hay producto y hay descripcion_libre, default fantasma."""
    raw = (getattr(item, "tipo_linea", None) or "").lower().strip() or "producto_catalogo"
    if producto and producto.es_servicio:
        return "servicio"
    if raw == "servicio":
        return "servicio"
    if not producto and getattr(item, "descripcion_libre", None):
        return "producto_fantasma" if raw not in ("servicio",) else "servicio"
    return "producto_catalogo"

router = APIRouter(prefix="/api/ventas", tags=["Ventas y Cotizaciones"])


# Defaults editables de "Condiciones Comerciales". Si una cotización se crea
# sin terminos_condiciones, se persiste este texto y el usuario lo puede
# editar/eliminar/agregar líneas desde el cotizador. Sincronizado con el
# DEFAULTS_TERMINOS de cotizador.html (mantener en paralelo).
_DEFAULT_TERMINOS = (
    "Agregar el IVA correspondiente. Tiempo de entrega S.P.V.\n"
    "Verificar que el material cotizado cumpla con sus requerimientos técnicos.\n"
    "Todos los precios que incluyen instalación, servicios y capacitación están basados en nuestros horarios normales de trabajo (L-V 8:00-18:00 hrs) a menos de que sea estipulado de otra forma dentro de la cotización. Los cargos adicionales por horas trabajadas fuera de estos horarios u horas superiores a ocho (8) por día serán facturadas por separado.\n"
    "En caso de cancelación se cobrará el 25% del monto total.\n"
    "Los precios indicados no incluyen flete.\n"
    "Si se tiene el material en existencia y el cliente se encuentra ubicado en CDMX y/o área metropolitana se entregará en 2 a 3 días hábiles. En caso contrario el flete será cubierto por el cliente.\n"
    "Para procesar su pedido es necesario colocar una orden de compra indicando el número de cotización y aceptación de estas condiciones comerciales (más anticipo cuando aplique).\n"
    "La garantía de los productos es la que otorga cada fabricante."
)


def _iva_rate() -> Decimal:
    return Decimal(str(get_settings().iva_rate))


def _iva_pct_label() -> str:
    rate = get_settings().iva_rate * 100
    return f"{rate:g}%"


def _quote_validity_days() -> int:
    return get_settings().quote_validity_days


@router.get("/config/cotizador-defaults", dependencies=[Depends(allow_all_staff)])
def cotizador_defaults():
    """Defaults dinámicos para el frontend del cotizador (IVA, vigencia)."""
    s = get_settings()
    return {
        "iva_rate": s.iva_rate,
        "iva_pct_label": f"{s.iva_rate * 100:g}%",
        "quote_validity_days": s.quote_validity_days,
    }


def _generar_folio(
    db: Session,
    tipo_orden: "models.EstatusOrden",
    vendedor: "models.Usuario",
) -> str:
    """Folio formato DASIC: C-YYMM<seq> (cotización) o V-YYMM<seq> (venta).

    El consecutivo es global por mes y por tipo (no por usuario), con padding
    mínimo de 3 dígitos. Refleja el formato real usado en los PDFs históricos
    (ej. C-2604227, OC-2604001).
    """
    ahora = datetime.utcnow()
    yymm = ahora.strftime("%y%m")
    es_cot = tipo_orden == models.EstatusOrden.COTIZACION
    prefijo = "C" if es_cot else "V"
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Advisory lock transaccional: serializa el cómputo del consecutivo por
    # (prefijo, mes) entre llamadas concurrentes. Sin esto, count()+1 sufre
    # race y dos cotizaciones del mismo minuto pueden colisionar en folio.
    lock_key = f"folio:{prefijo}:{yymm}"
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": lock_key})

    q = db.query(models.OrdenVenta).filter(
        models.OrdenVenta.fecha_creacion >= inicio_mes,
        models.OrdenVenta.folio.like(f"{prefijo}-%"),
    )
    consecutivo = q.count() + 1
    return f"{prefijo}-{yymm}{consecutivo:03d}"


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

# --- PLANTILLA PDF: layout DASIC real (cotización / nota de venta) ---
PDF_TEMPLATE_VENTA = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{{ tipo_doc }} {{ orden.folio }}</title>
<style>
  @page { size: Letter; margin: 0; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #1e293b; font-size: 12px; }

  .page { width: 100%; min-height: 100vh; padding: 28px 38px 96px 38px; position: relative; }

  /* Header DASIC */
  .brand-row { display: flex; align-items: center; gap: 18px; padding-bottom: 10px; border-bottom: 4px solid #0f3a66; }
  .brand-mark { width: 46px; height: 46px; border-radius: 8px; background: linear-gradient(135deg,#0f3a66,#1d6fb8); color:#fff; font-weight: 900; font-size: 24px; display:flex; align-items:center; justify-content:center; letter-spacing: -1px; }
  .brand-name { font-size: 30px; font-weight: 900; color:#0f3a66; letter-spacing: 1px; }
  .brand-tag { font-size: 11px; color:#475569; margin-top: 2px; letter-spacing: 0.5px; }
  .brand-rule { height: 6px; background: linear-gradient(90deg,#0f3a66,#1d6fb8 60%,#cbd5e1); margin-bottom: 22px; }

  /* Encabezado documento */
  .doc-head { display:flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
  .doc-fecha { font-size: 13px; color:#0f172a; }
  .doc-fecha .lbl { font-weight: 700; }
  .doc-fecha .val { text-decoration: underline; font-weight: 600; }
  .doc-title { color:#0f3a66; font-weight: 800; font-size: 26px; letter-spacing: 1px; }
  .doc-folio { color:#0f172a; font-weight: 700; font-size: 16px; margin-left: 6px; }

  /* Bloque cliente (alineado a la derecha como los PDFs reales) */
  .cliente { text-align: right; margin-bottom: 14px; }
  .cliente .row { font-size: 12.5px; color:#0f172a; line-height: 1.45; }
  .cliente .lbl { font-weight: 700; }
  .cliente .name, .cliente .email a { color: #1d6fb8; font-weight: 700; }

  /* Tabla */
  table.items { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 8px; font-size: 11px; }
  table.items thead th {
    background:#0f3a66; color:#fff; padding: 8px 6px; font-weight: 700;
    border-right: 1px solid #1d6fb8; text-transform: capitalize; font-size: 11px;
  }
  table.items thead th:last-child { border-right: none; }
  table.items tbody td { background:#f1f5f9; padding: 10px 8px; border-bottom: 4px solid #fff; vertical-align: top; }
  table.items td.center { text-align: center; }
  table.items td.right { text-align: right; }
  .item-cat { font-weight: 700; color:#0f172a; }
  .item-desc { color:#0f172a; white-space: pre-line; }
  table.items tfoot td { background:#cfe2f3; font-weight: 700; padding: 9px 8px; border-bottom: 4px solid #fff; }

  /* Condiciones */
  .terms-title { font-weight: 800; color:#0f172a; margin-top: 22px; margin-bottom: 6px; font-size: 12px; }
  ul.terms { padding-left: 18px; margin: 0; color:#1e293b; font-size: 11px; line-height: 1.55; }
  ul.terms li { margin-bottom: 3px; }
  ul.terms strong { color:#0f172a; }

  /* Firma */
  .firma { margin-top: 32px; text-align: center; font-size: 12px; color:#0f172a; }
  .firma .label { font-weight: 800; letter-spacing: 1px; }
  .firma .line { width: 240px; border-top: 1px solid #0f172a; margin: 36px auto 4px; }
  .firma .name { font-weight: 700; }
  .firma .mail a { color:#1d6fb8; }

  /* Footer */
  .footer-bar {
    position: absolute; left: 0; right: 0; bottom: 0;
    background: linear-gradient(180deg, #0f3a66 0%, #0a2949 100%);
    color:#cbd5e1; font-size: 12px; text-align: center; padding: 14px 0; letter-spacing: 1px;
  }
  .footer-bar .web { color:#fff; font-weight: 700; }

  .print-btn { position: fixed; top: 14px; right: 14px; background:#1d6fb8; color:#fff; border: 0; padding: 8px 14px; border-radius: 6px; font-weight: 700; cursor: pointer; box-shadow: 0 6px 16px rgba(0,0,0,0.18); }
  @media print { .print-btn { display:none; } body { background:#fff; } }
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">Imprimir / Guardar PDF</button>
<div class="page">

  <div class="brand-row">
    <div class="brand-mark">D</div>
    <div>
      <div class="brand-name">DASIC</div>
      <div class="brand-tag">Development Of Automation System And Industrial Control</div>
    </div>
  </div>
  <div class="brand-rule"></div>

  <div class="doc-head">
    <div class="doc-fecha">
      <span class="lbl">Fecha:</span>
      <span class="val">{{ fecha_str }}</span>
    </div>
    <div>
      <span class="doc-title">{{ tipo_doc }}:</span>
      <span class="doc-folio">{{ orden.folio }}</span>
    </div>
  </div>

  <div class="cliente">
    {% if orden.cliente.contacto_nombre %}
      <div class="row"><span class="lbl">Nombre:</span> <span class="name">{{ orden.cliente.contacto_nombre }}</span></div>
    {% endif %}
    <div class="row"><span class="lbl">Compañía:</span> {{ orden.cliente.nombre_empresa }}</div>
    {% if orden.cliente.email %}
      <div class="row email"><span class="lbl">E-mail:</span> <a href="mailto:{{ orden.cliente.email }}">{{ orden.cliente.email }}</a></div>
    {% endif %}
  </div>

  {% set ns = namespace(has_desc=false, has_entrega=false) %}
  {% for d in orden.detalles %}
    {% if (d.descuento_aplicado or 0) > 0 %}{% set ns.has_desc = true %}{% endif %}
    {% if d.entrega_min is not none and d.entrega_max is not none and d.entrega_unidad %}{% set ns.has_entrega = true %}{% endif %}
  {% endfor %}
  {% set cols_extra = (1 if ns.has_desc else 0) + (1 if ns.has_entrega else 0) %}
  {% set cols_label = 5 + cols_extra %}
  <table class="items">
    <thead>
      <tr>
        <th style="width: 6%;">Item</th>
        <th style="width: 16%;">Catalog #</th>
        <th>Description</th>
        <th style="width: 7%;">Qty</th>
        {% if ns.has_entrega %}<th style="width: 12%;">Entrega</th>{% endif %}
        <th style="width: 14%;">UNIT</th>
        {% if ns.has_desc %}<th style="width: 8%;">Dto%</th>{% endif %}
        <th style="width: 14%;">SubTotal</th>
      </tr>
    </thead>
    <tbody>
      {% for item in orden.detalles %}
      <tr>
        <td class="center">{{ loop.index }}</td>
        <td><div class="item-cat">{{ (item.producto.sku_comercial if item.producto else item.sku_libre) or (item.producto.sku if item.producto else "—") }}</div></td>
        <td><div class="item-desc">{{ (item.producto.nombre if item.producto else (item.descripcion_libre or "Producto especial")) }}</div></td>
        <td class="center">{{ item.cantidad }}</td>
        {% if ns.has_entrega %}<td class="center">{% if item.entrega_min is not none and item.entrega_max is not none and item.entrega_unidad %}{% if item.entrega_min == item.entrega_max %}{{ item.entrega_min }} {{ item.entrega_unidad }}{% else %}{{ item.entrega_min }}–{{ item.entrega_max }} {{ item.entrega_unidad }}{% endif %}{% else %}—{% endif %}</td>{% endif %}
        <td class="right">{{ simbolo_moneda }} {{ "{:,.2f}".format(item.precio_unitario) }}</td>
        {% if ns.has_desc %}<td class="center">{% if (item.descuento_aplicado or 0) > 0 %}{{ "{:g}".format(item.descuento_aplicado|float) }}%{% else %}—{% endif %}</td>{% endif %}
        <td class="right">{{ simbolo_moneda }} {{ "{:,.2f}".format(item.subtotal) }}</td>
      </tr>
      {% endfor %}
    </tbody>
    <tfoot>
      {% if es_cotizacion %}
        <tr>
          <td colspan="{{ cols_label }}" class="right">subtotal({{ etiqueta_moneda_corta }})</td>
          <td class="right">{{ simbolo_moneda }} {{ "{:,.2f}".format(orden.total) }}</td>
        </tr>
      {% else %}
        <tr>
          <td colspan="{{ cols_label }}" class="right">SubTotal({{ etiqueta_moneda_corta }})</td>
          <td class="right">{{ simbolo_moneda }} {{ "{:,.2f}".format(orden.total) }}</td>
        </tr>
        <tr>
          <td colspan="{{ cols_label }}" class="right">IVA({{ iva_pct_label }})</td>
          <td class="right">{{ simbolo_moneda }} {{ "{:,.2f}".format(iva) }}</td>
        </tr>
        <tr>
          <td colspan="{{ cols_label }}" class="right">Total({{ etiqueta_moneda_corta }})</td>
          <td class="right">{{ simbolo_moneda }} {{ "{:,.2f}".format(gran_total) }}</td>
        </tr>
      {% endif %}
    </tfoot>
  </table>

  {% if es_cotizacion %}
  <div class="terms-title">CONDICIONES COMERCIALES:</div>
  <ul class="terms">
    {# Metadata fija (depende del estado de la cotización, no editable) #}
    <li>Los precios están expresados en <strong>{{ etiqueta_moneda }} ({{ orden.moneda }})</strong>{% if orden.moneda == "USD" %} — tipo de cambio referencia: {{ "{:,.4f}".format(orden.tipo_cambio) }} MXN/USD{% endif %}.</li>
    <li>Condiciones de pago: {{ orden.observaciones or "según acuerdo comercial" }}.</li>

    {# Bloque editable. orden.terminos_condiciones NULL → fallback hardcoded (legacy). #}
    {% if orden.terminos_condiciones is not none %}
      {% for linea in orden.terminos_condiciones.split('\n') %}
        {% if linea.strip() %}<li>{{ linea.strip() }}</li>{% endif %}
      {% endfor %}
    {% else %}
      <li><strong>Agregar el IVA correspondiente.</strong> Tiempo de entrega S.P.V.</li>
      <li><strong>Verificar que el material cotizado cumpla con sus requerimientos técnicos.</strong></li>
      <li>Todos los precios que incluyen instalación, servicios y capacitación están basados en nuestros horarios normales de trabajo (L-V 8:00-18:00 hrs) a menos de que sea estipulado de otra forma dentro de la cotización. Los cargos adicionales por horas trabajadas fuera de estos horarios u horas superiores a ocho (8) por día serán facturadas por separado.</li>
      <li>En caso de cancelación se cobrará el 25% del monto total.</li>
      <li>Los precios indicados no incluyen flete.</li>
      <li>Si se tiene el material en existencia y el cliente se encuentra ubicado en CDMX y/o área metropolitana se entregará en 2 a 3 días hábiles. En caso contrario el flete será cubierto por el cliente.</li>
      <li>Para procesar su pedido es necesario colocar una orden de compra indicando el número de cotización y aceptación de estas condiciones comerciales (más anticipo cuando aplique).</li>
      <li>La garantía de los productos es la que otorga cada fabricante.</li>
    {% endif %}

    {# Metadata sistema #}
    <li>Vigencia de esta cotización: <strong>{{ vigencia_dias }} días a partir de la fecha de emisión.</strong></li>
  </ul>
  {% endif %}

  <div class="firma">
    <div class="label">ATENTAMENTE</div>
    <div class="line"></div>
    <div class="name">{{ orden.vendedor.nombre if orden.vendedor else "Equipo DASIC" }}</div>
    <div class="mail">{% if orden.vendedor and orden.vendedor.email %}<a href="mailto:{{ orden.vendedor.email }}">{{ orden.vendedor.email }}</a>{% endif %}</div>
  </div>

  <div class="footer-bar"><span class="web">www.dasic.mx</span></div>
</div>
</body>
</html>
"""

# --- 1. CREAR ORDEN (POST) ---
@router.post("/", response_model=schemas.OrdenVentaResponse, dependencies=[Depends(allow_all_staff)])
def crear_orden(
    orden_data: schemas.OrdenVentaCreate,
    tipo_orden: models.EstatusOrden = models.EstatusOrden.COTIZACION,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    from app.security.permissions import require
    require(current_user, "create", "cotizacion")  # operativo: 403
    cliente = (
        db.query(models.Cliente)
        .filter(
            models.Cliente.id == orden_data.cliente_id,
        )
        .first()
    )
    if not cliente: raise HTTPException(404, "Cliente no encontrado")

    moneda_cotizacion = _normalize_currency(orden_data.moneda)
    tipo_cambio = _resolve_exchange_rate(moneda_cotizacion, orden_data.tipo_cambio)

    try:
        folio = _generar_folio(db, tipo_orden, current_user)

        # Si el cliente no envió terminos_condiciones (None), aplicamos los
        # defaults. Si envió cualquier string (incluso ""), respetamos su
        # decisión (puede haber elegido vaciar el bloque editable).
        terminos = orden_data.terminos_condiciones
        if terminos is None:
            terminos = _DEFAULT_TERMINOS

        nueva_orden = models.OrdenVenta(
            folio=folio,
            cliente_id=cliente.id,
            vendedor_id=current_user.id,
            estatus=tipo_orden,
            observaciones=orden_data.observaciones,
            moneda=moneda_cotizacion,
            tipo_cambio=tipo_cambio,
            fecha_vencimiento=datetime.utcnow() + timedelta(days=_quote_validity_days()),
            total=0,
            terminos_condiciones=terminos,
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
                    # SALIDA auditada (kardex) + lock pesimista vía aplicar_movimiento.
                    # El servicio valida stock no-negativo y levanta ValueError si falla.
                    try:
                        aplicar_movimiento(
                            db,
                            producto=producto,
                            tipo=TipoMovimientoStock.SALIDA.value,
                            cantidad=-item.cantidad,
                            referencia_tipo="venta_directa",
                            referencia_id=nueva_orden.id,
                            motivo=f"venta directa {nueva_orden.folio}",
                            usuario=current_user,
                        )
                    except ValueError as exc:
                        raise HTTPException(400, f"Stock insuficiente para {producto.sku}: {exc}")

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
            descuento_pct = Decimal(item.descuento or 0)
            precio_unit_bruto = costo_base * (Decimal("1.0") + (utilidad_pct / Decimal("100")))
            subtotal = (
                precio_unit_bruto
                * item.cantidad
                * (Decimal("1.0") - (descuento_pct / Decimal("100")))
            )
            total_orden += subtotal

            tipo_linea = _resolve_tipo_linea(item, producto)
            db.add(models.DetalleOrden(
                orden_id=nueva_orden.id,
                producto_id=producto.id if producto else None,
                sku_libre=sku_libre,
                descripcion_libre=descripcion_libre,
                moneda_origen_linea=moneda_origen_linea,
                costo_base_linea=costo_origen.quantize(Decimal("0.01")),
                cantidad=item.cantidad,
                # precio_unitario = bruto pre-descuento (lo que el cliente ve por unidad).
                # subtotal ya incluye el descuento aplicado.
                precio_unitario=precio_unit_bruto.quantize(Decimal("0.01")),
                utilidad_aplicada=utilidad_pct,
                descuento_aplicado=descuento_pct,
                subtotal=subtotal.quantize(Decimal("0.01")),
                tipo_linea=tipo_linea,
                proveedor_sugerido_id=getattr(item, "proveedor_sugerido_id", None),
                entrega_min=item.entrega_min,
                entrega_max=item.entrega_max,
                entrega_unidad=item.entrega_unidad,
            ))

            # Reserva inventario sólo si es producto del catálogo y la orden es cotización
            if (
                tipo_orden == models.EstatusOrden.COTIZACION
                and producto is not None
                and tipo_linea == "producto_catalogo"
            ):
                reservar_para_cotizacion(
                    db,
                    producto=producto,
                    cantidad=item.cantidad,
                    cotizacion_id=nueva_orden.id,
                    usuario=current_user,
                )

        nueva_orden.total = total_orden.quantize(Decimal("0.01"))

        # Deuda (Solo si es venta directa)
        if tipo_orden == models.EstatusOrden.PENDIENTE:
            total_con_iva = (total_orden * (Decimal("1.0") + _iva_rate())).quantize(Decimal("0.01"))
            deuda = models.TransaccionCliente(
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
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
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
        if orden_update.terminos_condiciones is not None:
            orden.terminos_condiciones = orden_update.terminos_condiciones
        orden.moneda = moneda_cotizacion
        orden.tipo_cambio = tipo_cambio
        orden.fecha_vencimiento = datetime.utcnow() + timedelta(days=_quote_validity_days())

        # Liberar reservas previas antes de borrar y reinsertar detalles
        liberar_reservas_cotizacion(
            db,
            cotizacion_id=orden.id,
            motivo="re-edición de cotización",
            usuario=current_user,
        )

        # Borrar detalles viejos
        db.query(models.DetalleOrden).filter(
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
            descuento_pct = Decimal(item.descuento or 0)
            precio_unit_bruto = costo_base * (Decimal("1.0") + (utilidad_pct / Decimal("100")))
            subtotal = (
                precio_unit_bruto
                * item.cantidad
                * (Decimal("1.0") - (descuento_pct / Decimal("100")))
            )
            total_orden += subtotal

            tipo_linea = _resolve_tipo_linea(item, producto)
            db.add(models.DetalleOrden(
                orden_id=orden.id,
                producto_id=producto.id if producto else None,
                sku_libre=sku_libre,
                descripcion_libre=descripcion_libre,
                moneda_origen_linea=moneda_origen_linea,
                costo_base_linea=costo_origen.quantize(Decimal("0.01")),
                cantidad=item.cantidad,
                precio_unitario=precio_unit_bruto.quantize(Decimal("0.01")),
                utilidad_aplicada=utilidad_pct,
                descuento_aplicado=descuento_pct,
                subtotal=subtotal.quantize(Decimal("0.01")),
                tipo_linea=tipo_linea,
                proveedor_sugerido_id=getattr(item, "proveedor_sugerido_id", None),
                entrega_min=item.entrega_min,
                entrega_max=item.entrega_max,
                entrega_unidad=item.entrega_unidad,
            ))

            if (
                producto is not None
                and tipo_linea == "producto_catalogo"
                and orden.estatus == models.EstatusOrden.COTIZACION
            ):
                reservar_para_cotizacion(
                    db,
                    producto=producto,
                    cantidad=item.cantidad,
                    cotizacion_id=orden.id,
                    usuario=current_user,
                )

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
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea una nueva versión de la cotización clonando partidas. La original
    queda archivada (no se modifica) y se devuelve la nueva versión."""
    origen = (
        db.query(models.OrdenVenta)
        .filter(
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
            ((models.OrdenVenta.cotizacion_origen_id == raiz_id) | (models.OrdenVenta.id == raiz_id)),
        )
        .count()
        + 1
    )

    folio_nuevo = _generar_folio(db, models.EstatusOrden.COTIZACION, current_user)
    # Formato versionado alineado al folio real DASIC: C-YYMMNNN + V<n>  (ej. C-2604227V2)
    folio_versionado = f"{folio_nuevo}V{siguiente_version}"

    nueva = models.OrdenVenta(
        folio=folio_versionado,
        cliente_id=origen.cliente_id,
        vendedor_id=current_user.id,
        estatus=models.EstatusOrden.COTIZACION,
        observaciones=origen.observaciones,
        terminos_condiciones=origen.terminos_condiciones,
        moneda=origen.moneda,
        tipo_cambio=origen.tipo_cambio,
        total=origen.total,
        fecha_vencimiento=datetime.utcnow() + timedelta(days=_quote_validity_days()),
        cotizacion_origen_id=raiz_id,
        version=siguiente_version,
    )
    db.add(nueva)
    db.flush()

    for det in origen.detalles:
        db.add(models.DetalleOrden(
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
            tipo_linea=det.tipo_linea,
            proveedor_sugerido_id=det.proveedor_sugerido_id,
            entrega_min=det.entrega_min,
            entrega_max=det.entrega_max,
            entrega_unidad=det.entrega_unidad,
        ))

    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/{id}/versiones", dependencies=[Depends(allow_all_staff)])
def listar_versiones(
    id: int,
    db: Session = Depends(get_db),
):
    base = (
        db.query(models.OrdenVenta)
        .filter(
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
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden or orden.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Orden no válida para conversión")
    _check_owner_or_403(orden, current_user, action="convert")

    try:
        # Verificar disponible considerando reservas de OTRAS cotizaciones.
        # Para cada línea de catálogo: stock_actual - reservas_de_otras_cotizaciones >= cantidad.
        for det in orden.detalles:
            if det.producto is None:
                continue
            if det.tipo_linea == "servicio" or det.producto.es_servicio:
                continue
            propia = det.cantidad
            reservado_total = reservas_activas(db, det.producto.id)
            otras = max(reservado_total - propia, 0)
            libre = (det.producto.stock_actual or 0) - otras
            if libre < det.cantidad:
                raise HTTPException(
                    400,
                    f"Stock insuficiente para {det.producto.sku} "
                    f"(libre={libre}, requerido={det.cantidad})",
                )

        # Convertir reservas en salidas reales (descuenta stock_actual)
        consumir_reservas_a_salida(db, cotizacion_id=orden.id, usuario=current_user)

        # Cambiar Estatus y Folio (formato real: C-YYMMNNN -> V-YYMMNNN; legacy: COT- -> VTA-)
        orden.estatus = models.EstatusOrden.PENDIENTE
        if orden.folio:
            if orden.folio.startswith("C-"):
                orden.folio = "V" + orden.folio[1:]
            elif orden.folio.startswith("COT-"):
                orden.folio = orden.folio.replace("COT-", "VTA-", 1)
        
        # Generar Deuda
        total_con_iva = (orden.total * (Decimal("1.0") + _iva_rate())).quantize(Decimal("0.01"))
        db.add(models.TransaccionCliente(
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
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    from app.security.permissions import is_owner_scoped, require
    require(current_user, "read", "cotizacion")  # operativo: 403
    query = db.query(models.OrdenVenta)
    if is_owner_scoped(current_user, "read", "cotizacion"):
        query = query.filter(models.OrdenVenta.vendedor_id == current_user.id)
    ordenes = query.order_by(desc(models.OrdenVenta.fecha_creacion)).limit(limit).all()

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
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
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
            "subtotal": d.subtotal,
            "entrega_min": d.entrega_min,
            "entrega_max": d.entrega_max,
            "entrega_unidad": d.entrega_unidad,
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
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden: raise HTTPException(404)

    iva = (orden.total * _iva_rate()).quantize(Decimal("0.01"))
    gran_total = (orden.total + iva).quantize(Decimal("0.01"))
    es_cotizacion = orden.estatus == models.EstatusOrden.COTIZACION
    tipo_doc = "COTIZACION" if es_cotizacion else "NOTA DE VENTA"
    simbolo_moneda = _currency_symbol(orden.moneda)
    etiqueta_moneda = "Dólares Americanos" if orden.moneda == "USD" else "Moneda Nacional"
    etiqueta_moneda_corta = "USD" if orden.moneda == "USD" else "MN"

    meses_es = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    if orden.fecha_creacion:
        f = orden.fecha_creacion
        fecha_str = f"{f.day} de {meses_es[f.month-1]} de {f.year}"
    else:
        fecha_str = ""
    vigencia_dias = (
        max((orden.fecha_vencimiento.date() - orden.fecha_creacion.date()).days, 0)
        if orden.fecha_vencimiento and orden.fecha_creacion
        else _quote_validity_days()
    )

    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_VENTA).render(
        orden=orden,
        iva=iva,
        gran_total=gran_total,
        tipo_doc=tipo_doc,
        es_cotizacion=es_cotizacion,
        simbolo_moneda=simbolo_moneda,
        etiqueta_moneda=etiqueta_moneda,
        etiqueta_moneda_corta=etiqueta_moneda_corta,
        vigencia_dias=vigencia_dias,
        fecha_str=fecha_str,
        iva_pct_label=_iva_pct_label(),
    )


# ---------------------------------------------------------------------------
# Bloque 5: Tracking, correo, WhatsApp, IA
# ---------------------------------------------------------------------------

class _SendEmailIn(BaseModel):
    to: EmailStr
    cc: Optional[List[EmailStr]] = None
    subject: Optional[str] = Field(default=None, max_length=200)
    mensaje: Optional[str] = Field(default=None, max_length=4000)
    incluir_pdf_link: bool = True


class _WhatsappLogIn(BaseModel):
    direccion: str = Field(default="OUTBOUND", pattern="^(OUTBOUND|INBOUND)$")
    destinatario: Optional[str] = Field(default=None, max_length=80)
    mensaje: str = Field(..., min_length=1, max_length=4000)


def _quote_summary(orden: "models.OrdenVenta") -> dict:
    ahora = datetime.utcnow().date()
    edad = max((ahora - orden.fecha_creacion.date()).days, 0) if orden.fecha_creacion else 0
    dias_restantes = (
        (orden.fecha_vencimiento.date() - ahora).days if orden.fecha_vencimiento else None
    )
    detalles_resumen = "; ".join(
        f"{(d.producto.sku_comercial if d.producto else (d.sku_libre or 'FANTASMA'))} x{d.cantidad}"
        for d in (orden.detalles or [])[:8]
    )
    return {
        "folio": orden.folio,
        "cliente": orden.cliente.nombre_empresa if orden.cliente else "",
        "total": float(orden.total or 0),
        "moneda": orden.moneda,
        "estatus": orden.estatus.value if hasattr(orden.estatus, "value") else str(orden.estatus),
        "edad_dias": edad,
        "dias_restantes": dias_restantes,
        "detalles_resumen": detalles_resumen,
    }


@router.post("/{id}/enviar-correo", dependencies=[Depends(allow_all_staff)])
def enviar_correo(
    id: int,
    payload: _SendEmailIn,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")

    asunto = (payload.subject or f"Cotización {orden.folio} - DASIC").strip()
    cuerpo = (payload.mensaje or "").strip()
    if not cuerpo:
        cuerpo = (
            f"Hola,\n\nAdjuntamos cotización {orden.folio} por un total de "
            f"{orden.moneda} {orden.total}.\n"
            "Cualquier duda quedamos atentos.\n\n— Equipo DASIC"
        )

    estatus = "DRY_RUN"
    error_detail: Optional[str] = None
    try:
        if smtp_configured():
            estatus = send_quote_email(
                to=str(payload.to),
                subject=asunto,
                body=cuerpo,
                cc=[str(c) for c in (payload.cc or [])] or None,
            )
        else:
            estatus = "DRY_RUN"
    except EmailDeliveryError as exc:
        estatus = "FAILED"
        error_detail = str(exc)

    evento = models.QuoteEvent(
        orden_id=orden.id,
        canal="EMAIL",
        direccion="OUTBOUND",
        estatus=estatus,
        asunto=asunto,
        cuerpo=cuerpo,
        destinatario=str(payload.to),
        creado_por_id=current_user.id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)

    if estatus == "FAILED":
        raise HTTPException(502, detail=f"SMTP falló: {error_detail}")

    return {
        "evento_id": evento.id,
        "estatus": estatus,
        "smtp_configurado": smtp_configured(),
    }


@router.post("/{id}/whatsapp-log", dependencies=[Depends(allow_all_staff)])
def whatsapp_log(
    id: int,
    payload: _WhatsappLogIn,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")

    evento = models.QuoteEvent(
        orden_id=orden.id,
        canal="WHATSAPP",
        direccion=payload.direccion,
        estatus="LOGGED",
        cuerpo=payload.mensaje,
        destinatario=payload.destinatario,
        creado_por_id=current_user.id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return {"evento_id": evento.id, "estatus": "LOGGED"}


@router.post("/{id}/ia-resumen", dependencies=[Depends(allow_all_staff)])
def ia_resumen(
    id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")

    summary = _quote_summary(orden)
    resultado = sugerir_proximo_paso(summary)

    evento = models.QuoteEvent(
        orden_id=orden.id,
        canal="IA",
        direccion="INTERNAL",
        estatus=resultado.get("modo", "HEURISTICO"),
        asunto=f"IA - próximo paso {orden.folio}",
        cuerpo=resultado.get("resumen", ""),
        creado_por_id=current_user.id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return {
        "evento_id": evento.id,
        "modo": resultado.get("modo"),
        "model": resultado.get("model"),
        "resumen": resultado.get("resumen"),
    }


@router.get("/{id}/eventos", dependencies=[Depends(allow_all_staff)])
def listar_eventos(
    id: int,
    db: Session = Depends(get_db),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.id == id,
        )
        .first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")

    eventos = (
        db.query(models.QuoteEvent)
        .filter(
            models.QuoteEvent.orden_id == orden.id,
        )
        .order_by(desc(models.QuoteEvent.creado_en))
        .limit(50)
        .all()
    )
    return [
        {
            "id": ev.id,
            "canal": ev.canal,
            "direccion": ev.direccion,
            "estatus": ev.estatus,
            "asunto": ev.asunto,
            "cuerpo": ev.cuerpo,
            "destinatario": ev.destinatario,
            "creado_en": ev.creado_en,
            "creado_por": ev.creado_por.nombre if ev.creado_por else None,
        }
        for ev in eventos
    ]


# --- 7. CANCELAR COTIZACIÓN (libera reservas) ---
@router.post("/{id}/cancelar", dependencies=[Depends(allow_all_staff)])
def cancelar_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(models.OrdenVenta.id == id)
        .first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")
    if orden.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Sólo se cancelan cotizaciones abiertas")
    _check_owner_or_403(orden, current_user, action="cancel")

    liberadas = liberar_reservas_cotizacion(
        db,
        cotizacion_id=orden.id,
        motivo="cancelación manual",
        usuario=current_user,
    )
    orden.estatus = models.EstatusOrden.CANCELADA
    db.commit()
    return {"ok": True, "folio": orden.folio, "productos_liberados": liberadas}


# --- 8. AUTO-OC: sugerir + generar ---
@router.post("/{id}/sugerir-oc", dependencies=[Depends(allow_all_staff)])
def sugerir_oc(id: int, db: Session = Depends(get_db)):
    from app.services.auto_oc_service import previsualizar_ocs
    orden = (
        db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")
    return previsualizar_ocs(db, orden)


@router.post("/{id}/generar-oc", dependencies=[Depends(allow_all_staff)])
def generar_oc_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    from app.services.auto_oc_service import generar_ocs
    orden = (
        db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    )
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")
    return {"ocs": generar_ocs(db, orden, usuario=current_user)}


# ============================================================
# CR (Cotizador Robusto): endpoints inteligentes
# ============================================================
import json as _cr_json
from sqlalchemy import func as _cr_func
from pydantic import BaseModel as _CRBase


@router.get("/auto-utilidad", dependencies=[Depends(allow_all_staff)])
def auto_utilidad(
    cliente_id: Optional[int] = None,
    producto_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Sugerencia inteligente de % de utilidad.

    Prioridad: promedio para (cliente,producto) → cliente → producto → default 30.
    Devuelve {sugerido: float, fuente: str, n: int}.
    """
    base = db.query(models.DetalleOrden).join(
        models.OrdenVenta, models.DetalleOrden.orden_id == models.OrdenVenta.id
    ).filter(
        models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
        models.DetalleOrden.utilidad_aplicada.is_not(None),
        models.DetalleOrden.utilidad_aplicada > 0,
    )

    def _avg(rows):
        vals = [float(r.utilidad_aplicada) for r in rows if r.utilidad_aplicada]
        return round(sum(vals) / len(vals), 2) if vals else None

    if cliente_id and producto_id:
        rows = base.filter(
            models.OrdenVenta.cliente_id == cliente_id,
            models.DetalleOrden.producto_id == producto_id,
        ).limit(50).all()
        v = _avg(rows)
        if v is not None:
            return {"sugerido": v, "fuente": "cliente_producto", "n": len(rows)}

    if cliente_id:
        rows = base.filter(models.OrdenVenta.cliente_id == cliente_id).limit(100).all()
        v = _avg(rows)
        if v is not None:
            return {"sugerido": v, "fuente": "cliente", "n": len(rows)}

    if producto_id:
        rows = base.filter(models.DetalleOrden.producto_id == producto_id).limit(100).all()
        v = _avg(rows)
        if v is not None:
            return {"sugerido": v, "fuente": "producto", "n": len(rows)}

    return {"sugerido": 30.0, "fuente": "default", "n": 0}


class _PlantillaIn(_CRBase):
    nombre: str
    descripcion: Optional[str] = None
    lineas: list


@router.get("/plantillas", dependencies=[Depends(allow_all_staff)])
def listar_plantillas(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Plantillas del usuario + plantillas globales (usuario_id NULL)."""
    rows = (
        db.query(models.PlantillaCotizacion)
        .filter(
            (models.PlantillaCotizacion.usuario_id == current_user.id)
            | (models.PlantillaCotizacion.usuario_id.is_(None))
        )
        .order_by(desc(models.PlantillaCotizacion.creado_en))
        .all()
    )
    out = []
    for p in rows:
        try:
            lineas = _cr_json.loads(p.lineas or "[]")
        except Exception:
            lineas = []
        out.append({
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "lineas": lineas,
            "n_lineas": len(lineas),
            "creado_en": p.creado_en.isoformat() if p.creado_en else None,
            "es_global": p.usuario_id is None,
            "es_propia": p.usuario_id == current_user.id,
        })
    return out


@router.post("/plantillas", dependencies=[Depends(allow_all_staff)])
def crear_plantilla(
    payload: _PlantillaIn,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    if not payload.nombre or not payload.nombre.strip():
        raise HTTPException(400, "nombre requerido")
    if not isinstance(payload.lineas, list) or not payload.lineas:
        raise HTTPException(400, "lineas debe ser una lista no vacía")

    nueva = models.PlantillaCotizacion(
        nombre=payload.nombre.strip()[:120],
        descripcion=(payload.descripcion or "").strip() or None,
        usuario_id=current_user.id,
        lineas=_cr_json.dumps(payload.lineas, ensure_ascii=False),
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"id": nueva.id, "nombre": nueva.nombre, "n_lineas": len(payload.lineas)}


@router.delete("/plantillas/{id}", dependencies=[Depends(allow_all_staff)])
def eliminar_plantilla(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    p = db.query(models.PlantillaCotizacion).filter(models.PlantillaCotizacion.id == id).first()
    if not p:
        raise HTTPException(404, "Plantilla no encontrada")
    # Solo el dueño o admin puede borrar
    from app.security.permissions import _normalize_role
    rol = _normalize_role(getattr(current_user, "rol", None))
    is_admin = rol in (models.RolUsuario.ADMINISTRADOR, models.RolUsuario.SUPERADMIN)
    if not is_admin and p.usuario_id != current_user.id:
        raise HTTPException(403, "Solo puedes borrar tus propias plantillas")
    db.delete(p)
    db.commit()
    return {"ok": True, "id": id}


@router.get("/productos-relacionados/{producto_id}", dependencies=[Depends(allow_all_staff)])
def productos_relacionados(
    producto_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Co-ocurrencia: productos que aparecen en las MISMAS cotizaciones que este.

    Devuelve top N por frecuencia de aparición conjunta.
    """
    # subquery: ids de órdenes que contienen el producto pivot
    ordenes_pivot = (
        db.query(models.DetalleOrden.orden_id)
        .filter(models.DetalleOrden.producto_id == producto_id)
        .subquery()
    )
    rows = (
        db.query(
            models.Producto.id,
            models.Producto.sku_comercial,
            models.Producto.sku,
            models.Producto.nombre,
            models.Producto.marca,
            models.Producto.stock_actual,
            _cr_func.count(models.DetalleOrden.id).label("cooccurrences"),
        )
        .join(models.DetalleOrden, models.DetalleOrden.producto_id == models.Producto.id)
        .filter(
            models.DetalleOrden.orden_id.in_(ordenes_pivot),
            models.Producto.id != producto_id,
        )
        .group_by(models.Producto.id)
        .order_by(desc(_cr_func.count(models.DetalleOrden.id)))
        .limit(limit)
        .all()
    )
    return [
        {
            "producto_id": r.id,
            "sku": r.sku_comercial or r.sku,
            "nombre": r.nombre,
            "marca": r.marca,
            "stock_actual": r.stock_actual,
            "co_apariciones": int(r.cooccurrences),
        }
        for r in rows
    ]


@router.get("/ultima-cotizacion-cliente/{cliente_id}", dependencies=[Depends(allow_all_staff)])
def ultima_cotizacion_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Para mostrar widget "última cotización de este cliente"."""
    from app.security.permissions import is_owner_scoped

    q = db.query(models.OrdenVenta).filter(models.OrdenVenta.cliente_id == cliente_id)
    if is_owner_scoped(current_user, "read", "cotizacion"):
        q = q.filter(models.OrdenVenta.vendedor_id == current_user.id)
    o = q.order_by(desc(models.OrdenVenta.fecha_creacion)).first()
    if not o:
        return None
    fc = o.fecha_creacion.replace(tzinfo=None) if o.fecha_creacion and o.fecha_creacion.tzinfo else o.fecha_creacion
    dias = (datetime.utcnow() - fc).days if fc else None
    return {
        "id": o.id,
        "folio": o.folio,
        "fecha": o.fecha_creacion.isoformat() if o.fecha_creacion else None,
        "dias_atras": dias,
        "total": float(o.total or 0),
        "moneda": o.moneda,
        "estatus": o.estatus.value if hasattr(o.estatus, "value") else str(o.estatus),
    }


@router.get("/sinonimos", dependencies=[Depends(allow_all_staff)])
def sinonimos_industriales():
    """Diccionario para búsqueda semántica en el cotizador."""
    from pathlib import Path as _P
    p = _P(__file__).resolve().parent.parent / "data" / "sinonimos.json"
    if not p.exists():
        return {"entradas": []}
    return _cr_json.loads(p.read_text(encoding="utf-8"))
