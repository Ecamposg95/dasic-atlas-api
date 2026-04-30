from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

from app import models
from app.db import get_db
from app.security import allow_admin, allow_admin_asistente, allow_all_staff, get_current_user

router = APIRouter(prefix="/api/gastos", tags=["Gastos Operativos"])

# --- SCHEMAS ---
class GastoCreate(BaseModel):
    categoria: str = Field(..., min_length=1, max_length=80)
    descripcion: Optional[str] = None
    monto: Decimal = Field(..., gt=0)
    moneda: str = Field(default="MXN", min_length=3, max_length=3)

class GastoUpdate(BaseModel):
    categoria: Optional[str] = Field(None, min_length=1, max_length=80)
    descripcion: Optional[str] = None
    monto: Optional[Decimal] = Field(None, gt=0)
    moneda: Optional[str] = Field(None, min_length=3, max_length=3)

class GastoResponse(BaseModel):
    id: int
    categoria: str
    descripcion: Optional[str] = None
    monto: Decimal
    moneda: str = "MXN"
    fecha: datetime
    usuario: Optional[str] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- ENDPOINTS ---

@router.get("/", response_model=List[GastoResponse], dependencies=[Depends(allow_admin_asistente)])
def listar_gastos(limit: int = 200, db: Session = Depends(get_db)):
    gastos = db.query(models.Gasto).order_by(desc(models.Gasto.fecha)).limit(limit).all()
    out = []
    for g in gastos:
        nombre_user = g.usuario.nombre if g.usuario else "Sistema"
        out.append(GastoResponse(
            id=g.id,
            categoria=g.categoria,
            descripcion=g.descripcion,
            monto=g.monto,
            moneda=g.moneda or "MXN",
            fecha=g.fecha,
            usuario=nombre_user,
            usuario_id=g.usuario_id,
        ))
    return out


@router.post("/", response_model=GastoResponse, dependencies=[Depends(allow_admin_asistente)])
def registrar_gasto(
    gasto: GastoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    nuevo = models.Gasto(
        categoria=gasto.categoria.strip(),
        descripcion=(gasto.descripcion or "").strip() or None,
        monto=gasto.monto,
        moneda=(gasto.moneda or "MXN").upper(),
        usuario_id=current_user.id,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return GastoResponse(
        id=nuevo.id, categoria=nuevo.categoria, descripcion=nuevo.descripcion,
        monto=nuevo.monto, moneda=nuevo.moneda, fecha=nuevo.fecha,
        usuario=current_user.nombre, usuario_id=current_user.id,
    )


@router.put("/{id}", response_model=GastoResponse, dependencies=[Depends(allow_admin_asistente)])
def editar_gasto(id: int, payload: GastoUpdate, db: Session = Depends(get_db)):
    g = db.query(models.Gasto).filter(models.Gasto.id == id).first()
    if not g:
        raise HTTPException(404, "Gasto no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "moneda" in data and data["moneda"]:
        data["moneda"] = data["moneda"].upper()
    for k, v in data.items():
        setattr(g, k, v)
    db.commit()
    db.refresh(g)
    return GastoResponse(
        id=g.id, categoria=g.categoria, descripcion=g.descripcion,
        monto=g.monto, moneda=g.moneda or "MXN", fecha=g.fecha,
        usuario=g.usuario.nombre if g.usuario else "Sistema",
        usuario_id=g.usuario_id,
    )


@router.delete("/{id}", dependencies=[Depends(allow_admin)])
def eliminar_gasto(id: int, db: Session = Depends(get_db)):
    g = db.query(models.Gasto).filter(models.Gasto.id == id).first()
    if not g:
        raise HTTPException(404, "Gasto no encontrado")
    db.delete(g)
    db.commit()
    return {"mensaje": "Eliminado"}
