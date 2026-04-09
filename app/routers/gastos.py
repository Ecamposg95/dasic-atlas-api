from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from typing import List

from app import models
from app.db import get_db
from app.security import allow_admin, get_current_user

router = APIRouter(prefix="/api/gastos", tags=["Gastos Operativos"])

# --- SCHEMAS ---
class GastoCreate(BaseModel):
    categoria: str
    descripcion: str
    monto: Decimal

class GastoResponse(BaseModel):
    id: int
    categoria: str
    descripcion: str
    monto: Decimal
    fecha: datetime
    usuario: str # Nombre del que registró
    
    class Config:
        from_attributes = True

# --- ENDPOINTS ---

@router.get("/", response_model=List[GastoResponse])
def listar_gastos(limit: int = 100, db: Session = Depends(get_db)):
    gastos = db.query(models.Gasto).order_by(desc(models.Gasto.fecha)).limit(limit).all()
    
    # Mapeo manual simple para incluir nombre de usuario
    resultado = []
    for g in gastos:
        # Buscamos el nombre del usuario, si no existe ponemos "Desconocido"
        user = db.query(models.Usuario).filter(models.Usuario.id == g.usuario_id).first()
        nombre_user = user.nombre if user else "Sistema"
        
        resultado.append(GastoResponse(
            id=g.id, 
            categoria=g.categoria, 
            descripcion=g.descripcion, 
            monto=g.monto, 
            fecha=g.fecha,
            usuario=nombre_user
        ))
    return resultado

@router.post("/", dependencies=[Depends(allow_admin)])
def registrar_gasto(
    gasto: GastoCreate, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    if gasto.monto <= 0: raise HTTPException(400, "El monto debe ser positivo")
    
    nuevo_gasto = models.Gasto(
        categoria=gasto.categoria,
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        usuario_id=current_user.id
    )
    db.add(nuevo_gasto)
    db.commit()
    return {"mensaje": "Gasto registrado"}

@router.delete("/{id}", dependencies=[Depends(allow_admin)])
def eliminar_gasto(id: int, db: Session = Depends(get_db)):
    g = db.query(models.Gasto).filter(models.Gasto.id == id).first()
    if not g: raise HTTPException(404, "Gasto no encontrado")
    db.delete(g)
    db.commit()
    return {"mensaje": "Eliminado"}
