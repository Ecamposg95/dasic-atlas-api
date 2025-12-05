from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from decimal import Decimal
from datetime import datetime
from jinja2 import Environment, BaseLoader

import database
import models
import schemas
from auth import get_current_user, allow_all_staff
from models import EstatusOrden, TipoMovimiento

router = APIRouter(prefix="/api/ventas", tags=["Ventas y Cotizaciones"])

# --- PLANTILLA PDF CON TÉRMINOS Y CONDICIONES ---
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
        .desc-text { color: #dc2626; font-size: 10px; display: block; }

        /* TOTALES */
        .totals-container { display: flex; justify-content: flex-end; margin-bottom: 30px; }
        .totals-box { width: 40%; }
        .total-row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 14px; color: #475569; }
        .grand-total { font-size: 20px; font-weight: bold; color: #1e3a8a; border-top: 2px solid #1e3a8a; padding-top: 10px; margin-top: 5px; }

        /* --- AQUÍ ESTÁ EL TEXTO QUE PEDISTE --- */
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
                    <td style="font-weight: bold; color: #475569;">{{ item.producto.sku }}</td>
                    <td>
                        {{ item.producto.nombre }}
                        {% if item.descuento_aplicado > 0 %}
                            <span class="desc-text">(Descuento aplicado: {{ item.descuento_aplicado|int }}%)</span>
                        {% endif %}
                    </td>
                    <td class="text-center">{{ item.cantidad }}</td>
                    <td class="text-right">${{ "{:,.2f}".format(item.precio_unitario) }}</td>
                    <td class="text-right font-bold text-slate-700">${{ "{:,.2f}".format(item.subtotal) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-container">
            <div class="totals-box">
                <div class="total-row">
                    <span>Subtotal:</span>
                    <span>${{ "{:,.2f}".format(orden.total) }}</span>
                </div>
                <div class="total-row">
                    <span>IVA (16%):</span>
                    <span>${{ "{:,.2f}".format(iva) }}</span>
                </div>
                <div class="total-row grand-total">
                    <span>TOTAL:</span>
                    <span>${{ "{:,.2f}".format(gran_total) }}</span>
                </div>
            </div>
        </div>

        <div class="terms-box">
            <div class="terms-title">Términos y Condiciones Comerciales</div>
            <ul>
                <li>Precios sujetos a cambio sin previo aviso. Cotización en Moneda Nacional.</li>
                <li>Vigencia de la cotización: <strong>15 días naturales</strong>.</li>
                <li>Tiempo de entrega sujeto a disponibilidad de stock al momento de confirmar el pedido.</li>
                <li>En caso de requerir factura, favor de solicitarla dentro del mismo mes de compra.</li>
                <li>{{ orden.observaciones or "Sin observaciones adicionales." }}</li>
            </ul>

            <div class="bank-info">
                <strong>DATOS BANCARIOS PARA TRANSFERENCIA:</strong><br>
                Banco: <strong>BBVA Bancomer</strong> &nbsp;|&nbsp; Beneficiario: <strong>DASIC S.A. DE C.V.</strong><br>
                Cuenta: <strong>0123 4567 89</strong> &nbsp;|&nbsp; CLABE: <strong>012 345 67890123456 7</strong>
            </div>
        </div>

        <div class="footer">
            www.dasic.com | Soluciones integrales para la industria
        </div>
    </div>
</body>
</html>
"""

# --- ENDPOINTS ---

@router.post("/", response_model=schemas.OrdenVentaResponse, dependencies=[Depends(allow_all_staff)])
def crear_orden(
    orden_data: schemas.OrdenVentaCreate,
    tipo_orden: EstatusOrden = EstatusOrden.COTIZACION, 
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == orden_data.cliente_id).first()
    if not cliente: raise HTTPException(404, "Cliente no encontrado")

    try:
        count = db.query(models.OrdenVenta).count()
        prefijo = "COT" if tipo_orden == EstatusOrden.COTIZACION else "VTA"
        folio = f"{prefijo}-{count + 1:04d}"

        nueva_orden = models.OrdenVenta(
            folio=folio,
            cliente_id=cliente.id,
            vendedor_id=current_user.id,
            estatus=tipo_orden,
            observaciones=orden_data.observaciones,
            total=0
        )
        db.add(nueva_orden)
        db.flush()

        total_orden = Decimal(0)
        
        for item in orden_data.detalles:
            producto = db.query(models.Producto).filter(models.Producto.id == item.producto_id).first()
            if not producto: raise HTTPException(404, f"Producto {item.producto_id} no existe")
            
            if tipo_orden != EstatusOrden.COTIZACION:
                if producto.stock_actual < item.cantidad:
                    raise HTTPException(400, f"Stock insuficiente para {producto.sku}")
                producto.stock_actual -= item.cantidad

            # LÓGICA DE DESCUENTOS (Backend)
            precio_base = producto.precio_publico
            descuento_dec = Decimal(item.descuento) / 100
            precio_final = precio_base * (1 - descuento_dec)
            
            subtotal = precio_final * item.cantidad
            total_orden += subtotal
            
            db.add(models.DetalleOrden(
                orden_id=nueva_orden.id,
                producto_id=producto.id,
                cantidad=item.cantidad,
                precio_unitario=precio_final,
                descuento_aplicado=item.descuento,
                subtotal=subtotal
            ))

        nueva_orden.total = total_orden
        
        if tipo_orden == EstatusOrden.PENDIENTE:
            total_con_iva = total_orden * Decimal("1.16")
            deuda = models.TransaccionCliente(
                cliente_id=cliente.id,
                tipo=TipoMovimiento.CARGO,
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

# Historial
@router.get("/historial")
def listar_historial(limit: int = 50, db: Session = Depends(database.get_db)):
    ordenes = db.query(models.OrdenVenta)\
        .order_by(desc(models.OrdenVenta.fecha_creacion))\
        .limit(limit).all()
    
    return [{
        "id": o.id,
        "folio": o.folio,
        "fecha": o.fecha_creacion,
        "cliente": o.cliente.nombre_empresa,
        "total": o.total,
        "estatus": o.estatus
    } for o in ordenes]

# PDF
@router.get("/{id}/pdf", response_class=HTMLResponse)
def generar_pdf(id: int, db: Session = Depends(database.get_db)):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden: raise HTTPException(404)

    iva = orden.total * Decimal("0.16")
    gran_total = orden.total + iva
    tipo_doc = "COTIZACIÓN" if orden.estatus == EstatusOrden.COTIZACION else "NOTA DE VENTA"

    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_VENTA).render(
        orden=orden, iva=iva, gran_total=gran_total, tipo_doc=tipo_doc
    )

# Convertir
@router.post("/{id}/convertir", dependencies=[Depends(allow_all_staff)])
def convertir_cotizacion(id: int, db: Session = Depends(database.get_db)):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden or orden.estatus != EstatusOrden.COTIZACION:
        raise HTTPException(400, "Orden no válida para conversión")

    try:
        for det in orden.detalles:
            if det.producto.stock_actual < det.cantidad:
                raise HTTPException(400, f"Stock insuficiente para {det.producto.sku}")
            det.producto.stock_actual -= det.cantidad
        
        orden.estatus = EstatusOrden.PENDIENTE
        orden.folio = orden.folio.replace("COT", "VTA")
        
        total_con_iva = orden.total * Decimal("1.16")
        db.add(models.TransaccionCliente(
            cliente_id=orden.cliente_id,
            tipo=TipoMovimiento.CARGO,
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