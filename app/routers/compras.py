from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from decimal import Decimal
from datetime import datetime
from jinja2 import Environment, BaseLoader

from app import models
from app import schemas
from app.db import get_db
from app.security import allow_admin_asistente, get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/compras", tags=["Proveedores y Gastos"])

# --- PLANTILLA PDF PROFESIONAL (CORREGIDA) ---
PDF_TEMPLATE_COMPRA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Orden de Compra #{{ orden.id }}</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; padding: 0; margin: 0; }
        .container { width: 100%; max-width: 800px; margin: 0 auto; padding: 20px; }
        
        /* HEADER */
        .header-table { width: 100%; margin-bottom: 30px; }
        .company-name { font-size: 28px; font-weight: bold; color: #1e3a8a; margin: 0; } /* Azul Dasic */
        .company-info { font-size: 12px; color: #666; line-height: 1.4; }
        .invoice-title { font-size: 24px; font-weight: bold; text-align: right; color: #333; }
        .invoice-details { text-align: right; font-size: 13px; margin-top: 5px; }
        
        /* PROVEEDOR BOX */
        .box-section { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin-bottom: 30px; display: flex; justify-content: space-between; }
        .box-title { font-size: 11px; font-weight: bold; text-transform: uppercase; color: #64748b; margin-bottom: 5px; }
        .box-content { font-size: 14px; font-weight: bold; color: #333; }
        .box-sub { font-size: 12px; color: #555; }

        /* TABLA PRODUCTOS */
        .items-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }
        .items-table th { background-color: #1e3a8a; color: white; padding: 10px; text-align: left; font-weight: bold; text-transform: uppercase; font-size: 11px; }
        .items-table td { padding: 10px; border-bottom: 1px solid #eee; }
        .items-table tr:nth-child(even) { background-color: #f8fafc; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        
        /* TOTALES */
        .totals-section { width: 40%; margin-left: auto; font-size: 14px; }
        .total-row { display: flex; justify-content: space-between; padding: 5px 0; }
        .total-final { font-size: 18px; font-weight: bold; color: #1e3a8a; border-top: 2px solid #1e3a8a; padding-top: 10px; margin-top: 5px; }

        /* FIRMAS Y FOOTER */
        .signatures { margin-top: 80px; display: flex; justify-content: space-between; padding: 0 50px; }
        .sig-line { width: 200px; border-top: 1px solid #333; text-align: center; font-size: 12px; padding-top: 5px; }
        .footer { margin-top: 50px; text-align: center; font-size: 10px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
</head>
<body onload="window.print()">
    <div class="container">
        
        <table class="header-table">
            <tr>
                <td width="60%">
                    <div style="font-size: 40px; color: #1e3a8a; font-weight:900;">DASIC</div> 
                    <div class="company-name">ERP System</div>
                    <div class="company-info">
                       Development of Automation System and Industrial Control<br>
                        Av. Industrial 123, Ciudad de México<br>
                        RFC: DAS-220101-ABC<br>
                        contacto@dasic.mx | (55) 1234-5678
                    </div>
                </td>
                <td width="40%" style="vertical-align: top;">
                    <div class="invoice-title">ORDEN DE COMPRA</div>
                    <div class="invoice-details">
                        <strong>Folio Interno:</strong> #OC-{{ "%04d" | format(orden.id) }}<br>
                        <strong>Fecha Emisión:</strong> {{ orden.fecha.strftime('%d/%m/%Y') }}<br>
                        <strong>Estado:</strong> {{ orden.estatus | upper }}
                    </div>
                </td>
            </tr>
        </table>

        <div class="box-section">
            <div style="width: 48%;">
                <div class="box-title">PROVEEDOR</div>
                <div class="box-content">{{ orden.proveedor.nombre_empresa }}</div>
                <div class="box-sub">Atn: {{ orden.proveedor.contacto_nombre }}</div>
                <div class="box-sub">{{ orden.proveedor.email }}</div>
                <div class="box-sub">{{ orden.proveedor.telefono }}</div>
            </div>
            <div style="width: 48%;">
                <div class="box-title">ENVIAR A (ALMACÉN)</div>
                <div class="box-content">Almacén General DASIC</div>
                <div class="box-sub">Calle Principal #45</div>
                <div class="box-sub">Recibo de Mercancía: Lunes a Viernes</div>
            </div>
        </div>

        <table class="items-table">
            <thead>
                <tr>
                    <th width="15%">SKU</th>
                    <th width="45%">Descripción</th>
                    <th width="10%" class="text-center">Cant.</th>
                    <th width="15%" class="text-right">Costo Unit.</th>
                    <th width="15%" class="text-right">Importe</th>
                </tr>
            </thead>
            <tbody>
                {% for item in orden.detalles %}
                <tr>
                    <td style="font-weight:bold; color:#555;">{{ item.producto.sku }}</td>
                    <td>{{ item.producto.nombre }}</td>
                    <td class="text-center">{{ item.cantidad }}</td>
                    <td class="text-right">${{ "{:,.2f}".format(item.costo_unitario) }}</td>
                    <td class="text-right font-bold">${{ "{:,.2f}".format(item.costo_unitario * item.cantidad) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-section">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>${{ "{:,.2f}".format(orden.total) }}</span>
            </div>
            <div class="total-row" style="color: #666;">
                <span>IVA (16%) (Estimado):</span>
                <span>${{ "{:,.2f}".format(iva) }}</span>
            </div>
            <div class="total-row total-final">
                <span>TOTAL:</span>
                <span>${{ "{:,.2f}".format(gran_total) }}</span>
            </div>
        </div>

        <div class="signatures">
            <div class="sig-line">
                Autorizado por<br><strong>Gerencia de Compras</strong>
            </div>
            <div class="sig-line">
                Recibido por<br><strong>Almacén</strong>
            </div>
        </div>

        <div class="footer">
            Documento generado electrónicamente por DASIC ERP System.
        </div>
    </div>
</body>
</html>
"""

# --- SCHEMAS ---
class DetalleCompraInput(BaseModel):
    producto_id: int
    cantidad: int
    costo_unitario: Decimal 

class CompraInput(BaseModel):
    proveedor_id: int
    detalles: List[DetalleCompraInput]
    folio_factura: str = "PENDIENTE"

# --- ENDPOINTS ---

@router.get("/proveedores", response_model=List[schemas.ProveedorResponse])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(models.Proveedor).all()

@router.post("/proveedores", response_model=schemas.ProveedorResponse)
def crear_proveedor(proveedor: schemas.ProveedorCreate, db: Session = Depends(get_db)):
    nuevo = models.Proveedor(**proveedor.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# Listar Historial
@router.get("/historial")
def listar_historial_compras(limit: int = 50, db: Session = Depends(get_db)):
    ordenes = db.query(models.OrdenCompra)\
        .order_by(desc(models.OrdenCompra.fecha))\
        .limit(limit).all()
    
    resultado = []
    for o in ordenes:
        resultado.append({
            "id": o.id,
            "fecha": o.fecha,
            "proveedor": o.proveedor.nombre_empresa,
            "total": o.total,
            "estatus": o.estatus
        })
    return resultado


@router.get("/cotizacion/{quote_id}/borrador", dependencies=[Depends(allow_admin_asistente)])
def borrador_orden_compra_desde_cotizacion(
    quote_id: int,
    db: Session = Depends(get_db),
):
    quote = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == quote_id).first()
    if not quote:
        raise HTTPException(404, "Cotización no encontrada")
    if quote.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Solo se puede generar borrador desde cotizaciones")

    detalles = []
    total_estimado = Decimal("0")
    symbol = "US$" if quote.moneda == "USD" else "$"

    for item in quote.detalles:
        producto = item.producto
        costo_unitario = Decimal(producto.costo_compra or 0)
        if (producto.moneda_compra or "MXN").upper() != quote.moneda:
            if quote.moneda == "USD":
                costo_unitario = costo_unitario / Decimal(quote.tipo_cambio or 1)
            else:
                costo_unitario = costo_unitario * Decimal(quote.tipo_cambio or 1)

        importe = (costo_unitario * item.cantidad).quantize(Decimal("0.01"))
        total_estimado += importe
        detalles.append(
            {
                "producto_id": producto.id,
                "sku": producto.sku_comercial or producto.sku,
                "nombre": producto.nombre,
                "cantidad": item.cantidad,
                "costo_unitario": costo_unitario.quantize(Decimal("0.01")),
                "importe": importe,
                "moneda": symbol,
            }
        )

    return {
        "cotizacion": {
            "id": quote.id,
            "folio": quote.folio,
            "cliente": quote.cliente.nombre_empresa,
            "observaciones": quote.observaciones,
        },
        "moneda": symbol,
        "total_estimado": total_estimado.quantize(Decimal("0.01")),
        "detalles": detalles,
        "nota": "Borrador de orden de compra. No genera stock ni cuentas por pagar.",
    }

@router.post("/registrar-entrada", dependencies=[Depends(allow_admin_asistente)])
def registrar_compra(compra: CompraInput, db: Session = Depends(get_db)):
    proveedor = db.query(models.Proveedor).filter(models.Proveedor.id == compra.proveedor_id).first()
    if not proveedor: raise HTTPException(404, "Proveedor no encontrado")

    try:
        total = Decimal(0)
        nueva_orden = models.OrdenCompra(proveedor_id=proveedor.id, fecha=datetime.now(), total=0)
        db.add(nueva_orden)
        db.flush()

        for item in compra.detalles:
            prod = db.query(models.Producto).filter(models.Producto.id == item.producto_id).first()
            if prod:
                prod.stock_actual += item.cantidad
                prod.costo_compra = item.costo_unitario
                total += item.costo_unitario * item.cantidad
                db.add(models.DetalleCompra(
                    orden_compra_id=nueva_orden.id, producto_id=prod.id,
                    cantidad=item.cantidad, costo_unitario=item.costo_unitario
                ))
        
        nueva_orden.total = total
        
        # Deuda
        db.add(models.TransaccionProveedor(
            proveedor_id=proveedor.id, tipo=models.TipoMovimiento.CARGO, monto=total,
            descripcion=f"Compra OC #{nueva_orden.id} - {compra.folio_factura}"
        ))
        proveedor.saldo_actual += total
        db.commit()
        return {"mensaje": "Ok", "id": nueva_orden.id}
    except Exception as e:
        db.rollback()
        raise e

@router.post("/registrar-pago", dependencies=[Depends(allow_admin_asistente)])
def pagar_proveedor(
    proveedor_id: int,
    monto: Decimal,
    ref: str = "Pago",
    db: Session = Depends(get_db),
):
    prov = db.query(models.Proveedor).filter(models.Proveedor.id == proveedor_id).first()
    if not prov: raise HTTPException(404, "Proveedor no encontrado")
    
    db.add(models.TransaccionProveedor(
        proveedor_id=prov.id,
        tipo=models.TipoMovimiento.ABONO,
        monto=monto,
        descripcion=f"PAGO: {ref}",
    ))
    prov.saldo_actual -= monto
    db.commit()
    return {"mensaje": "Pago registrado", "nuevo_saldo": prov.saldo_actual}

@router.get("/{id}/imprimir", response_class=HTMLResponse)
def imprimir_oc(id: int, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == id).first()
    if not orden: raise HTTPException(404)
    
    # CÁLCULOS SEGUROS EN PYTHON (CORRECCIÓN CLAVE)
    iva = orden.total * Decimal("0.16")
    gran_total = orden.total + iva
    
    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_COMPRA).render(
        orden=orden, 
        iva=iva, 
        gran_total=gran_total
    )
