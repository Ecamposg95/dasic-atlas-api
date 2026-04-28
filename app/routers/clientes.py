from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import datetime
from fastapi.responses import HTMLResponse
from jinja2 import Environment, BaseLoader

from app import models
from app import schemas
from app.db import get_db
from app.security import allow_admin_asistente, allow_all_staff, get_current_user

router = APIRouter(prefix="/api/clientes", tags=["Clientes y Cobranza"])

# --- 1. LISTAR CLIENTES (CON SALDO) ---
@router.get("/", response_model=List[schemas.ClienteResponse], dependencies=[Depends(allow_all_staff)])
def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista todos los clientes. El campo 'saldo_actual' permite ver rápidamente quién debe dinero.
    """
    clientes = (
        db.query(models.Cliente)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return clientes

# --- 2. CREAR CLIENTE ---
@router.post("/", response_model=schemas.ClienteResponse, dependencies=[Depends(allow_all_staff)])
def crear_cliente(
    cliente: schemas.ClienteCreate,
    db: Session = Depends(get_db)
):
    """
    Permite registrar un nuevo cliente. Accesible para Vendedores.
    """
    # Verificar si el email o nombre ya existe para evitar duplicados
    if (
        db.query(models.Cliente)
        .filter(
            models.Cliente.email == cliente.email,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Ya existe un cliente con este email")

    nuevo_cliente = models.Cliente(**cliente.model_dump())
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente

# --- 3. OBTENER DETALLE CLIENTE ---
@router.get("/{cliente_id}", response_model=schemas.ClienteResponse, dependencies=[Depends(allow_all_staff)])
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
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
