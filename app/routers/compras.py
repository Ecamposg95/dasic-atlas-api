from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from typing import List
from decimal import Decimal
from datetime import datetime
from jinja2 import Environment, BaseLoader

from app import models
from app import schemas
from app.core.config import get_settings
from app.db import get_db
from app.models.enums import TipoMovimientoStock
from app.security import allow_admin_asistente, get_current_user
from app.services.stock_service import aplicar_movimiento
from pydantic import BaseModel


def _iva_rate() -> Decimal:
    return Decimal(str(get_settings().iva_rate))


def _iva_pct_label() -> str:
    return f"{get_settings().iva_rate * 100:g}%"

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
                        <strong>Folio:</strong> {{ orden.folio or ("OC-%04d" | format(orden.id)) }}<br>
                        <strong>Fecha Emisión:</strong> {{ orden.fecha.strftime('%d/%m/%Y') }}<br>
                        <strong>Moneda:</strong> {{ orden.moneda or "MXN" }}<br>
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
                <span>IVA ({{ iva_pct_label }}) (Estimado):</span>
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


# --- SCHEMAS para editor de OC (Fase 5) ---
from typing import Optional  # noqa: E402


class OCLineaIn(BaseModel):
    """Línea editable de OC. Producto del catálogo o fantasma."""
    producto_id: Optional[int] = None
    sku_libre: Optional[str] = None
    descripcion_libre: Optional[str] = None
    cantidad: int
    costo_unitario: Decimal
    moneda_origen: Optional[str] = None


class OCEditorIn(BaseModel):
    proveedor_id: int
    cotizacion_id: Optional[int] = None
    moneda: str = "MXN"
    tipo_cambio: Decimal = Decimal("1")
    detalles: List[OCLineaIn]


class OCDesdeCotizacionInput(BaseModel):
    proveedor_id: int
    afecta_stock: bool = False  # default: solo persiste OC, no toca stock


def _generar_folio_oc(db: Session, vendedor: "models.Usuario | None" = None) -> str:
    """Folio OC formato DASIC: OC-YYMM<seq> (consecutivo global por mes).

    Usa advisory_xact_lock para serializar el cómputo del consecutivo y
    evitar colisión entre OCs creadas concurrentemente en el mismo mes.
    Mismo patrón que `ventas._generar_folio`.
    """
    ahora = datetime.utcnow()
    yymm = ahora.strftime("%y%m")
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:k))"),
        {"k": f"folio:OC:{yymm}"},
    )

    consecutivo = (
        db.query(models.OrdenCompra)
        .filter(
            models.OrdenCompra.fecha >= inicio_mes,
            models.OrdenCompra.folio.like("OC-%"),
        )
        .count()
        + 1
    )
    return f"OC-{yymm}{consecutivo:03d}"

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

