from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import datetime

import database
import models
import schemas
from auth import get_current_user, allow_all_staff, allow_admin_asistente
from models import TipoMovimiento, RolUsuario

router = APIRouter(prefix="/api/clientes", tags=["Clientes y Cobranza"])

# --- 1. LISTAR CLIENTES (CON SALDO) ---
@router.get("/", response_model=List[schemas.ClienteResponse], dependencies=[Depends(allow_all_staff)])
def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """
    Lista todos los clientes. El campo 'saldo_actual' permite ver rápidamente quién debe dinero.
    """
    clientes = db.query(models.Cliente).offset(skip).limit(limit).all()
    return clientes

# --- 2. CREAR CLIENTE ---
@router.post("/", response_model=schemas.ClienteResponse, dependencies=[Depends(allow_all_staff)])
def crear_cliente(
    cliente: schemas.ClienteCreate,
    db: Session = Depends(database.get_db)
):
    """
    Permite registrar un nuevo cliente. Accesible para Vendedores.
    """
    # Verificar si el email o nombre ya existe para evitar duplicados
    if db.query(models.Cliente).filter(models.Cliente.email == cliente.email).first():
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
    db: Session = Depends(database.get_db)
):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# --- 4. VER ESTADO DE CUENTA (HISTORIAL) ---
@router.get("/{cliente_id}/estado-cuenta", response_model=List[schemas.TransaccionResponse], dependencies=[Depends(allow_all_staff)])
def ver_estado_cuenta(
    cliente_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Muestra el historial financiero:
    - CARGO: Ventas (Deuda aumenta)
    - ABONO: Pagos (Deuda disminuye)
    """
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Traemos las transacciones ordenadas por fecha reciente
    movimientos = db.query(models.TransaccionCliente)\
        .filter(models.TransaccionCliente.cliente_id == cliente_id)\
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
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Registra un pago del cliente (ABONO).
    Esto reduce la deuda en 'saldo_actual' y crea un registro histórico.
    """
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto del pago debe ser mayor a 0")

    try:
        # 1. Crear la transacción de ABONO
        nuevo_abono = models.TransaccionCliente(
            cliente_id=cliente.id,
            tipo=TipoMovimiento.ABONO,
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