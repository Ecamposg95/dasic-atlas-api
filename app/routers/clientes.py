from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi.responses import HTMLResponse
from jinja2 import Environment, BaseLoader

from app import models
from app import schemas
from app.db import get_db
from app.security import allow_admin_asistente, allow_all_staff, get_current_user
from app.security.permissions import is_owner_scoped, require

router = APIRouter(prefix="/api/clientes", tags=["Clientes y Cobranza"])

# --- 1. LISTAR CLIENTES (CON SALDO) ---
@router.get("/", response_model=List[schemas.ClienteResponse], dependencies=[Depends(allow_all_staff)])
def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Lista clientes. VENTAS solo ve los que ellos crearon."""
    query = db.query(models.Cliente)
    if is_owner_scoped(current_user, "read", "cliente"):
        query = query.filter(models.Cliente.creado_por_id == current_user.id)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            models.Cliente.nombre_empresa.ilike(like),
            models.Cliente.contacto_nombre.ilike(like),
            models.Cliente.email.ilike(like),
        ))
    return (
        query.order_by(models.Cliente.nombre_empresa.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

# --- 2. CREAR CLIENTE ---
@router.post("/", response_model=schemas.ClienteResponse, dependencies=[Depends(allow_all_staff)])
def crear_cliente(
    cliente: schemas.ClienteCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Registra un nuevo cliente. Accesible para todo el staff."""
    require(current_user, "create", "cliente")
    if not cliente.nombre_empresa or not cliente.nombre_empresa.strip():
        raise HTTPException(status_code=400, detail="nombre_empresa es requerido")
    if cliente.email:
        existing = (
            db.query(models.Cliente)
            .filter(models.Cliente.email == cliente.email)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un cliente con este email")

    nuevo_cliente = models.Cliente(**cliente.model_dump(), creado_por_id=current_user.id)
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente


# --- 2.5 EDITAR CLIENTE ---
@router.put("/{cliente_id}", response_model=schemas.ClienteResponse, dependencies=[Depends(allow_all_staff)])
def editar_cliente(
    cliente_id: int,
    payload: schemas.ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Edita un cliente. VENTAS sólo puede editar los que él creó."""
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if is_owner_scoped(current_user, "write", "cliente") and cliente.creado_por_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes editar clientes que tú creaste")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] and data["email"] != cliente.email:
        otro = (
            db.query(models.Cliente)
            .filter(models.Cliente.email == data["email"], models.Cliente.id != cliente_id)
            .first()
        )
        if otro:
            raise HTTPException(status_code=400, detail="Ya existe otro cliente con este email")

    for k, v in data.items():
        setattr(cliente, k, v)
    db.commit()
    db.refresh(cliente)
    return cliente


# --- 2.6 ELIMINAR CLIENTE (admin) ---
@router.delete("/{cliente_id}", dependencies=[Depends(allow_admin_asistente)])
def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Elimina cliente. Bloquea si tiene cotizaciones/ventas o saldo > 0."""
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if cliente.saldo_actual and float(cliente.saldo_actual) != 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cliente tiene saldo {cliente.saldo_actual}. Liquida antes de eliminar.",
        )

    en_uso = (
        db.query(models.OrdenVenta)
        .filter(models.OrdenVenta.cliente_id == cliente_id)
        .first()
    )
    if en_uso:
        raise HTTPException(
            status_code=409,
            detail="Cliente referenciado en cotizaciones/ventas. No se puede eliminar.",
        )

    db.delete(cliente)
    db.commit()
    return {"mensaje": "Cliente eliminado", "id": cliente_id}

# --- 3. OBTENER DETALLE CLIENTE ---
@router.get("/{cliente_id}", response_model=schemas.ClienteResponse, dependencies=[Depends(allow_all_staff)])
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    cliente = (
        db.query(models.Cliente)
        .filter(
            models.Cliente.id == cliente_id,
        )
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if is_owner_scoped(current_user, "read", "cliente") and cliente.creado_por_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# --- 4. VER ESTADO DE CUENTA (HISTORIAL) ---
@router.get("/{cliente_id}/estado-cuenta", response_model=List[schemas.TransaccionResponse], dependencies=[Depends(allow_all_staff)])
def ver_estado_cuenta(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Muestra el historial financiero:
    - CARGO: Ventas (Deuda aumenta)
    - ABONO: Pagos (Deuda disminuye)
    """
    cliente = (
        db.query(models.Cliente)
        .filter(
            models.Cliente.id == cliente_id,
        )
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Traemos las transacciones ordenadas por fecha reciente
    movimientos = db.query(models.TransaccionCliente)\
        .filter(
            models.TransaccionCliente.cliente_id == cliente_id,
        )\
        .order_by(models.TransaccionCliente.fecha.desc())\
        .all()

    return movimientos

# --- 5. REGISTRAR PAGO (SOLO ADMIN/ASISTENTE) ---
@router.post("/{cliente_id}/registrar-pago", dependencies=[Depends(allow_admin_asistente)])
def registrar_pago_cliente(
    cliente_id: int,
    monto: Decimal,
    descripcion: str = "Abono a cuenta",
    nota_id: int = None, # Opcional: Si el pago es específico para una nota
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Registra un pago del cliente (ABONO).
    Esto reduce la deuda en 'saldo_actual' y crea un registro histórico.
    """
    cliente = (
        db.query(models.Cliente)
        .filter(
            models.Cliente.id == cliente_id,
        )
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto del pago debe ser mayor a 0")

    try:
        # 1. Crear la transacción de ABONO
        nuevo_abono = models.TransaccionCliente(
            cliente_id=cliente.id,
            tipo=models.TipoMovimiento.ABONO,
            monto=monto,
            descripcion=f"PAGO RECIBIDO: {descripcion} (Reg. por {current_user.nombre})",
            referencia_id=nota_id # Puede ser null
        )
        db.add(nuevo_abono)

        # 2. Actualizar el saldo del cliente
        # Nota: Al ser abono, RESTAMOS al saldo (Saldo positivo = Deuda)
        cliente.saldo_actual -= monto

        db.commit()

        return {
            "mensaje": "Pago registrado exitosamente",
            "nuevo_saldo": cliente.saldo_actual,
            "transaccion_id": nuevo_abono.id
        }

    except Exception as e:
        db.rollback()
        raise e


# --- 4. RECONCILIACIÓN DE SALDO ---
@router.get("/{cliente_id}/saldo-reconciliacion", dependencies=[Depends(allow_admin_asistente)])
def saldo_reconciliacion(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Compara saldo_actual contra la suma neta de TransaccionCliente.

    Útil para detectar drift por borrado manual de filas, rollback parcial
    de transacciones, o cualquier escenario donde el campo cacheado en
    Cliente quede desincronizado con la fuente de verdad (transacciones).
    """
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    saldo_cacheado = Decimal(cliente.saldo_actual or 0)
    saldo_calculado = Decimal("0")
    for t in cliente.transacciones:
        if t.tipo == models.TipoMovimiento.CARGO:
            saldo_calculado += Decimal(t.monto or 0)
        elif t.tipo == models.TipoMovimiento.ABONO:
            saldo_calculado -= Decimal(t.monto or 0)

    diferencia = (saldo_cacheado - saldo_calculado).quantize(Decimal("0.01"))
    return {
        "cliente_id": cliente.id,
        "nombre_empresa": cliente.nombre_empresa,
        "saldo_cacheado": saldo_cacheado,
        "saldo_calculado": saldo_calculado.quantize(Decimal("0.01")),
        "diferencia": diferencia,
        "en_sincronia": diferencia == 0,
        "n_transacciones": len(cliente.transacciones),
    }


@router.post("/{cliente_id}/saldo-reconciliacion/aplicar", dependencies=[Depends(allow_admin_asistente)])
def aplicar_reconciliacion(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Reescribe saldo_actual con el saldo calculado desde transacciones.

    Acción destructiva; solo admin/gerente. Usar después de revisar el
    reporte de /saldo-reconciliacion y aceptar el drift detectado.
    """
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    saldo_calculado = Decimal("0")
    for t in cliente.transacciones:
        if t.tipo == models.TipoMovimiento.CARGO:
            saldo_calculado += Decimal(t.monto or 0)
        elif t.tipo == models.TipoMovimiento.ABONO:
            saldo_calculado -= Decimal(t.monto or 0)

    saldo_anterior = cliente.saldo_actual
    cliente.saldo_actual = saldo_calculado.quantize(Decimal("0.01"))
    db.commit()
    return {
        "cliente_id": cliente.id,
        "saldo_anterior": saldo_anterior,
        "saldo_nuevo": cliente.saldo_actual,
    }


    # Plantilla HTML para Estado de Cuenta
PDF_TEMPLATE_EDO_CTA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Estado de Cuenta - {{ cliente.nombre_empresa }}</title>
    <style>
        body { font-family: Arial, sans-serif; color: #333; padding: 30px; font-size: 12px; }
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
        .title { font-size: 20px; font-weight: bold; color: #1e3a8a; text-transform: uppercase; }
        .client-box { background: #f8fafc; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background: #1e3a8a; color: white; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .cargo { color: #dc2626; } /* Rojo */
        .abono { color: #16a34a; } /* Verde */
        .saldo-final { margin-top: 20px; text-align: right; font-size: 16px; font-weight: bold; padding: 10px; background: #eff6ff; }
    </style>
</head>
<body onload="window.print()">
    <div class="header">
        <div>
            <div class="title">DASIC ERP</div>
            <div>Soluciones Industriales S.A. de C.V.</div>
        </div>
        <div style="text-align: right;">
            <div class="title">ESTADO DE CUENTA</div>
            <div>Fecha Emisión: {{ fecha_hoy }}</div>
        </div>
    </div>

    <div class="client-box">
        <strong>Cliente:</strong> {{ cliente.nombre_empresa }}<br>
        <strong>Atención:</strong> {{ cliente.contacto_nombre }}<br>
        <strong>RFC:</strong> {{ cliente.rfc_tax_id or "N/A" }} | <strong>Tel:</strong> {{ cliente.telefono }}
    </div>

    <table>
        <thead>
            <tr>
                <th width="15%">Fecha</th>
                <th width="40%">Concepto / Referencia</th>
                <th width="15%" class="text-right">Cargos (Ventas)</th>
                <th width="15%" class="text-right">Abonos (Pagos)</th>
                <th width="15%" class="text-right">Saldo Acumulado</th>
            </tr>
        </thead>
        <tbody>
            {# Lógica para calcular saldo acumulado línea por línea #}
            {% set ns = namespace(saldo=0) %}
            
            {% for m in movimientos %}
                {% if m.tipo.value == 'cargo' %}
                    {% set ns.saldo = ns.saldo + m.monto %}
                {% else %}
                    {% set ns.saldo = ns.saldo - m.monto %}
                {% endif %}
            <tr>
                <td>{{ m.fecha.strftime('%d/%m/%Y') }}</td>
                <td>{{ m.descripcion }}</td>
                <td class="text-right cargo">
                    {% if m.tipo.value == 'cargo' %}${{ "{:,.2f}".format(m.monto) }}{% else %}-{% endif %}
                </td>
                <td class="text-right abono">
                    {% if m.tipo.value == 'abono' %}${{ "{:,.2f}".format(m.monto) }}{% else %}-{% endif %}
                </td>
                <td class="text-right font-bold">${{ "{:,.2f}".format(ns.saldo) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="saldo-final">
        Saldo Total Pendiente: ${{ "{:,.2f}".format(cliente.saldo_actual) }}
    </div>
</body>
</html>
"""

@router.get("/{cliente_id}/pdf-estado-cuenta", response_class=HTMLResponse)
def generar_pdf_estado_cuenta(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    cliente = (
        db.query(models.Cliente)
        .filter(
            models.Cliente.id == cliente_id,
        )
        .first()
    )
    if not cliente: raise HTTPException(404, "Cliente no encontrado")

    # Traemos movimientos antiguos primero para calcular el saldo histórico correctamente
    movimientos = db.query(models.TransaccionCliente)\
        .filter(
            models.TransaccionCliente.cliente_id == cliente_id,
        )\
        .order_by(models.TransaccionCliente.fecha.asc())\
        .all()

    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_EDO_CTA).render(
        cliente=cliente,
        movimientos=movimientos,
        fecha_hoy=datetime.now().strftime('%d/%m/%Y %H:%M')
    )


# --- CRM CxC: cargos abiertos + pago distribuido (Fase 6) ---

@router.get("/{cliente_id}/cuentas-por-cobrar", dependencies=[Depends(allow_all_staff)])
def cuentas_por_cobrar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Lista los cargos (CxC) del cliente con estatus_pago + saldo pendiente."""
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")
    rows = (
        db.query(models.TransaccionCliente)
        .filter(models.TransaccionCliente.cliente_id == cliente_id)
        .filter(models.TransaccionCliente.tipo == models.TipoMovimiento.CARGO)
        .order_by(models.TransaccionCliente.fecha.desc())
        .all()
    )
    from decimal import Decimal
    from datetime import datetime as _dt
    hoy = _dt.utcnow().date()

    def _saldo(r):
        return float(Decimal(r.monto or 0) - Decimal(r.monto_pagado or 0))

    return {
        "cliente": {
            "id": cliente.id,
            "nombre_empresa": cliente.nombre_empresa,
            "saldo_actual": float(cliente.saldo_actual or 0),
            "limite_credito": float(cliente.limite_credito or 0),
            "dias_credito": int(cliente.dias_credito or 0),
            "moneda_credito": cliente.moneda_credito,
        },
        "cargos": [
            {
                "id": r.id,
                "orden_venta_id": r.orden_venta_id,
                "folio": (r.orden_venta.folio if r.orden_venta else None),
                "fecha": r.fecha.isoformat() if r.fecha else None,
                "fecha_vencimiento": r.fecha_vencimiento.isoformat() if r.fecha_vencimiento else None,
                "descripcion": r.descripcion,
                "monto": float(r.monto or 0),
                "monto_pagado": float(r.monto_pagado or 0),
                "saldo_pendiente": _saldo(r),
                "estatus_pago": r.estatus_pago,
                "dias_atraso": (hoy - r.fecha_vencimiento).days if r.fecha_vencimiento and r.fecha_vencimiento < hoy and (r.estatus_pago != "pagado") else 0,
            }
            for r in rows
        ],
    }


@router.post("/{cliente_id}/pago-distribuido", dependencies=[Depends(allow_admin_asistente)])
def registrar_pago_distribuido(
    cliente_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    """Registra un pago aplicándolo a CxC (FIFO por defecto o explícito).

    Body:
      {
        "monto": 5000.00,
        "descripcion": "Transferencia OXXO 12345" (opcional),
        "orden_venta_ids": [12, 15]  (opcional; sin esto = FIFO)
      }
    """
    from app.services.cuentas_por_cobrar import aplicar_pago
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")
    try:
        from decimal import Decimal
        monto = Decimal(str(payload.get("monto", 0)))
        result = aplicar_pago(
            db,
            cliente=cliente,
            monto=monto,
            descripcion=payload.get("descripcion"),
            orden_venta_ids=payload.get("orden_venta_ids"),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    db.commit()
    return {"ok": True, **result}
