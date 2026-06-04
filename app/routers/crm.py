"""Router CRM Kanban: Pipeline / Stage / Deal.

Todos los endpoints requieren al menos rol VENTAS (allow_all_staff).
organization_id se resuelve desde el modelo Usuario activo (campo
organization_id, que el seed garantiza en el usuario inicial). Para
compatibilidad con el sistema mono-tenant actual, los endpoints filtran
por organization_id cuando está disponible en el usuario; si es None,
devuelven todos los registros de la tabla (comportamiento idéntico a
routers como servicios.py).
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.models.crm import Deal, Pipeline, PipelineStage
from app.schemas.crm import DealCreate, DealMove, DealOut, DealUpdate, PipelineOut, StageOut
from app.security import allow_all_staff, get_current_user

router = APIRouter(prefix="/api/crm", tags=["CRM"])


def _org_id(user: models.Usuario) -> str | None:
    """Devuelve el organization_id del usuario si existe."""
    return getattr(user, "organization_id", None)


def _pipeline_or_404(
    db: Session, pipeline_id: int, org_id: str | None
) -> Pipeline:
    q = db.query(Pipeline).filter(Pipeline.id == pipeline_id)
    if org_id:
        q = q.filter(Pipeline.organization_id == org_id)
    p = q.first()
    if not p:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    return p


def _deal_or_404(
    db: Session, deal_id: int, org_id: str | None
) -> Deal:
    q = db.query(Deal).filter(Deal.id == deal_id)
    if org_id:
        q = q.filter(Deal.organization_id == org_id)
    d = q.first()
    if not d:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    return d


# ---------------------------------------------------------------------------
# GET /pipelines
# ---------------------------------------------------------------------------
@router.get("/pipelines", response_model=list[PipelineOut], dependencies=[Depends(allow_all_staff)])
def listar_pipelines(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    q = db.query(Pipeline)
    org_id = _org_id(current_user)
    if org_id:
        q = q.filter(Pipeline.organization_id == org_id)
    return q.order_by(Pipeline.es_default.desc(), Pipeline.nombre).all()


# ---------------------------------------------------------------------------
# GET /pipelines/{pipeline_id}/board
# ---------------------------------------------------------------------------
@router.get("/pipelines/{pipeline_id}/board", dependencies=[Depends(allow_all_staff)])
def get_board(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict[str, Any]:
    org_id = _org_id(current_user)
    pipeline = _pipeline_or_404(db, pipeline_id, org_id)

    stages = (
        db.query(PipelineStage)
        .filter(PipelineStage.pipeline_id == pipeline_id)
        .order_by(PipelineStage.orden)
        .all()
    )

    # Un query para todos los deals del pipeline, agrupados en Python
    deals_q = (
        db.query(Deal)
        .filter(Deal.pipeline_id == pipeline_id)
    )
    if org_id:
        deals_q = deals_q.filter(Deal.organization_id == org_id)

    deals_by_stage: dict[str, list[DealOut]] = {str(s.id): [] for s in stages}
    for deal in deals_q.order_by(Deal.orden_en_stage).all():
        key = str(deal.stage_id)
        if key in deals_by_stage:
            deals_by_stage[key].append(DealOut.model_validate(deal))

    return {
        "pipeline": PipelineOut.model_validate(pipeline),
        "stages": [StageOut.model_validate(s) for s in stages],
        "deals_by_stage": deals_by_stage,
    }


# ---------------------------------------------------------------------------
# POST /deals
# ---------------------------------------------------------------------------
@router.post("/deals", response_model=DealOut, status_code=201, dependencies=[Depends(allow_all_staff)])
def crear_deal(
    payload: DealCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    org_id = _org_id(current_user)

    # Verificar que el pipeline pertenece al org
    _pipeline_or_404(db, payload.pipeline_id, org_id)

    # Resolver stage_id: si no viene, usar el primer stage (min orden)
    if payload.stage_id is not None:
        stage_q = db.query(PipelineStage).filter(
            PipelineStage.id == payload.stage_id,
            PipelineStage.pipeline_id == payload.pipeline_id,
        )
        if org_id:
            stage_q = stage_q.filter(PipelineStage.organization_id == org_id)
        stage = stage_q.first()
        if not stage:
            raise HTTPException(status_code=404, detail="Stage no encontrado")
        stage_id = stage.id
    else:
        first_stage = (
            db.query(PipelineStage)
            .filter(PipelineStage.pipeline_id == payload.pipeline_id)
            .order_by(PipelineStage.orden)
            .first()
        )
        if not first_stage:
            raise HTTPException(status_code=400, detail="El pipeline no tiene stages")
        stage_id = first_stage.id

    # orden_en_stage = max actual + 1
    max_orden = (
        db.query(func.max(Deal.orden_en_stage))
        .filter(Deal.stage_id == stage_id)
        .scalar()
    )
    orden_en_stage = (max_orden or 0) + 1

    deal = Deal(
        organization_id=org_id,
        pipeline_id=payload.pipeline_id,
        stage_id=stage_id,
        titulo=payload.titulo,
        cliente_id=payload.cliente_id,
        orden_id=payload.orden_id,
        monto=payload.monto,
        moneda=payload.moneda,
        owner_user_id=payload.owner_user_id,
        orden_en_stage=orden_en_stage,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


# ---------------------------------------------------------------------------
# PATCH /deals/{deal_id}
# ---------------------------------------------------------------------------
@router.patch("/deals/{deal_id}", response_model=DealOut, dependencies=[Depends(allow_all_staff)])
def actualizar_deal(
    deal_id: int,
    payload: DealUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    org_id = _org_id(current_user)
    deal = _deal_or_404(db, deal_id, org_id)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(deal, field, value)

    db.commit()
    db.refresh(deal)
    return deal


# ---------------------------------------------------------------------------
# PATCH /deals/{deal_id}/move
# ---------------------------------------------------------------------------
@router.patch("/deals/{deal_id}/move", response_model=DealOut, dependencies=[Depends(allow_all_staff)])
def mover_deal(
    deal_id: int,
    payload: DealMove,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    org_id = _org_id(current_user)
    deal = _deal_or_404(db, deal_id, org_id)

    # Verificar que el target stage pertenece al mismo pipeline y al org
    target_q = db.query(PipelineStage).filter(
        PipelineStage.id == payload.stage_id,
        PipelineStage.pipeline_id == deal.pipeline_id,
    )
    if org_id:
        target_q = target_q.filter(PipelineStage.organization_id == org_id)
    target_stage = target_q.first()
    if not target_stage:
        raise HTTPException(status_code=404, detail="Stage destino no encontrado")

    deal.stage_id = payload.stage_id

    if payload.orden_en_stage is not None:
        deal.orden_en_stage = payload.orden_en_stage

    # Cerrar si llega a etapa terminal
    if target_stage.es_ganado or target_stage.es_perdido:
        deal.cerrado_en = datetime.now(timezone.utc)
    else:
        deal.cerrado_en = None

    db.commit()
    db.refresh(deal)
    return deal


# ---------------------------------------------------------------------------
# DELETE /deals/{deal_id}
# ---------------------------------------------------------------------------
@router.delete("/deals/{deal_id}", status_code=204, dependencies=[Depends(allow_all_staff)])
def eliminar_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    org_id = _org_id(current_user)
    deal = _deal_or_404(db, deal_id, org_id)
    db.delete(deal)
    db.commit()