# Listar Historial (alias en "/" para compat con clientes con caché viejo)
@router.get("/")
@router.get("/historial")
def listar_historial_compras(limit: int = 50, db: Session = Depends(get_db)):
    ordenes = db.query(models.OrdenCompra)\
        .order_by(desc(models.OrdenCompra.fecha))\
        .limit(limit).all()
    
    resultado = []
    for o in ordenes:
        resultado.append({
            "id": o.id,
            "folio": o.folio,
            "fecha": o.fecha,
            "proveedor": o.proveedor.nombre_empresa,
            "total": o.total,
            "moneda": o.moneda or "MXN",
            "estatus": o.estatus,
            "cotizacion_id": o.cotizacion_id,
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
    omitidas = []
    total_estimado = Decimal("0")
    symbol = "US$" if quote.moneda == "USD" else "$"

    for item in quote.detalles:
        producto = item.producto

        # Saltar líneas sin producto del catálogo: servicios, fantasmas, o
        # FK huérfana. No tienen sentido en una OC a proveedor.
        if producto is None:
            tipo = item.tipo_linea or ("servicio" if not item.producto_id else "huerfano")
            omitidas.append({
                "sku": item.sku_libre or "—",
                "descripcion": item.descripcion_libre or "Línea sin producto del catálogo",
                "cantidad": item.cantidad,
                "motivo": f"{tipo}: no se incluye en OC a proveedor",
            })
            continue

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
        "omitidas": omitidas,
        "nota": "Borrador de orden de compra. No genera stock ni cuentas por pagar.",
    }

@router.post("/cotizacion/{quote_id}/orden", dependencies=[Depends(allow_admin_asistente)])
def crear_oc_desde_cotizacion(
    quote_id: int,
    payload: OCDesdeCotizacionInput,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Persiste una OC vinculada a una cotización. Por defecto NO afecta stock
    ni cuentas por pagar (estatus=borrador). Si afecta_stock=True, suma stock
    y registra el cargo al proveedor."""
    quote = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == quote_id).first()
    if not quote:
        raise HTTPException(404, "Cotización no encontrada")
    if quote.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Sólo cotizaciones generan OC")

    proveedor = db.query(models.Proveedor).filter(models.Proveedor.id == payload.proveedor_id).first()
    if not proveedor:
        raise HTTPException(404, "Proveedor no encontrado")

    folio = _generar_folio_oc(db, current_user)
    estatus = "recibido" if payload.afecta_stock else "borrador"

    try:
        oc = models.OrdenCompra(
            proveedor_id=proveedor.id,
            fecha=datetime.utcnow(),
            total=Decimal("0"),
            estatus=estatus,
            folio=folio,
            moneda=quote.moneda,
            tipo_cambio=quote.tipo_cambio,
            cotizacion_id=quote.id,
        )
        db.add(oc)
        db.flush()

        total = Decimal("0")
        for item in quote.detalles:
            if not item.producto_id:
                # Productos fantasma/servicios: no se pueden ordenar al proveedor.
                continue
            producto = item.producto
            if producto is None:
                # FK apuntando a producto borrado (orphan). Saltar sin tronar.
                continue
            costo_unitario = Decimal(producto.costo_compra or item.costo_base_linea or 0)
            origen = (item.moneda_origen_linea or producto.moneda_compra or "MXN").upper()
            if origen != quote.moneda:
                if quote.moneda == "USD":
                    costo_unitario = costo_unitario / Decimal(quote.tipo_cambio or 1)
                else:
                    costo_unitario = costo_unitario * Decimal(quote.tipo_cambio or 1)
            costo_unitario = costo_unitario.quantize(Decimal("0.01"))
            importe = (costo_unitario * item.cantidad).quantize(Decimal("0.01"))
            total += importe

            db.add(models.DetalleCompra(
                orden_compra_id=oc.id,
                producto_id=producto.id,
                cantidad=item.cantidad,
                costo_unitario=costo_unitario,
            ))
            if payload.afecta_stock:
                # ENTRADA auditada con lock pesimista. Antes era mutación directa.
                aplicar_movimiento(
                    db,
                    producto=producto,
                    tipo=TipoMovimientoStock.ENTRADA.value,
                    cantidad=item.cantidad,
                    referencia_tipo="oc",
                    referencia_id=oc.id,
                    motivo=f"OC {oc.folio} con afecta_stock=True (desde cotización {quote.folio})",
                    usuario=current_user,
                )
                producto.costo_compra = costo_unitario  # metadato, no stock

        oc.total = total

        if payload.afecta_stock and total > 0:
            db.add(models.TransaccionProveedor(
                proveedor_id=proveedor.id,
                tipo=models.TipoMovimiento.CARGO,
                monto=total,
                descripcion=f"OC {folio} (desde cotización {quote.folio})",
            ))
            proveedor.saldo_actual += total

        db.commit()
        db.refresh(oc)
        return {
            "id": oc.id,
            "folio": oc.folio,
            "estatus": oc.estatus,
            "moneda": oc.moneda,
            "total": oc.total,
            "cotizacion_id": oc.cotizacion_id,
            "afecta_stock": payload.afecta_stock,
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/registrar-entrada", dependencies=[Depends(allow_admin_asistente)])
def registrar_compra(
    compra: CompraInput,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
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
                # ENTRADA auditada con lock. Antes mutaba prod.stock_actual directo.
                aplicar_movimiento(
                    db,
                    producto=prod,
                    tipo=TipoMovimientoStock.ENTRADA.value,
                    cantidad=item.cantidad,
                    referencia_tipo="compra_directa",
                    referencia_id=nueva_orden.id,
                    motivo=f"compra directa a proveedor #{proveedor.id}",
                    usuario=current_user,
                )
                prod.costo_compra = item.costo_unitario  # metadato, no stock
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
    
    iva = orden.total * _iva_rate()
    gran_total = orden.total + iva

    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_COMPRA).render(
        orden=orden,
        iva=iva,
        gran_total=gran_total,
        iva_pct_label=_iva_pct_label(),
    )


@router.post("/{id}/recibir", dependencies=[Depends(allow_admin_asistente)])
def recibir_oc(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Marca OC como recibida y emite ENTRADA por cada DetalleCompra."""
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == id).first()
    if not orden:
        raise HTTPException(404, "OC no encontrada")
    if orden.estatus == "recibido":
        raise HTTPException(400, "La OC ya fue recibida")
    if orden.estatus not in ("borrador", "enviada", "confirmada"):
        raise HTTPException(400, f"Estatus '{orden.estatus}' no permite recepción")

    detalles = (
        db.query(models.DetalleCompra)
        .filter(models.DetalleCompra.orden_compra_id == id)
        .all()
    )
    if not detalles:
        raise HTTPException(400, "OC sin detalles, nada que recibir")

    procesados = 0
    for det in detalles:
        if not det.producto_id:
            continue
        producto = db.get(models.Producto, det.producto_id)
        if not producto:
            continue
        aplicar_movimiento(
            db,
            producto=producto,
            tipo=TipoMovimientoStock.ENTRADA.value,
            cantidad=int(det.cantidad),
            referencia_tipo="oc",
            referencia_id=orden.id,
            motivo=f"Recepción OC {orden.folio or '#'+str(orden.id)}",
            usuario=current_user,
        )
        procesados += 1

    orden.estatus = "recibido"
    db.commit()
    return {
        "ok": True,
        "folio": orden.folio,
        "productos_ingresados": procesados,
    }


# --- EDITOR DE OC (Fase 5) ---

def _convertir_costo_compra(costo: Decimal, moneda_origen: str, moneda_oc: str, tc: Decimal) -> Decimal:
    """Convierte costo entre monedas usando el TC de la OC. TC = MXN por USD."""
    o = (moneda_origen or "MXN").upper()
    d = (moneda_oc or "MXN").upper()
    if o == d:
        return costo
    if o == "USD" and d == "MXN":
        return costo * (tc or Decimal("1"))
    if o == "MXN" and d == "USD":
        return costo / (tc or Decimal("1"))
    return costo


def _serializar_oc(oc: models.OrdenCompra) -> dict:
    return {
        "id": oc.id,
        "folio": oc.folio,
        "fecha": oc.fecha.isoformat() if oc.fecha else None,
        "estatus": oc.estatus,
        "proveedor_id": oc.proveedor_id,
        "proveedor": oc.proveedor.nombre_empresa if oc.proveedor else None,
        "cotizacion_id": oc.cotizacion_id,
        "moneda": oc.moneda,
        "tipo_cambio": float(oc.tipo_cambio or 1),
        "total": float(oc.total or 0),
        "detalles": [
            {
                "id": d.id,
                "producto_id": d.producto_id,
                "producto": (
                    {"id": d.producto.id, "sku": d.producto.sku_comercial or d.producto.sku, "nombre": d.producto.nombre}
                    if d.producto else None
                ),
                "sku_libre": d.sku_libre,
                "descripcion_libre": d.descripcion_libre,
                "moneda_origen_linea": d.moneda_origen_linea,
                "costo_base_linea": float(d.costo_base_linea or 0),
                "cantidad": d.cantidad,
                "costo_unitario": float(d.costo_unitario or 0),
            }
            for d in oc.detalles
        ],
    }


@router.get("/{id}/json", dependencies=[Depends(allow_admin_asistente)])
def obtener_oc_json(id: int, db: Session = Depends(get_db)):
    oc = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == id).first()
    if not oc:
        raise HTTPException(404, "OC no encontrada")
    return _serializar_oc(oc)


