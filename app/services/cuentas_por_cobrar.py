"""Servicio CRM: cuentas por cobrar (cargos vinculados a ventas + pagos).

Funciones expuestas:
  - crear_cargo_por_venta(db, orden_venta, monto, ...)
  - aplicar_pago(db, cliente, monto, orden_venta_ids=None)
  - recalcular_estatus_pago(db, cargo)
  - marcar_vencidos(db, org_id=None)   # uso de cron / job diario
  - listar_vencimientos(db, dias=7)

Reglas:
  - Estatus: pendiente | parcial | pagado | vencido
  - vencido se calcula con fecha_vencimiento < hoy y estatus != pagado
  - Distribución de pagos: FIFO sobre cargos abiertos del cliente, o explícita
    si se pasan IDs.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app import models
from app.models.enums import TipoMovimiento


def _hoy() -> date:
    return datetime.utcnow().date()


def crear_cargo_por_venta(
    db: Session,
    *,
    orden_venta: "models.OrdenVenta",
    monto: Decimal,
    descripcion: Optional[str] = None,
) -> "models.TransaccionCliente":
    """Crea un CARGO en cuentas por cobrar ligado a una venta.

    Calcula fecha_vencimiento a partir de cliente.dias_credito. Si dias_credito
    es 0, queda con vencimiento = hoy (cargo a contado).
    """
    cliente = orden_venta.cliente
    dias = int(cliente.dias_credito or 0)
    fecha_venc = _hoy() + timedelta(days=dias)

    tx = models.TransaccionCliente(
        cliente_id=cliente.id,
        tipo=TipoMovimiento.CARGO,
        monto=Decimal(monto),
        descripcion=descripcion or f"Venta {orden_venta.folio}",
        referencia_id=orden_venta.id,  # compat
        orden_venta_id=orden_venta.id,
        fecha_vencimiento=fecha_venc,
        estatus_pago="pendiente",
        monto_pagado=Decimal("0"),
    )
    db.add(tx)
    cliente.saldo_actual = (cliente.saldo_actual or Decimal("0")) + Decimal(monto)
    return tx


def recalcular_estatus_pago(db: Session, cargo: "models.TransaccionCliente") -> str:
    """Recalcula estatus_pago en base a monto_pagado / monto y vencimiento."""
    if cargo.tipo != TipoMovimiento.CARGO:
        return cargo.estatus_pago or "pendiente"
    monto = Decimal(cargo.monto or 0)
    pagado = Decimal(cargo.monto_pagado or 0)
    if pagado >= monto:
        cargo.estatus_pago = "pagado"
    elif pagado > 0:
        cargo.estatus_pago = "parcial"
    else:
        cargo.estatus_pago = "pendiente"

    # Sobre-escribe a 'vencido' si aplica (solo si no está pagado)
    if cargo.estatus_pago != "pagado":
        if cargo.fecha_vencimiento and cargo.fecha_vencimiento < _hoy():
            cargo.estatus_pago = "vencido"
    return cargo.estatus_pago


def _cargos_abiertos(db: Session, cliente_id: int) -> list["models.TransaccionCliente"]:
    """Cargos con saldo > 0, ordenados por fecha de vencimiento (FIFO real)."""
    rows = (
        db.query(models.TransaccionCliente)
        .filter(models.TransaccionCliente.cliente_id == cliente_id)
        .filter(models.TransaccionCliente.tipo == TipoMovimiento.CARGO)
        .filter(models.TransaccionCliente.estatus_pago != "pagado")
        .order_by(
            models.TransaccionCliente.fecha_vencimiento.asc().nullsfirst(),
            models.TransaccionCliente.fecha.asc(),
        )
        .all()
    )
    abiertos = []
    for r in rows:
        saldo = Decimal(r.monto or 0) - Decimal(r.monto_pagado or 0)
        if saldo > 0:
            abiertos.append(r)
    return abiertos


def aplicar_pago(
    db: Session,
    *,
    cliente: "models.Cliente",
    monto: Decimal,
    descripcion: Optional[str] = None,
    orden_venta_ids: Optional[Iterable[int]] = None,
) -> dict:
    """Aplica un pago al cliente, distribuyendo sobre cargos abiertos.

    Si `orden_venta_ids` se proporciona, distribuye en ese orden. Si no, FIFO.
    Si sobra (pago en exceso), registra un ABONO sobrante sin cargo asociado.

    Crea siempre 1 fila ABONO global (asentamiento) y actualiza monto_pagado en
    los CARGOs afectados.
    """
    monto_total = Decimal(monto)
    if monto_total <= 0:
        raise ValueError("Monto debe ser > 0")

    if orden_venta_ids:
        explicit = list(orden_venta_ids)
        rows_q = (
            db.query(models.TransaccionCliente)
            .filter(models.TransaccionCliente.cliente_id == cliente.id)
            .filter(models.TransaccionCliente.tipo == TipoMovimiento.CARGO)
            .filter(models.TransaccionCliente.orden_venta_id.in_(explicit))
            .all()
        )
        # Mantén orden de IDs entrantes
        rows_by_ov = {r.orden_venta_id: r for r in rows_q}
        cola = [rows_by_ov[ov] for ov in explicit if ov in rows_by_ov]
    else:
        cola = _cargos_abiertos(db, cliente.id)

    aplicado = Decimal("0")
    detalle = []
    restante = monto_total
    for cargo in cola:
        if restante <= 0:
            break
        saldo = Decimal(cargo.monto or 0) - Decimal(cargo.monto_pagado or 0)
        if saldo <= 0:
            continue
        toma = min(restante, saldo)
        cargo.monto_pagado = (Decimal(cargo.monto_pagado or 0) + toma).quantize(Decimal("0.01"))
        recalcular_estatus_pago(db, cargo)
        aplicado += toma
        restante -= toma
        detalle.append({
            "transaccion_cliente_id": cargo.id,
            "orden_venta_id": cargo.orden_venta_id,
            "aplicado": float(toma),
            "estatus_pago": cargo.estatus_pago,
        })

    abono = models.TransaccionCliente(
        cliente_id=cliente.id,
        tipo=TipoMovimiento.ABONO,
        monto=monto_total,
        descripcion=descripcion or "Pago cliente",
        estatus_pago="pagado",
        monto_pagado=monto_total,
    )
    db.add(abono)
    cliente.saldo_actual = (cliente.saldo_actual or Decimal("0")) - monto_total
    return {
        "pago_id": None,  # se llena tras flush si el caller lo necesita
        "monto_aplicado": float(aplicado),
        "monto_excedente": float(max(restante, Decimal("0"))),
        "detalle": detalle,
    }


def marcar_vencidos(db: Session) -> int:
    """Job idempotente: marca como 'vencido' los CARGOs con fecha_vencimiento <
    hoy y estatus distinto a 'pagado' / 'vencido'."""
    hoy = _hoy()
    rows = (
        db.query(models.TransaccionCliente)
        .filter(models.TransaccionCliente.tipo == TipoMovimiento.CARGO)
        .filter(models.TransaccionCliente.fecha_vencimiento.is_not(None))
        .filter(models.TransaccionCliente.fecha_vencimiento < hoy)
        .filter(models.TransaccionCliente.estatus_pago.notin_(["pagado", "vencido"]))
        .all()
    )
    n = 0
    for r in rows:
        r.estatus_pago = "vencido"
        n += 1
    if n:
        db.commit()
    return n


def listar_vencimientos(db: Session, *, dias: int = 7) -> list[dict]:
    """Lista CARGOs por vencer (en N días) o ya vencidos, agrupados por cliente."""
    hoy = _hoy()
    limite = hoy + timedelta(days=dias)
    rows = (
        db.query(models.TransaccionCliente)
        .filter(models.TransaccionCliente.tipo == TipoMovimiento.CARGO)
        .filter(models.TransaccionCliente.estatus_pago != "pagado")
        .filter(
            (models.TransaccionCliente.fecha_vencimiento.is_(None))
            | (models.TransaccionCliente.fecha_vencimiento <= limite)
        )
        .order_by(models.TransaccionCliente.fecha_vencimiento.asc().nullslast())
        .all()
    )
    out = []
    for r in rows:
        saldo = float(Decimal(r.monto or 0) - Decimal(r.monto_pagado or 0))
        out.append({
            "id": r.id,
            "cliente_id": r.cliente_id,
            "cliente": r.cliente.nombre_empresa if r.cliente else None,
            "orden_venta_id": r.orden_venta_id,
            "fecha": r.fecha.isoformat() if r.fecha else None,
            "fecha_vencimiento": r.fecha_vencimiento.isoformat() if r.fecha_vencimiento else None,
            "monto": float(r.monto or 0),
            "monto_pagado": float(r.monto_pagado or 0),
            "saldo_pendiente": saldo,
            "estatus_pago": r.estatus_pago,
            "dias_atraso": (hoy - r.fecha_vencimiento).days if r.fecha_vencimiento and r.fecha_vencimiento < hoy else 0,
        })
    return out
