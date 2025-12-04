from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from .. import database, models, schemas, auth

router = APIRouter()

# --- CRUD Básico ---
@router.get("/")
def listar_clientes(db: Session = Depends(database.get_db)):
    return db.query(models.Cliente).all()

@router.post("/")
def crear_cliente(data: schemas.ClienteCreate, db: Session = Depends(database.get_db)):
    cliente = models.Cliente(
        nombre=data.nombre,
        compania=data.compania,
        email=data.email,
        telefono=data.telefono,
        direccion=data.direccion,
        rfc=data.rfc,
        dias_credito=data.dias_credito
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

# --- MÓDULO FINANCIERO (Estado de Cuenta) ---

@router.get("/{cliente_id}/estado-cuenta")
def ver_estado_cuenta(cliente_id: int, db: Session = Depends(database.get_db)):
    """Obtiene historial de movimientos y saldo al día"""
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente: raise HTTPException(status_code=404, detail="Cliente no existe")
    
    # Ordenar movimientos del más reciente al más antiguo
    movimientos = db.query(models.MovimientoCuenta)\
        .filter(models.MovimientoCuenta.cliente_id == cliente_id)\
        .order_by(models.MovimientoCuenta.fecha.desc()).all()
        
    return {
        "cliente": cliente.nombre,
        "limite_credito_dias": cliente.dias_credito,
        "saldo_pendiente": cliente.saldo_actual,
        "movimientos": movimientos
    }

@router.post("/{cliente_id}/registrar-pago")
def registrar_pago(cliente_id: int, monto: float, referencia: str, db: Session = Depends(database.get_db)):
    """Registra un ABONO (El cliente paga)"""
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    
    # 1. Crear Movimiento
    abono = models.MovimientoCuenta(
        cliente_id=cliente_id,
        tipo="ABONO",
        monto=monto,
        referencia=referencia,
        descripcion="Pago recibido de cliente",
        fecha=datetime.now()
    )
    
    # 2. Actualizar Saldo Global
    cliente.saldo_actual -= monto
    
    db.add(abono)
    db.commit()
    return {"mensaje": "Pago registrado", "nuevo_saldo": cliente.saldo_actual}

@router.post("/convertir-nota-remision/{cotizacion_id}")
def convertir_a_deuda(cotizacion_id: int, db: Session = Depends(database.get_db)):
    """
    Convierte una Cotización 'Aceptada' en DEUDA real (CARGO).
    Esto sucede cuando entregas la mercancía (Nota de Remisión).
    """
    cot = db.query(models.Cotizacion).filter(models.Cotizacion.id == cotizacion_id).first()
    if not cot: raise HTTPException(404, "Cotización no encontrada")
    
    if cot.estado == "Entregada":
        raise HTTPException(400, "Esta cotización ya fue procesada como deuda")
    
    # 1. Crear Cargo
    cargo = models.MovimientoCuenta(
        cliente_id=cot.cliente_id,
        tipo="CARGO",
        monto=cot.total_neto,
        referencia=cot.folio,
        descripcion=f"Nota de Remisión / Entrega {cot.folio}",
        fecha=datetime.now()
    )
    
    # 2. Actualizar Saldo Cliente
    cot.cliente.saldo_actual += cot.total_neto
    
    # 3. Actualizar Estatus Cotización
    cot.estado = "Entregada" # O "Nota Generada"
    
    db.add(cargo)
    db.commit()
    return {"mensaje": "Deuda registrada exitosamente"}