@router.post("/", dependencies=[Depends(allow_admin_asistente)])
def crear_oc_editor(
    payload: OCEditorIn,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Crea OC en estatus 'borrador' desde el editor (sin cotización origen
    obligatoria). Sin impacto en stock ni cuentas por pagar."""
    proveedor = db.query(models.Proveedor).filter(
        models.Proveedor.id == payload.proveedor_id
    ).first()
    if not proveedor:
        raise HTTPException(404, "Proveedor no encontrado")
    if not payload.detalles:
        raise HTTPException(400, "Debe haber al menos un renglón.")

    moneda = (payload.moneda or "MXN").upper()
    tc = Decimal(payload.tipo_cambio or 1)
    folio = _generar_folio_oc(db, current_user)

    try:
        oc = models.OrdenCompra(
            proveedor_id=proveedor.id,
            fecha=datetime.utcnow(),
            total=Decimal("0"),
            estatus="borrador",
            folio=folio,
            moneda=moneda,
            tipo_cambio=tc,
            cotizacion_id=payload.cotizacion_id,
        )
        db.add(oc)
        db.flush()

        total = Decimal("0")
        for det in payload.detalles:
            if det.producto_id:
                producto = db.query(models.Producto).filter(
                    models.Producto.id == det.producto_id
                ).first()
                if not producto:
                    raise HTTPException(404, f"Producto {det.producto_id} no existe")
                origen = (det.moneda_origen or producto.moneda_compra or "MXN").upper()
            else:
                if not (det.descripcion_libre or "").strip():
                    raise HTTPException(400, "Producto fantasma requiere descripción.")
                origen = (det.moneda_origen or "MXN").upper()

            costo_origen = Decimal(det.costo_unitario)
            costo_oc = _convertir_costo_compra(costo_origen, origen, moneda, tc).quantize(Decimal("0.01"))
            importe = (costo_oc * det.cantidad).quantize(Decimal("0.01"))
            total += importe

            db.add(models.DetalleCompra(
                orden_compra_id=oc.id,
                producto_id=det.producto_id,
                sku_libre=det.sku_libre,
                descripcion_libre=det.descripcion_libre,
                moneda_origen_linea=origen,
                costo_base_linea=costo_origen.quantize(Decimal("0.01")),
                cantidad=det.cantidad,
                costo_unitario=costo_oc,
            ))

        oc.total = total.quantize(Decimal("0.01"))
        db.commit()
        db.refresh(oc)
        return _serializar_oc(oc)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.put("/{id}", dependencies=[Depends(allow_admin_asistente)])
def actualizar_oc_editor(
    id: int,
    payload: OCEditorIn,
    db: Session = Depends(get_db),
):
    """Edita una OC en estatus 'borrador'. Si está confirmada/recibida, rechaza."""
    oc = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == id).first()
    if not oc:
        raise HTTPException(404, "OC no encontrada")
    if oc.estatus and oc.estatus.lower() not in ("borrador", "draft"):
        raise HTTPException(400, "Solo se pueden editar OCs en borrador.")

    proveedor = db.query(models.Proveedor).filter(
        models.Proveedor.id == payload.proveedor_id
    ).first()
    if not proveedor:
        raise HTTPException(404, "Proveedor no encontrado")

    moneda = (payload.moneda or "MXN").upper()
    tc = Decimal(payload.tipo_cambio or 1)

    try:
        oc.proveedor_id = proveedor.id
        oc.moneda = moneda
        oc.tipo_cambio = tc
        oc.cotizacion_id = payload.cotizacion_id

        # Reemplaza líneas (cascade del back_populates ya borra)
        db.query(models.DetalleCompra).filter(
            models.DetalleCompra.orden_compra_id == oc.id
        ).delete()

        total = Decimal("0")
        for det in payload.detalles:
            if det.producto_id:
                producto = db.query(models.Producto).filter(
                    models.Producto.id == det.producto_id
                ).first()
                if not producto:
                    raise HTTPException(404, f"Producto {det.producto_id} no existe")
                origen = (det.moneda_origen or producto.moneda_compra or "MXN").upper()
            else:
                if not (det.descripcion_libre or "").strip():
                    raise HTTPException(400, "Producto fantasma requiere descripción.")
                origen = (det.moneda_origen or "MXN").upper()

            costo_origen = Decimal(det.costo_unitario)
            costo_oc = _convertir_costo_compra(costo_origen, origen, moneda, tc).quantize(Decimal("0.01"))
            importe = (costo_oc * det.cantidad).quantize(Decimal("0.01"))
            total += importe

            db.add(models.DetalleCompra(
                orden_compra_id=oc.id,
                producto_id=det.producto_id,
                sku_libre=det.sku_libre,
                descripcion_libre=det.descripcion_libre,
                moneda_origen_linea=origen,
                costo_base_linea=costo_origen.quantize(Decimal("0.01")),
                cantidad=det.cantidad,
                costo_unitario=costo_oc,
            ))

        oc.total = total.quantize(Decimal("0.01"))
        db.commit()
        db.refresh(oc)
        return _serializar_oc(oc)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
