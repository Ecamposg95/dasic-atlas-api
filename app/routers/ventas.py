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

# --- PLANTILLA PDF COTIZACIÓN (DISEÑO CLIENTE) ---
PDF_TEMPLATE_VENTA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ tipo_doc }} {{ orden.folio }}</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        
        /* HEADER */
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #10b981; padding-bottom: 20px; margin-bottom: 30px; }
        .company-name { font-size: 32px; font-weight: 900; color: #064e3b; margin: 0; }
        .doc-title { font-size: 24px; font-weight: bold; text-align: right; color: #333; text-transform: uppercase; }
        .meta-info { font-size: 12px; color: #666; text-align: right; line-height: 1.5; }
        
        /* CLIENTE BOX */
        .client-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; margin-bottom: 30px; display: flex; justify-content: space-between; }
        .label { font-size: 10px; font-weight: bold; text-transform: uppercase; color: #15803d; letter-spacing: 1px; }
        .value { font-size: 14px; font-weight: bold; color: #333; margin-top: 2px; }
        
        /* TABLA */
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px; }
        th { background: #065f46; color: white; padding: 12px; text-align: left; text-transform: uppercase; font-size: 11px; }
        td { padding: 12px; border-bottom: 1px solid #eee; }
        tr:nth-child(even) { background: #f9fafb; }
        
        /* TOTALES */
        .totals { width: 40%; margin-left: auto; font-size: 14px; }
        .row { display: flex; justify-content: space-between; padding: 5px 0; }
        .grand-total { font-size: 20px; font-weight: bold; color: #064e3b; border-top: 2px solid #064e3b; padding-top: 10px; margin-top: 10px; }
        
        /* FOOTER */
        .footer { margin-top: 60px; text-align: center; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 15px; }
    </style>
</head>
<body onload="window.print()">
    <div class="container">
        <div class="header">
            <div>
                <div class="company-name">DASIC</div>
                <div style="font-size: 12px; color: #555;">Soluciones en Automatización</div>
            </div>
            <div>
                <div class="doc-title">{{ tipo_doc }}</div>
                <div class="meta-info">
                    Folio: <strong>{{ orden.folio }}</strong><br>
                    Fecha: {{ orden.fecha_creacion.strftime('%d/%m/%Y') }}<br>
                    Vendedor: {{ orden.vendedor.nombre }}
                </div>
            </div>
        </div>

        <div class="client-box">
            <div style="width: 50%;">
                <div class="label">Cliente</div>
                <div class="value">{{ orden.cliente.nombre_empresa }}</div>
                <div style="font-size: 12px;">{{ orden.cliente.contacto_nombre }}</div>
                <div style="font-size: 12px;">{{ orden.cliente.email }}</div>
            </div>
            <div style="width: 40%;">
                <div class="label">Condiciones</div>
                <div class="value" style="font-size: 12px; font-weight: normal;">
                    {{ orden.observaciones or "Sin observaciones adicionales." }}
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th width="15%">SKU</th>
                    <th width="45%">Descripción</th>
                    <th width="10%" style="text-align: center;">Cant.</th>
                    <th width="15%" style="text-align: right;">Precio Unit.</th>
                    <th width="15%" style="text-align: right;">Importe</th>
                </tr>
            </thead>
            <tbody>
                {% for item in orden.detalles %}
                <tr>
                    <td style="font-weight: bold; color: #555;">{{ item.producto.sku }}</td>
                    <td>{{ item.producto.nombre }}</td>
                    <td style="text-align: center;">{{ item.cantidad }}</td>
                    <td style="text-align: right;">${{ "{:,.2f}".format(item.precio_unitario) }}</td>
                    <td style="text-align: right;">${{ "{:,.2f}".format(item.subtotal) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals">
            <div class="row">
                <span>Subtotal:</span>
                <span>${{ "{:,.2f}".format(orden.total) }}</span>
            </div>
            <div class="row">
                <span>IVA (16%):</span>
                <span>${{ "{:,.2f}".format(iva) }}</span>
            </div>
            <div class="row grand-total">
                <span>TOTAL:</span>
                <span>${{ "{:,.2f}".format(gran_total) }}</span>
            </div>
        </div>

        <div class="footer">
            {% if orden.estatus.value == 'cotizacion' %}
                Precios sujetos a cambio sin previo aviso. Esta cotización tiene una vigencia de 15 días.
            {% else %}
                Gracias por su compra. Favor de conservar este documento para cualquier aclaración.
            {% endif %}
            <br>www.dasic.com
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
        # Generar Folio
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
            
            # Validar Stock si es Venta
            if tipo_orden != EstatusOrden.COTIZACION:
                if producto.stock_actual < item.cantidad:
                    raise HTTPException(400, f"Stock insuficiente para {producto.sku}")
                producto.stock_actual -= item.cantidad

            # Precio (Aquí podrías añadir lógica de listas de precios)
            precio = producto.precio_publico
            subtotal = precio * item.cantidad
            total_orden += subtotal
            
            db.add(models.DetalleOrden(
                orden_id=nueva_orden.id,
                producto_id=producto.id,
                cantidad=item.cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            ))

        nueva_orden.total = total_orden
        
        # Generar Deuda si es Venta Pendiente
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

# NUEVO: Historial de Ventas
@router.get("/historial")
def listar_historial(limit: int = 50, db: Session = Depends(database.get_db)):
    ordenes = db.query(models.OrdenVenta)\
        .order_by(desc(models.OrdenVenta.fecha_creacion))\
        .limit(limit).all()
    
    # Respuesta simplificada para tabla
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

    # Cálculos seguros
    iva = orden.total * Decimal("0.16")
    gran_total = orden.total + iva
    tipo_doc = "COTIZACIÓN" if orden.estatus == EstatusOrden.COTIZACION else "NOTA DE VENTA"

    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_VENTA).render(
        orden=orden, iva=iva, gran_total=gran_total, tipo_doc=tipo_doc
    )

# CONVERTIR
@router.post("/{id}/convertir", dependencies=[Depends(allow_all_staff)])
def convertir_cotizacion(id: int, db: Session = Depends(database.get_db)):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden or orden.estatus != EstatusOrden.COTIZACION:
        raise HTTPException(400, "Orden no válida para conversión")

    try:
        # Descontar Stock
        for det in orden.detalles:
            if det.producto.stock_actual < det.cantidad:
                raise HTTPException(400, f"Stock insuficiente para {det.producto.sku}")
            det.producto.stock_actual -= det.cantidad
        
        # Cambiar Estatus y Folio
        orden.estatus = EstatusOrden.PENDIENTE
        orden.folio = orden.folio.replace("COT", "VTA")
        
        # Generar Deuda
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