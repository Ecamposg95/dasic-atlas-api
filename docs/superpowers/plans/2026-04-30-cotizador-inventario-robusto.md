# Cotizador robusto + Inventario "siempre saber qué se tiene" — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/superpowers/specs/2026-04-30-cotizador-inventario-robusto-design.md`

**Goal:** Hacer que el cotizador soporte TC del día (Banxico), líneas de tres tipos (catálogo / fantasma / servicio), reserve stock al cotizar, genere OCs automáticas a proveedores asignados, y que inventario muestre disponibilidad en tiempo real con timeline auditado.

**Architecture:** SQLAlchemy 2 con tres modelos nuevos (`MovimientoStock`, `TipoCambioDia`) y dos columnas/relaciones extra en `Producto` y `DetalleOrden`. Tres servicios nuevos (`fx_service`, `stock_service`, `auto_oc_service`) encapsulan la lógica. Endpoints REST en routers `fx`, `inventario` y `ventas` (extendido). Frontend Jinja+Alpine se actualiza en `cotizador.html` e `inventario.html`. ECharts ya está cargado para el dashboard; lo reusamos para sparklines en inventario.

**Tech Stack:** FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (psycopg) · Pydantic · Jinja2 · Tailwind (Play CDN) · Alpine.js · ECharts 5.6 · `httpx` (ya instalado vía anthropic SDK; si falta lo agrego con uv).

**Convención de testing:** Este repo no tiene suite pytest hoy. Cada tarea termina con un *smoke test* explícito vía `curl` + verificaciones SQL en psql + revisión visual cuando aplica. Cada tarea termina con un commit.

**Cómo leer este plan:** Cada tarea es ~30-60 min de trabajo, una unidad atómica que se commitea. Los pasos dentro de la tarea son acciones de 2-5 min.

---

## Task 1 — Migración + modelos nuevos

**Files:**
- Create: `migrations/versions/20260430_01_cotizador_robusto.py`
- Create: `app/models/inventory.py`
- Create: `app/models/fx.py`
- Modify: `app/models/catalog.py`
- Modify: `app/models/sales.py`
- Modify: `app/models/enums.py`
- Modify: `app/models/__init__.py`

- [ ] **Step 1.1: Agregar enums nuevos**

Editar `app/models/enums.py`, agregar al final:

```python
class TipoLineaCotizacion(str, enum.Enum):
    PRODUCTO_CATALOGO = "producto_catalogo"
    PRODUCTO_FANTASMA = "producto_fantasma"
    SERVICIO = "servicio"


class TipoMovimientoStock(str, enum.Enum):
    ENTRADA = "entrada"      # OC recibida, devolución de cliente
    SALIDA = "salida"        # venta concretada
    AJUSTE = "ajuste"        # corrección manual (alta/baja)
    RESERVA = "reserva"      # cotización guardada
    LIBERACION = "liberacion"  # cotización cancelada/vencida
```

- [ ] **Step 1.2: Crear `app/models/inventory.py`**

```python
"""Inventario: movimientos de stock auditables."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # TipoMovimientoStock
    cantidad = Column(Integer, nullable=False)  # signed: +entrada/-salida/+reserva/-liberacion
    referencia_tipo = Column(String(20), nullable=True)  # cotizacion / venta / oc / manual
    referencia_id = Column(Integer, nullable=True, index=True)
    motivo = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    stock_resultante = Column(Integer, nullable=False)

    producto = relationship("Producto")
    usuario = relationship("Usuario")
```

- [ ] **Step 1.3: Crear `app/models/fx.py`**

```python
"""Tipos de cambio cacheados por día."""

from sqlalchemy import Column, Date, DateTime, DECIMAL, Integer, String
from sqlalchemy.sql import func

from app.db import Base


class TipoCambioDia(Base):
    __tablename__ = "tipos_cambio_dia"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    usd_mxn = Column(DECIMAL(12, 6), nullable=False)
    fuente = Column(String(20), nullable=False)  # BANXICO / EXCHANGERATE / MANUAL
    obtenido_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 1.4: Extender `app/models/catalog.py::Producto`**

Agregar dentro de `class Producto`, después de `unidad`:

```python
    proveedor_principal_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True, index=True)
    proveedor_alterno_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    tiempo_entrega_dias = Column(Integer, nullable=False, default=7)
    es_servicio = Column(Boolean, nullable=False, default=False)
```

Y al final de la clase (antes de la siguiente clase) agregar:

```python
    proveedor_principal = relationship("Proveedor", foreign_keys=[proveedor_principal_id])
    proveedor_alterno = relationship("Proveedor", foreign_keys=[proveedor_alterno_id])
    movimientos_stock = relationship("MovimientoStock", back_populates="producto", cascade="all, delete-orphan")
```

(Borra el `cascade="all, delete-orphan"` si ya hay un cascade conflict; ajustá según el patrón existente.)

- [ ] **Step 1.5: Extender `app/models/sales.py::DetalleOrden`**

Agregar dentro de `class DetalleOrden`:

```python
    tipo_linea = Column(String(20), nullable=False, default="producto_catalogo")  # TipoLineaCotizacion
    proveedor_sugerido_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
```

- [ ] **Step 1.6: Exponer modelos nuevos en `app/models/__init__.py`**

Agregar al `__init__.py` los imports y `__all__`:

```python
from .inventory import MovimientoStock
from .fx import TipoCambioDia
from .enums import TipoLineaCotizacion, TipoMovimientoStock
```

Y agregarlos al `__all__` si existe.

- [ ] **Step 1.7: Crear migración Alembic**

Crear `migrations/versions/20260430_01_cotizador_robusto.py`:

```python
"""cotizador robusto + inventario auditable

Revision ID: 20260430_01
Revises: 20260429_02
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_01"
down_revision = "20260429_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # productos: nuevos campos
    op.add_column("productos", sa.Column("proveedor_principal_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=True))
    op.add_column("productos", sa.Column("proveedor_alterno_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=True))
    op.add_column("productos", sa.Column("tiempo_entrega_dias", sa.Integer(), nullable=False, server_default="7"))
    op.add_column("productos", sa.Column("es_servicio", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_productos_proveedor_principal_id", "productos", ["proveedor_principal_id"])

    # detalles_orden: tipo de línea + proveedor sugerido para fantasmas
    op.add_column("detalles_orden", sa.Column("tipo_linea", sa.String(length=20), nullable=False, server_default="producto_catalogo"))
    op.add_column("detalles_orden", sa.Column("proveedor_sugerido_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=True))

    # movimientos_stock
    op.create_table(
        "movimientos_stock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("referencia_tipo", sa.String(length=20), nullable=True),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("stock_resultante", sa.Integer(), nullable=False),
    )
    op.create_index("ix_movimientos_stock_producto_creado", "movimientos_stock", ["producto_id", "creado_en"])
    op.create_index("ix_movimientos_stock_referencia_id", "movimientos_stock", ["referencia_id"])

    # tipos_cambio_dia
    op.create_table(
        "tipos_cambio_dia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False, unique=True),
        sa.Column("usd_mxn", sa.DECIMAL(precision=12, scale=6), nullable=False),
        sa.Column("fuente", sa.String(length=20), nullable=False),
        sa.Column("obtenido_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tipos_cambio_dia_fecha", "tipos_cambio_dia", ["fecha"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tipos_cambio_dia_fecha", table_name="tipos_cambio_dia")
    op.drop_table("tipos_cambio_dia")
    op.drop_index("ix_movimientos_stock_referencia_id", table_name="movimientos_stock")
    op.drop_index("ix_movimientos_stock_producto_creado", table_name="movimientos_stock")
    op.drop_table("movimientos_stock")
    op.drop_column("detalles_orden", "proveedor_sugerido_id")
    op.drop_column("detalles_orden", "tipo_linea")
    op.drop_index("ix_productos_proveedor_principal_id", table_name="productos")
    op.drop_column("productos", "es_servicio")
    op.drop_column("productos", "tiempo_entrega_dias")
    op.drop_column("productos", "proveedor_alterno_id")
    op.drop_column("productos", "proveedor_principal_id")
```

- [ ] **Step 1.8: Aplicar migración**

```bash
set -a && . ./.env && set +a && .venv/bin/alembic upgrade head
```

Expected: `INFO Running upgrade 20260429_02 -> 20260430_01, cotizador robusto + inventario auditable`.

- [ ] **Step 1.9: Smoke test SQL**

```bash
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "\d productos" | grep -E "proveedor|tiempo_entrega|es_servicio"
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "\d detalles_orden" | grep -E "tipo_linea|proveedor_sugerido"
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "\dt movimientos_stock tipos_cambio_dia"
```

Expected: las 4 columnas en productos, 2 en detalles_orden, ambas tablas listadas.

- [ ] **Step 1.10: Compile-check + commit**

```bash
.venv/bin/python -m py_compile app/models/inventory.py app/models/fx.py app/models/catalog.py app/models/sales.py app/models/enums.py
git add app/models/ migrations/versions/20260430_01_cotizador_robusto.py
git commit -m "feat(db): MovimientoStock + TipoCambioDia + producto.proveedor_principal + detalle.tipo_linea"
```

---

## Task 2 — Schemas Pydantic

**Files:**
- Create: `app/schemas/inventory.py`
- Create: `app/schemas/fx.py`
- Modify: `app/schemas/catalog.py`
- Modify: `app/schemas/sales.py`
- Modify: `app/schemas/__init__.py`

- [ ] **Step 2.1: Crear `app/schemas/fx.py`**

```python
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class TipoCambioDiaResponse(BaseModel):
    fecha: date
    usd_mxn: Decimal
    fuente: str
    obtenido_en: datetime
    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2.2: Crear `app/schemas/inventory.py`**

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MovimientoStockResponse(BaseModel):
    id: int
    producto_id: int
    tipo: str
    cantidad: int
    referencia_tipo: Optional[str] = None
    referencia_id: Optional[int] = None
    motivo: Optional[str] = None
    creado_en: datetime
    stock_resultante: int
    model_config = ConfigDict(from_attributes=True)


class AjusteManualIn(BaseModel):
    producto_id: int
    cantidad: int = Field(..., description="Signed: positivo entrada, negativo salida")
    motivo: str = Field(..., min_length=3, max_length=500)


class DisponibilidadResponse(BaseModel):
    producto_id: int
    stock_actual: int
    reservado: int
    disponible: int
    en_oc_pendiente: int
```

- [ ] **Step 2.3: Extender `app/schemas/catalog.py::ProductoBase`**

Agregar dentro de `ProductoBase`:

```python
    proveedor_principal_id: Optional[int] = None
    proveedor_alterno_id: Optional[int] = None
    tiempo_entrega_dias: int = Field(7, ge=0)
    es_servicio: bool = False
```

Y agregar a `ProductoUpdate` los mismos campos como `Optional`:

```python
    proveedor_principal_id: Optional[int] = None
    proveedor_alterno_id: Optional[int] = None
    tiempo_entrega_dias: Optional[int] = Field(None, ge=0)
    es_servicio: Optional[bool] = None
```

- [ ] **Step 2.4: Extender `app/schemas/sales.py::DetalleOrdenCreate`**

Buscar `DetalleOrdenCreate` y agregar:

```python
    tipo_linea: Optional[str] = "producto_catalogo"  # producto_catalogo / producto_fantasma / servicio
    proveedor_sugerido_id: Optional[int] = None
```

(Si no existe el schema todavía bajo este nombre, ubicar el que se usa en `app/routers/ventas.py::crear_orden` y extenderlo.)

- [ ] **Step 2.5: Exportar schemas nuevos en `app/schemas/__init__.py`**

```python
from .fx import TipoCambioDiaResponse
from .inventory import MovimientoStockResponse, AjusteManualIn, DisponibilidadResponse
```

Y al `__all__`.

- [ ] **Step 2.6: Compile + commit**

```bash
.venv/bin/python -m py_compile app/schemas/inventory.py app/schemas/fx.py app/schemas/catalog.py app/schemas/sales.py
git add app/schemas/
git commit -m "feat(schemas): inventory + fx + tipo_linea en detalle"
```

---

## Task 3 — Servicio FX (Banxico + fallback + cache)

**Files:**
- Create: `app/services/fx_service.py`
- Create: `app/routers/fx.py`
- Modify: `app/main.py`
- Modify: `app/services/__init__.py`

- [ ] **Step 3.1: Crear `app/services/fx_service.py`**

```python
"""Servicio de tipo de cambio USD/MXN.

Estrategia:
1. Cache en `tipos_cambio_dia` (1 row por fecha).
2. Fuente primaria: Banxico SIE serie SF63528 (TC FIX). Requiere BANXICO_TOKEN.
3. Fallback: api.exchangerate.host (sin token).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app import models

log = logging.getLogger(__name__)

BANXICO_SERIE = "SF63528"
BANXICO_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/oportuno"
EXCHANGERATE_URL = "https://api.exchangerate.host/latest?base=USD&symbols=MXN"


class FXError(RuntimeError):
    pass


def _http_get_json(url: str, headers: Optional[dict] = None, timeout: int = 8) -> dict:
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _from_banxico(token: str) -> tuple[Decimal, date]:
    url = BANXICO_URL.format(serie=BANXICO_SERIE)
    data = _http_get_json(url, headers={"Bmx-Token": token})
    serie = data["bmx"]["series"][0]
    dato = serie["datos"][0]
    valor = Decimal(dato["dato"].replace(",", ""))
    fecha_str = dato["fecha"]  # "DD/MM/YYYY"
    d, m, y = fecha_str.split("/")
    return valor, date(int(y), int(m), int(d))


def _from_exchangerate() -> tuple[Decimal, date]:
    data = _http_get_json(EXCHANGERATE_URL)
    rate = Decimal(str(data["rates"]["MXN"]))
    fecha_iso = data.get("date")
    if fecha_iso:
        y, m, d = fecha_iso.split("-")
        return rate, date(int(y), int(m), int(d))
    return rate, date.today()


def get_or_fetch(db: Session, fecha: Optional[date] = None, force: bool = False) -> "models.TipoCambioDia":
    fecha = fecha or date.today()
    if not force:
        existing = db.query(models.TipoCambioDia).filter(models.TipoCambioDia.fecha == fecha).first()
        if existing:
            return existing

    token = os.getenv("BANXICO_TOKEN", "").strip()
    valor: Optional[Decimal] = None
    fuente = "MANUAL"
    fecha_real = fecha

    if token:
        try:
            valor, fecha_real = _from_banxico(token)
            fuente = "BANXICO"
        except (URLError, HTTPError, KeyError, IndexError, ValueError) as exc:
            log.warning("Banxico FX fetch falló: %s. Caigo a fallback.", exc)

    if valor is None:
        try:
            valor, fecha_real = _from_exchangerate()
            fuente = "EXCHANGERATE"
        except (URLError, HTTPError, KeyError, ValueError) as exc:
            log.error("Fallback exchangerate.host también falló: %s", exc)
            raise FXError("No se pudo obtener TC de ninguna fuente.") from exc

    # upsert por fecha real recibida (puede no ser hoy si es fin de semana / feriado)
    row = db.query(models.TipoCambioDia).filter(models.TipoCambioDia.fecha == fecha_real).first()
    if row:
        if force:
            row.usd_mxn = valor
            row.fuente = fuente
            row.obtenido_en = datetime.utcnow()
    else:
        row = models.TipoCambioDia(fecha=fecha_real, usd_mxn=valor, fuente=fuente)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
```

- [ ] **Step 3.2: Registrar export en `app/services/__init__.py`**

Agregar:

```python
from .fx_service import get_or_fetch as fx_get_or_fetch, FXError  # noqa: F401
```

- [ ] **Step 3.3: Crear `app/routers/fx.py`**

```python
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.security import allow_admin, allow_all_staff
from app.services.fx_service import get_or_fetch, FXError

router = APIRouter(prefix="/api/fx", tags=["Tipo de cambio"])


@router.get("/usd-mxn", response_model=schemas.TipoCambioDiaResponse, dependencies=[Depends(allow_all_staff)])
def usd_mxn(
    fecha: Optional[date] = Query(None, description="YYYY-MM-DD; default hoy"),
    db: Session = Depends(get_db),
):
    try:
        return get_or_fetch(db, fecha=fecha)
    except FXError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/refresh", response_model=schemas.TipoCambioDiaResponse, dependencies=[Depends(allow_admin)])
def refresh(db: Session = Depends(get_db)):
    try:
        return get_or_fetch(db, force=True)
    except FXError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
```

- [ ] **Step 3.4: Wire en `app/main.py`**

Agregar import y `app.include_router(fx.router)` siguiendo el patrón existente.

```python
from app.routers import auth, clientes, compras, dashboard, fx, gastos, productos, usuarios, ventas
...
app.include_router(fx.router)
```

- [ ] **Step 3.5: Smoke test FX**

```bash
.venv/bin/python -m py_compile app/services/fx_service.py app/routers/fx.py
sleep 2 && tail -5 /tmp/dasic-uvicorn.log
curl -s -c /tmp/dasic-cookies -X POST http://127.0.0.1:8001/api/auth/login -d 'username=admin@dasic.com&password=admin123' -H 'Content-Type: application/x-www-form-urlencoded' > /dev/null
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/fx/usd-mxn" | python3 -m json.tool
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT fecha, usd_mxn, fuente FROM tipos_cambio_dia ORDER BY fecha DESC LIMIT 3;"
```

Expected: 200 con `{ fecha, usd_mxn, fuente: "EXCHANGERATE" }` (sin token), o `BANXICO` si está configurado. SQL muestra la row.

- [ ] **Step 3.6: Commit**

```bash
git add app/services/fx_service.py app/services/__init__.py app/routers/fx.py app/main.py
git commit -m "feat(fx): servicio TC con cache + Banxico/exchangerate fallback"
```

---

## Task 4 — Servicio de stock + endpoints inventario

**Files:**
- Create: `app/services/stock_service.py`
- Create: `app/routers/inventario.py`
- Modify: `app/main.py`
- Modify: `app/services/__init__.py`

- [ ] **Step 4.1: Crear `app/services/stock_service.py`**

```python
"""Operaciones de stock auditables.

Toda mutación al stock pasa por aquí. Las reservas (cotizaciones vivas)
no modifican stock_actual pero afectan disponible.

disponible = stock_actual - sum(cantidad de movimientos RESERVA activos)

Una reserva está "activa" si la cotización referenciada existe y está en
estatus COTIZACION (no convertida ni cancelada). La conversión transforma
RESERVA → SALIDA. La cancelación emite LIBERACION.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.models.enums import EstatusOrden, TipoMovimientoStock


def aplicar_movimiento(
    db: Session,
    *,
    producto: "models.Producto",
    tipo: str,
    cantidad: int,
    referencia_tipo: Optional[str] = None,
    referencia_id: Optional[int] = None,
    motivo: Optional[str] = None,
    usuario: Optional["models.Usuario"] = None,
) -> "models.MovimientoStock":
    """Crea row en movimientos_stock. Para tipos ENTRADA/SALIDA/AJUSTE
    suma `cantidad` (signed) a producto.stock_actual. Para RESERVA/LIBERACION
    no toca stock_actual."""

    afecta_stock = tipo in (
        TipoMovimientoStock.ENTRADA.value,
        TipoMovimientoStock.SALIDA.value,
        TipoMovimientoStock.AJUSTE.value,
    )
    if afecta_stock:
        nuevo = (producto.stock_actual or 0) + cantidad
        if nuevo < 0:
            raise ValueError(
                f"Stock no puede quedar negativo para {producto.sku} (actual={producto.stock_actual}, delta={cantidad})"
            )
        producto.stock_actual = nuevo
        stock_resultante = nuevo
    else:
        stock_resultante = producto.stock_actual or 0

    mov = models.MovimientoStock(
        producto_id=producto.id,
        tipo=tipo,
        cantidad=cantidad,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        motivo=motivo,
        usuario_id=usuario.id if usuario else None,
        stock_resultante=stock_resultante,
    )
    db.add(mov)
    db.flush()
    return mov


def reservas_activas(db: Session, producto_id: int) -> int:
    """Suma neta de RESERVA - LIBERACION para cotizaciones aún en estatus COTIZACION."""
    rows = (
        db.query(
            models.MovimientoStock.tipo,
            func.coalesce(func.sum(models.MovimientoStock.cantidad), 0),
        )
        .join(models.OrdenVenta, models.OrdenVenta.id == models.MovimientoStock.referencia_id)
        .filter(
            models.MovimientoStock.producto_id == producto_id,
            models.MovimientoStock.referencia_tipo == "cotizacion",
            models.MovimientoStock.tipo.in_([
                TipoMovimientoStock.RESERVA.value,
                TipoMovimientoStock.LIBERACION.value,
            ]),
            models.OrdenVenta.estatus == EstatusOrden.COTIZACION,
        )
        .group_by(models.MovimientoStock.tipo)
        .all()
    )
    reservado = 0
    for tipo, suma in rows:
        if tipo == TipoMovimientoStock.RESERVA.value:
            reservado += int(suma)
        else:  # LIBERACION resta
            reservado += int(suma)  # cantidad ya viene negativa para LIBERACION
    return max(reservado, 0)


def disponibilidad(db: Session, producto: "models.Producto") -> dict:
    reservado = reservas_activas(db, producto.id)
    en_oc_q = (
        db.query(func.coalesce(func.sum(models.DetalleCompra.cantidad), 0))
        .join(models.OrdenCompra, models.OrdenCompra.id == models.DetalleCompra.orden_compra_id)
        .filter(
            models.DetalleCompra.producto_id == producto.id,
            models.OrdenCompra.estatus.in_(["borrador", "enviada", "confirmada"]),
        )
    )
    en_oc = int(en_oc_q.scalar() or 0)
    return {
        "producto_id": producto.id,
        "stock_actual": producto.stock_actual or 0,
        "reservado": reservado,
        "disponible": (producto.stock_actual or 0) - reservado,
        "en_oc_pendiente": en_oc,
    }


def reservar_para_cotizacion(
    db: Session,
    *,
    producto: "models.Producto",
    cantidad: int,
    cotizacion_id: int,
    usuario: Optional["models.Usuario"] = None,
) -> "models.MovimientoStock":
    return aplicar_movimiento(
        db,
        producto=producto,
        tipo=TipoMovimientoStock.RESERVA.value,
        cantidad=cantidad,
        referencia_tipo="cotizacion",
        referencia_id=cotizacion_id,
        usuario=usuario,
    )


def liberar_reservas_cotizacion(
    db: Session,
    *,
    cotizacion_id: int,
    motivo: str = "cotización cancelada/vencida",
    usuario: Optional["models.Usuario"] = None,
) -> int:
    """Genera LIBERACION (cantidad negativa) por cada RESERVA activa de la cotización."""
    reservas = (
        db.query(models.MovimientoStock)
        .filter(
            models.MovimientoStock.referencia_tipo == "cotizacion",
            models.MovimientoStock.referencia_id == cotizacion_id,
            models.MovimientoStock.tipo == TipoMovimientoStock.RESERVA.value,
        )
        .all()
    )
    if not reservas:
        return 0

    # neto: por producto, suma reservas - liberaciones ya emitidas
    netas: dict[int, int] = {}
    for r in reservas:
        netas[r.producto_id] = netas.get(r.producto_id, 0) + r.cantidad

    liberaciones = (
        db.query(models.MovimientoStock)
        .filter(
            models.MovimientoStock.referencia_tipo == "cotizacion",
            models.MovimientoStock.referencia_id == cotizacion_id,
            models.MovimientoStock.tipo == TipoMovimientoStock.LIBERACION.value,
        )
        .all()
    )
    for l in liberaciones:
        netas[l.producto_id] = netas.get(l.producto_id, 0) + l.cantidad  # cantidad ya es negativa

    emitidas = 0
    for producto_id, neto in netas.items():
        if neto <= 0:
            continue
        producto = db.get(models.Producto, producto_id)
        if not producto:
            continue
        aplicar_movimiento(
            db,
            producto=producto,
            tipo=TipoMovimientoStock.LIBERACION.value,
            cantidad=-neto,
            referencia_tipo="cotizacion",
            referencia_id=cotizacion_id,
            motivo=motivo,
            usuario=usuario,
        )
        emitidas += 1
    return emitidas


def consumir_reservas_a_salida(
    db: Session,
    *,
    cotizacion_id: int,
    usuario: Optional["models.Usuario"] = None,
) -> int:
    """Cuando una cotización se convierte en venta: por cada RESERVA neta, emite SALIDA equivalente
    (descuenta stock_actual) y LIBERACION para cerrar la reserva conceptual."""
    reservas = (
        db.query(models.MovimientoStock.producto_id, func.sum(models.MovimientoStock.cantidad))
        .filter(
            models.MovimientoStock.referencia_tipo == "cotizacion",
            models.MovimientoStock.referencia_id == cotizacion_id,
            models.MovimientoStock.tipo.in_([
                TipoMovimientoStock.RESERVA.value,
                TipoMovimientoStock.LIBERACION.value,
            ]),
        )
        .group_by(models.MovimientoStock.producto_id)
        .all()
    )
    procesadas = 0
    for producto_id, neto in reservas:
        n = int(neto or 0)
        if n <= 0:
            continue
        producto = db.get(models.Producto, producto_id)
        if not producto:
            continue
        # liberar la reserva conceptual
        aplicar_movimiento(
            db,
            producto=producto,
            tipo=TipoMovimientoStock.LIBERACION.value,
            cantidad=-n,
            referencia_tipo="cotizacion",
            referencia_id=cotizacion_id,
            motivo="convertida a venta",
            usuario=usuario,
        )
        # registrar la salida real
        aplicar_movimiento(
            db,
            producto=producto,
            tipo=TipoMovimientoStock.SALIDA.value,
            cantidad=-n,
            referencia_tipo="venta",
            referencia_id=cotizacion_id,
            motivo="venta concretada",
            usuario=usuario,
        )
        procesadas += 1
    return procesadas
```

- [ ] **Step 4.2: Crear `app/routers/inventario.py`**

```python
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_admin_asistente, allow_all_staff, get_current_user
from app.services.stock_service import (
    aplicar_movimiento,
    disponibilidad,
    liberar_reservas_cotizacion,
)
from app.models.enums import EstatusOrden, TipoMovimientoStock

router = APIRouter(prefix="/api/inventario", tags=["Inventario"])


@router.get("/movimientos", response_model=List[schemas.MovimientoStockResponse], dependencies=[Depends(allow_all_staff)])
def listar_movimientos(
    producto_id: Optional[int] = None,
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    desde = datetime.utcnow() - timedelta(days=dias)
    q = db.query(models.MovimientoStock).filter(models.MovimientoStock.creado_en >= desde)
    if producto_id:
        q = q.filter(models.MovimientoStock.producto_id == producto_id)
    return q.order_by(models.MovimientoStock.creado_en.desc()).limit(500).all()


@router.post("/movimientos", response_model=schemas.MovimientoStockResponse, dependencies=[Depends(allow_admin_asistente)])
def crear_ajuste_manual(
    payload: schemas.AjusteManualIn,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    producto = db.get(models.Producto, payload.producto_id)
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    try:
        mov = aplicar_movimiento(
            db,
            producto=producto,
            tipo=TipoMovimientoStock.AJUSTE.value,
            cantidad=payload.cantidad,
            referencia_tipo="manual",
            motivo=payload.motivo,
            usuario=current_user,
        )
        db.commit()
        db.refresh(mov)
        return mov
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))


@router.get("/disponibilidad/{producto_id}", response_model=schemas.DisponibilidadResponse, dependencies=[Depends(allow_all_staff)])
def disponibilidad_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.get(models.Producto, producto_id)
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    return disponibilidad(db, producto)


@router.post("/liberar-vencidas", dependencies=[Depends(allow_admin_asistente)])
def liberar_vencidas(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Libera reservas de cotizaciones cuya fecha_vencimiento ya pasó. Idempotente."""
    ahora = datetime.utcnow()
    candidatas = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.estatus == EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_vencimiento.is_not(None),
            models.OrdenVenta.fecha_vencimiento < ahora,
        )
        .all()
    )
    total_liberadas = 0
    for cot in candidatas:
        total_liberadas += liberar_reservas_cotizacion(
            db,
            cotizacion_id=cot.id,
            motivo="vencimiento automático",
            usuario=current_user,
        )
    db.commit()
    return {"cotizaciones_revisadas": len(candidatas), "productos_liberados": total_liberadas}
```

- [ ] **Step 4.3: Wire router en `app/main.py`**

Agregar `inventario` al import de routers y `app.include_router(inventario.router)`.

- [ ] **Step 4.4: Smoke test inventario**

```bash
.venv/bin/python -m py_compile app/services/stock_service.py app/routers/inventario.py
sleep 2 && tail -5 /tmp/dasic-uvicorn.log

# Re-login
curl -s -c /tmp/dasic-cookies -X POST http://127.0.0.1:8001/api/auth/login -d 'username=admin@dasic.com&password=admin123' -H 'Content-Type: application/x-www-form-urlencoded' > /dev/null

# Disponibilidad de un producto existente
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/inventario/disponibilidad/2" | python3 -m json.tool

# Ajuste manual: bajar 1 con motivo
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/inventario/movimientos" -H 'Content-Type: application/json' -d '{"producto_id": 2, "cantidad": -1, "motivo": "ajuste por conteo físico"}' | python3 -m json.tool

# Lista movimientos
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/inventario/movimientos?dias=1" | python3 -m json.tool | head -30
```

Expected: disponibilidad devuelve `{stock_actual, reservado: 0, disponible, en_oc_pendiente}`. Ajuste manual baja stock y crea row en movimientos_stock con stock_resultante.

- [ ] **Step 4.5: Commit**

```bash
git add app/services/stock_service.py app/routers/inventario.py app/services/__init__.py app/main.py
git commit -m "feat(stock): MovimientoStock service + /api/inventario endpoints"
```

---

## Task 5 — Reservas en flujo de cotizaciones

**Files:**
- Modify: `app/routers/ventas.py` (POST `/`, PUT `/{id}`, POST `/{id}/convertir`)
- Modify: posible nuevo endpoint POST `/{id}/cancelar`

- [ ] **Step 5.1: Hook RESERVA en POST `/api/ventas/`**

En `app/routers/ventas.py::crear_orden`, dentro del loop sobre `orden_data.detalles`, después de crear el `DetalleOrden` y antes del `db.commit()` final, agregar para cada detalle con `producto`:

```python
# Reserva inventario sólo para productos del catálogo (no fantasmas, no servicios)
es_servicio = (item.tipo_linea == "servicio") or (producto and producto.es_servicio)
if (
    tipo_orden == models.EstatusOrden.COTIZACION
    and producto is not None
    and not es_servicio
):
    from app.services.stock_service import reservar_para_cotizacion
    reservar_para_cotizacion(
        db,
        producto=producto,
        cantidad=item.cantidad,
        cotizacion_id=nueva_orden.id,
        usuario=current_user,
    )
```

(Nota: el servicio ya hace `db.flush()`. Con commit al final del bloque ya queda persistido.)

- [ ] **Step 5.2: Hook ajuste delta en PUT `/api/ventas/{id}`**

En `actualizar_orden`, antes de borrar detalles viejos: liberar reservas de la cotización vieja. Después de re-insertar detalles: re-reservar.

```python
from app.services.stock_service import liberar_reservas_cotizacion, reservar_para_cotizacion
...
# Antes de borrar detalles
liberar_reservas_cotizacion(db, cotizacion_id=orden.id, motivo="re-edición de cotización")
# ... borra y reinserta detalles ...
# Al insertar cada nuevo detalle con producto del catálogo:
if producto and not (item.tipo_linea == "servicio" or producto.es_servicio):
    reservar_para_cotizacion(db, producto=producto, cantidad=item.cantidad, cotizacion_id=orden.id)
```

- [ ] **Step 5.3: Hook RESERVA→SALIDA en POST `/api/ventas/{id}/convertir`**

En `convertir_cotizacion`, **reemplazar** el bloque actual de "Descontar Stock" por una llamada al servicio:

```python
from app.services.stock_service import consumir_reservas_a_salida
...
# Verificar que haya disponible suficiente (sumando reservas de OTRAS cotizaciones)
for det in orden.detalles:
    if det.producto is None:
        continue
    if det.tipo_linea == "servicio" or det.producto.es_servicio:
        continue
    # disponible considerando OTRAS cotizaciones distintas a esta
    from app.services.stock_service import reservas_activas
    otras = reservas_activas(db, det.producto.id) - det.cantidad  # quitamos la reserva propia
    libre = (det.producto.stock_actual or 0) - max(otras, 0)
    if libre < det.cantidad:
        raise HTTPException(400, f"Stock insuficiente para {det.producto.sku}")

# Convertir reservas a salidas
consumir_reservas_a_salida(db, cotizacion_id=orden.id, usuario=current_user)
```

(Borrar el viejo `for det in orden.detalles: if det.producto.stock_actual < det.cantidad: ...; det.producto.stock_actual -= det.cantidad`.)

- [ ] **Step 5.4: Endpoint cancelar cotización**

Agregar al final de `ventas.py`:

```python
@router.post("/{id}/cancelar", dependencies=[Depends(allow_all_staff)])
def cancelar_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")
    if orden.estatus != models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "Solo se cancelan cotizaciones abiertas")
    from app.services.stock_service import liberar_reservas_cotizacion
    liberar_reservas_cotizacion(
        db, cotizacion_id=orden.id, motivo="cancelación manual", usuario=current_user
    )
    orden.estatus = models.EstatusOrden.CANCELADA
    db.commit()
    return {"ok": True, "folio": orden.folio}
```

- [ ] **Step 5.5: Smoke test reservas**

```bash
.venv/bin/python -m py_compile app/routers/ventas.py
sleep 2 && tail -5 /tmp/dasic-uvicorn.log
curl -s -c /tmp/dasic-cookies -X POST http://127.0.0.1:8001/api/auth/login -d 'username=admin@dasic.com&password=admin123' -H 'Content-Type: application/x-www-form-urlencoded' > /dev/null

# Crear cotización con producto del catálogo (id=2 = GV2ME14, stock=2)
QUOTE=$(curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/?tipo_orden=cotizacion" -H 'Content-Type: application/json' -d '{
  "cliente_id": 1, "moneda": "MXN", "tipo_cambio": 1,
  "detalles": [{"producto_id": 2, "cantidad": 1, "utilidad": 30, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "producto_catalogo"}],
  "observaciones": "test reserva"
}')
QID=$(echo "$QUOTE" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "Quote id=$QID"

# Disponibilidad debe mostrar reservado=1
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/inventario/disponibilidad/2" | python3 -m json.tool
# Verifica row RESERVA
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT producto_id, tipo, cantidad, stock_resultante FROM movimientos_stock WHERE referencia_id=$QID;"

# Convertir → debe descontar stock real
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/$QID/convertir" | python3 -m json.tool
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT id, sku, stock_actual FROM productos WHERE id=2;"
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT tipo, cantidad FROM movimientos_stock WHERE referencia_id=$QID ORDER BY id;"

# Limpieza
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "DELETE FROM movimientos_stock WHERE referencia_id=$QID; DELETE FROM detalles_orden WHERE orden_id=$QID; DELETE FROM transacciones_clientes WHERE referencia_id=$QID; DELETE FROM ordenes_venta WHERE id=$QID;"
```

Expected: disponibilidad muestra reservado=1; movimientos_stock tiene RESERVA(+1) inicialmente y después de convertir agrega LIBERACION(-1) y SALIDA(-1); stock_actual baja de 2 a 1.

- [ ] **Step 5.6: Commit**

```bash
git add app/routers/ventas.py
git commit -m "feat(ventas): reservar stock al cotizar, RESERVA→SALIDA al convertir, cancelar libera"
```

---

## Task 6 — Tipos de línea (catálogo / fantasma / servicio) end-to-end

**Files:**
- Modify: `app/routers/ventas.py` (`crear_orden`, `actualizar_orden`)
- Modify: `app/schemas/sales.py` (DetalleOrdenCreate ya extendido en Task 2)

- [ ] **Step 6.1: Setear `tipo_linea` y `proveedor_sugerido_id` al crear DetalleOrden**

En `crear_orden` y `actualizar_orden`, en el bloque que construye `models.DetalleOrden(...)`, agregar:

```python
        # Resolver tipo_linea efectivo
        tipo_linea = (item.tipo_linea or "producto_catalogo").lower()
        if producto and producto.es_servicio:
            tipo_linea = "servicio"
        if not producto and not item.descripcion_libre:
            tipo_linea = "producto_catalogo"  # fuerce, no debería pasar
        elif not producto and item.descripcion_libre and tipo_linea not in ("servicio", "producto_fantasma"):
            tipo_linea = "producto_fantasma"

        db.add(models.DetalleOrden(
            ...,
            tipo_linea=tipo_linea,
            proveedor_sugerido_id=getattr(item, "proveedor_sugerido_id", None),
            ...
        ))
```

- [ ] **Step 6.2: Saltar reserva si tipo_linea==servicio**

En el hook de reserva (Task 5.1), la condición ya filtra `es_servicio = (item.tipo_linea == "servicio") or (producto and producto.es_servicio)`. Verificá que está alineado.

- [ ] **Step 6.3: Smoke test 3 tipos en una cotización**

```bash
QUOTE=$(curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/?tipo_orden=cotizacion" -H 'Content-Type: application/json' -d '{
  "cliente_id": 1, "moneda": "MXN", "tipo_cambio": 1,
  "detalles": [
    {"producto_id": 2, "cantidad": 1, "utilidad": 30, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "producto_catalogo"},
    {"producto_id": null, "cantidad": 1, "utilidad": 25, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "producto_fantasma", "sku_libre": "FANT-001", "descripcion_libre": "Producto especial bajo pedido", "costo_unitario": 1500, "proveedor_sugerido_id": 1},
    {"producto_id": null, "cantidad": 8, "utilidad": 0, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "servicio", "descripcion_libre": "Programación PLC 8 hrs", "costo_unitario": 800}
  ],
  "observaciones": "test 3 tipos"
}')
QID=$(echo "$QUOTE" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT tipo_linea, sku_libre, cantidad, subtotal FROM detalles_orden WHERE orden_id=$QID;"
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT count(*) FROM movimientos_stock WHERE referencia_id=$QID AND tipo='reserva';"

# Limpieza
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "DELETE FROM movimientos_stock WHERE referencia_id=$QID; DELETE FROM detalles_orden WHERE orden_id=$QID; DELETE FROM ordenes_venta WHERE id=$QID;"
```

Expected: 3 rows con tipo_linea distintos; sólo 1 RESERVA (la del producto del catálogo).

- [ ] **Step 6.4: Commit**

```bash
git add app/routers/ventas.py
git commit -m "feat(cotizador): tipo_linea catalogo/fantasma/servicio + proveedor sugerido"
```

---

## Task 7 — Auto-OC service + endpoints

**Files:**
- Create: `app/services/auto_oc_service.py`
- Modify: `app/routers/ventas.py` (agregar 2 endpoints)
- Modify: `app/services/__init__.py`

- [ ] **Step 7.1: Crear `app/services/auto_oc_service.py`**

```python
"""Generación automática de OCs a partir de una cotización.

Reglas (ver spec):
- Producto del catálogo con stock_disponible < cantidad -> agrega faltante.
- Producto fantasma con proveedor_sugerido_id -> agrega.
- Servicio -> ignora.
- Agrupa por proveedor; 1 OC por proveedor estatus 'borrador', vinculada vía cotizacion_id.
- Productos catálogo sin proveedor principal/alterno -> warning, no se incluyen.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.services.stock_service import disponibilidad


def _proveedor_para_producto(p: "models.Producto") -> Optional[int]:
    return p.proveedor_principal_id or p.proveedor_alterno_id


def previsualizar_ocs(db: Session, cotizacion: "models.OrdenVenta") -> dict:
    por_proveedor: dict[int, dict] = {}
    sin_proveedor: list[dict] = []

    for d in cotizacion.detalles:
        if d.tipo_linea == "servicio":
            continue

        if d.producto_id and d.producto:
            disp = disponibilidad(db, d.producto)
            faltante = max(d.cantidad - max(disp["disponible"], 0), 0)
            if faltante == 0:
                continue
            prov_id = _proveedor_para_producto(d.producto)
            if not prov_id:
                sin_proveedor.append({
                    "producto_id": d.producto.id,
                    "sku": d.producto.sku_comercial or d.producto.sku,
                    "nombre": d.producto.nombre,
                    "faltante": faltante,
                })
                continue
            entry = {
                "producto_id": d.producto.id,
                "sku": d.producto.sku_comercial or d.producto.sku,
                "nombre": d.producto.nombre,
                "cantidad": faltante,
                "costo_unitario": float(d.producto.costo_compra or 0),
                "moneda": d.producto.moneda_compra or "MXN",
            }
        else:
            # Fantasma
            if not d.proveedor_sugerido_id:
                sin_proveedor.append({
                    "producto_id": None,
                    "sku": d.sku_libre,
                    "nombre": d.descripcion_libre,
                    "faltante": d.cantidad,
                })
                continue
            entry = {
                "producto_id": None,
                "sku": d.sku_libre,
                "nombre": d.descripcion_libre,
                "cantidad": d.cantidad,
                "costo_unitario": float(d.costo_base_linea or 0),
                "moneda": d.moneda_origen_linea or "MXN",
            }
            prov_id = d.proveedor_sugerido_id

        bucket = por_proveedor.setdefault(prov_id, {"proveedor_id": prov_id, "items": []})
        bucket["items"].append(entry)

    # Enriquecer con nombre proveedor
    for prov_id, b in por_proveedor.items():
        prov = db.get(models.Proveedor, prov_id)
        b["proveedor_empresa"] = prov.nombre_empresa if prov else None
        b["subtotal"] = round(sum(i["cantidad"] * i["costo_unitario"] for i in b["items"]), 2)

    return {
        "por_proveedor": list(por_proveedor.values()),
        "sin_proveedor": sin_proveedor,
        "total_proveedores": len(por_proveedor),
    }


def generar_ocs(
    db: Session,
    cotizacion: "models.OrdenVenta",
    usuario: Optional["models.Usuario"] = None,
) -> list[dict]:
    """Persiste OCs en estado borrador. Devuelve folios + ids."""
    from app.routers.compras import _generar_folio_oc

    preview = previsualizar_ocs(db, cotizacion)
    if preview["sin_proveedor"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Hay productos sin proveedor asignado. Asigna proveedor antes de generar OC.",
                "sin_proveedor": preview["sin_proveedor"],
            },
        )

    creadas = []
    for grupo in preview["por_proveedor"]:
        folio = _generar_folio_oc(db)
        moneda_grupo = grupo["items"][0]["moneda"] if grupo["items"] else "MXN"
        oc = models.OrdenCompra(
            folio=folio,
            proveedor_id=grupo["proveedor_id"],
            estatus="borrador",
            cotizacion_id=cotizacion.id,
            moneda=moneda_grupo,
            tipo_cambio=Decimal(str(cotizacion.tipo_cambio or 1)),
            total=Decimal(str(grupo["subtotal"])),
        )
        db.add(oc)
        db.flush()
        for it in grupo["items"]:
            if it["producto_id"]:
                db.add(models.DetalleCompra(
                    orden_compra_id=oc.id,
                    producto_id=it["producto_id"],
                    cantidad=it["cantidad"],
                    costo_unitario=Decimal(str(it["costo_unitario"])),
                ))
        creadas.append({"id": oc.id, "folio": folio, "proveedor_id": grupo["proveedor_id"], "items": len(grupo["items"]), "subtotal": grupo["subtotal"]})
    db.commit()
    return creadas
```

- [ ] **Step 7.2: Endpoints en `ventas.py`**

Agregar al final del file:

```python
@router.post("/{id}/sugerir-oc", dependencies=[Depends(allow_all_staff)])
def sugerir_oc(id: int, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")
    from app.services.auto_oc_service import previsualizar_ocs
    return previsualizar_ocs(db, orden)


@router.post("/{id}/generar-oc", dependencies=[Depends(allow_all_staff)])
def generar_oc_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden:
        raise HTTPException(404, "Cotización no encontrada")
    from app.services.auto_oc_service import generar_ocs
    return {"ocs": generar_ocs(db, orden, usuario=current_user)}
```

- [ ] **Step 7.3: Smoke test auto-OC**

Pre-condición: producto id=2 (GV2ME14) tiene stock=2. Asigna proveedor manualmente:

```bash
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "UPDATE productos SET proveedor_principal_id=1 WHERE id=2;"
```

Crear cotización que pida 5 unidades (3 faltantes):

```bash
QUOTE=$(curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/?tipo_orden=cotizacion" -H 'Content-Type: application/json' -d '{
  "cliente_id": 1, "moneda": "MXN", "tipo_cambio": 1,
  "detalles": [{"producto_id": 2, "cantidad": 5, "utilidad": 30, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "producto_catalogo"}],
  "observaciones": "test auto-OC"
}')
QID=$(echo "$QUOTE" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')

# Sugerir
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/$QID/sugerir-oc" | python3 -m json.tool

# Generar
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/$QID/generar-oc" | python3 -m json.tool

# Verifica OC creada vinculada
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT folio, estatus, proveedor_id, cotizacion_id FROM ordenes_compra WHERE cotizacion_id=$QID;"
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT producto_id, cantidad, costo_unitario FROM detalles_compra WHERE orden_compra_id IN (SELECT id FROM ordenes_compra WHERE cotizacion_id=$QID);"

# Limpieza
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "DELETE FROM detalles_compra WHERE orden_compra_id IN (SELECT id FROM ordenes_compra WHERE cotizacion_id=$QID); DELETE FROM ordenes_compra WHERE cotizacion_id=$QID; DELETE FROM movimientos_stock WHERE referencia_id=$QID; DELETE FROM detalles_orden WHERE orden_id=$QID; DELETE FROM ordenes_venta WHERE id=$QID;"
```

Expected: sugerir-oc devuelve `por_proveedor:[{proveedor_id:1, items:[{cantidad:3, ...}]}]`. generar-oc crea OC `OC-...` con `cotizacion_id=$QID`.

- [ ] **Step 7.4: Commit**

```bash
git add app/services/auto_oc_service.py app/services/__init__.py app/routers/ventas.py
git commit -m "feat(auto-oc): sugerir + generar OCs agrupadas por proveedor desde cotización"
```

---

## Task 8 — Frontend cotizador: TC autollenado + 3 tipos de línea

**Files:**
- Modify: `app/templates/cotizador.html` (significativo)

- [ ] **Step 8.1: Hero del cotizador — badge TC desde Banxico**

En la cabecera del cotizador (donde está el `<select id="select-moneda">` y `input-tc`), reemplazar el `input-tc` por:

```html
<div class="flex items-center gap-2">
  <label class="text-xs font-bold text-slate-500 uppercase">T.C.</label>
  <input type="number" id="input-tc" step="0.0001" min="0.0001" class="w-24 dax-input text-right">
  <span x-show="fxBadge.text" class="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 cursor-pointer"
        @click="recargarTC()" title="Click para recargar"
        x-text="fxBadge.text"></span>
</div>
```

Agregar al state `fxBadge: { text: '', fuente: '' }` y método:

```javascript
async function cargarTC() {
  try {
    const r = await fetch('/api/fx/usd-mxn', { credentials:'include' });
    if (!r.ok) return;
    const d = await r.json();
    state.tc = parseFloat(d.usd_mxn);
    document.getElementById('input-tc').value = state.tc.toFixed(4);
    state.fxBadge = { text: `${d.fuente} · ${d.fecha} · ${state.tc.toFixed(2)}`, fuente: d.fuente };
  } catch(e) { console.warn('FX:', e); }
}
async function recargarTC() {
  const r = await fetch('/api/fx/refresh', { method:'POST', credentials:'include' });
  if (r.ok) cargarTC();
}
```

Llamar `cargarTC()` en el `DOMContentLoaded` del cotizador, justo antes/después de `loadData()`.

- [ ] **Step 8.2: Tres botones de tipo de línea**

Donde está el botón "Agregar producto fantasma", reemplazar por una fila de 3 botones:

```html
<div class="grid grid-cols-3 gap-1 mt-2">
  <button type="button" @click="modoCatalogoFocus()" class="dax-btn-ghost text-[10px] py-1.5">+ Producto</button>
  <button type="button" @click="abrirModalServicio()" class="dax-btn-ghost text-[10px] py-1.5 hover:bg-cyan-500/10">+ Servicio</button>
  <button type="button" @click="abrirModalFantasma()" class="dax-btn-ghost text-[10px] py-1.5 hover:bg-amber-500/10">+ Fantasma</button>
</div>
```

`modoCatalogoFocus()` simplemente hace foco en `#buscador`.

- [ ] **Step 8.3: Modal servicio**

Agregar (similar al modal fantasma actual):

```html
<div id="modal-servicio" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
  <div class="dax-card w-full max-w-md p-5 space-y-3">
    <h3 class="text-base font-bold text-slate-200">Servicio</h3>
    <div>
      <label class="block text-xs font-semibold text-slate-400 uppercase">Descripción *</label>
      <input id="servicio-desc" placeholder="Ej. Programación PLC, instalación, capacitación" class="dax-input">
    </div>
    <div class="grid grid-cols-3 gap-2">
      <div>
        <label class="block text-xs font-semibold text-slate-400 uppercase">Tarifa</label>
        <input id="servicio-cost" type="number" min="0" step="0.01" value="0" class="dax-input text-right font-mono">
      </div>
      <div>
        <label class="block text-xs font-semibold text-slate-400 uppercase">Mon.</label>
        <select id="servicio-mon" class="dax-input"><option>MXN</option><option>USD</option></select>
      </div>
      <div>
        <label class="block text-xs font-semibold text-slate-400 uppercase">Cant./Hrs</label>
        <input id="servicio-qty" type="number" min="1" value="1" class="dax-input text-right font-mono">
      </div>
    </div>
    <div class="flex justify-end gap-2 pt-2">
      <button onclick="document.getElementById('modal-servicio').classList.add('hidden')" class="dax-btn-ghost">Cancelar</button>
      <button onclick="agregarServicio()" class="dax-btn-primary">Agregar</button>
    </div>
  </div>
</div>
```

```javascript
function abrirModalServicio() {
  document.getElementById('modal-servicio').classList.remove('hidden');
  document.getElementById('servicio-desc').focus();
}
function agregarServicio() {
  const desc = document.getElementById('servicio-desc').value.trim();
  const cost = parseFloat(document.getElementById('servicio-cost').value);
  const qty = parseInt(document.getElementById('servicio-qty').value) || 1;
  if (!desc || cost < 0) { Swal.fire({toast:true,position:'top-end',icon:'warning',title:'Falta descripción/tarifa', timer:1500, showConfirmButton:false}); return; }
  state.cart.push({
    id: null, ghost: true, servicio: true,
    sku: '— SERVICIO',
    nom: desc,
    cost, productCurrency: document.getElementById('servicio-mon').value,
    qty, max: 9999, utilidad: 0,
    tipoLinea: 'servicio',
  });
  document.getElementById('modal-servicio').classList.add('hidden');
  ['servicio-desc'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('servicio-cost').value=0; document.getElementById('servicio-qty').value=1;
  renderCart();
}
```

- [ ] **Step 8.4: Pasar `tipo_linea` al backend en `guardar()`**

En el método `guardar()`, dentro del map de detalles agregar:

```javascript
tipo_linea: i.tipoLinea || (i.ghost ? 'producto_fantasma' : 'producto_catalogo'),
proveedor_sugerido_id: i.proveedor_sugerido_id || null,
```

Para el modal fantasma, agregar campo proveedor sugerido (select con clientes/proveedores). Por ahora hardcoded a null si no se selecciona. Una iteración posterior agrega un selector de proveedores.

- [ ] **Step 8.5: Render carrito muestra badge servicio**

En el template `<tr>` del carrito, donde dice `<div class="font-bold text-slate-700 dark:text-slate-200 text-xs">${i.sku}${ghostBadge}</div>`, agregar:

```javascript
const servicioBadge = i.servicio ? '<span class="text-[9px] font-bold bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 px-1.5 py-0.5 rounded ml-1 uppercase">Servicio</span>' : '';
```

Y usar `${ghostBadge}${servicioBadge}` en el HTML.

- [ ] **Step 8.6: Smoke test browser-less**

```bash
# Verifica que la página renderiza
curl -s -b /tmp/dasic-cookies -o /tmp/cot.html -w "HTTP %{http_code}  bytes %{size_download}\n" "http://127.0.0.1:8001/ventas/cotizador"
grep -c "modal-servicio\|cargarTC\|tipo_linea\|abrirModalServicio" /tmp/cot.html
```

Expected: HTTP 200, ≥4 hits.

- [ ] **Step 8.7: Commit**

```bash
git add app/templates/cotizador.html
git commit -m "feat(cotizador): TC Banxico autollenado + 3 tipos de línea (catálogo/servicio/fantasma)"
```

---

## Task 9 — Frontend cotizador: badge stock + modal Sugerir OC

**Files:**
- Modify: `app/templates/cotizador.html`

- [ ] **Step 9.1: Cargar disponibilidad por producto al agregar al carrito**

Modificar `addCart(p)` para que guarde `disp` (disponibilidad), o usar el endpoint disponibilidad. Para no spamear, traer disponibilidad batch en `loadData()`:

```javascript
// Después de cargar productos, traer disponibilidad para los del carrito (lazy)
function dispBadgeColor(item) {
  if (!item.id || item.servicio || item.ghost) return '';
  // disponible aproximado del producto en state.prods
  const p = state.prods.find(x => x.id === item.id);
  if (!p) return 'bg-slate-700 text-slate-400';
  const disponible = (p.stock_actual || 0); // simplificado para MVP, reservas se calculan server-side
  if (disponible >= item.qty) return 'bg-emerald-500/20 text-emerald-300';
  // sin stock pero con proveedor asignado
  if (p.proveedor_principal_id) return 'bg-amber-500/20 text-amber-300';
  return 'bg-rose-500/20 text-rose-300';
}
function dispBadgeText(item) {
  if (!item.id || item.servicio || item.ghost) return '';
  const p = state.prods.find(x => x.id === item.id);
  if (!p) return '';
  return p.stock_actual + ' disp';
}
```

En el render del carrito agregar al lado del SKU:

```html
<span class="text-[9px] px-1.5 py-0.5 rounded ml-1" :class="dispBadgeColor(i)" x-text="dispBadgeText(i)"></span>
```

(Usar `${...}` en innerHTML porque el carrito es plain JS, no Alpine; ajustá el patrón existente.)

- [ ] **Step 9.2: Botón "Sugerir OC" en footer**

En el footer del carrito, junto a Guardar/Vender, agregar:

```html
<button onclick="abrirSugerirOC()" id="btn-sugerir-oc" class="dax-btn-ghost text-xs">
  <i class="fas fa-truck mr-1"></i> Sugerir OC
</button>
```

Sólo lo activamos cuando hay una cotización ya guardada (`state.lastSavedId`).

- [ ] **Step 9.3: Modal preview OC**

```html
<div id="modal-oc-preview" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
  <div class="dax-card w-full max-w-2xl p-5">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-base font-bold text-slate-200">Sugerencia de OCs</h3>
      <button onclick="document.getElementById('modal-oc-preview').classList.add('hidden')" class="dax-btn-ghost p-1"><i class="fas fa-xmark"></i></button>
    </div>
    <div id="oc-preview-body"></div>
    <div class="flex justify-end gap-2 mt-4">
      <button onclick="document.getElementById('modal-oc-preview').classList.add('hidden')" class="dax-btn-ghost">Cerrar</button>
      <button onclick="confirmarGenerarOC()" id="btn-confirmar-oc" class="dax-btn-primary">Generar OCs</button>
    </div>
  </div>
</div>
```

```javascript
async function abrirSugerirOC() {
  if (!state.lastSavedId) { Swal.fire('Guardá la cotización primero', '', 'info'); return; }
  const r = await fetch(`/api/ventas/${state.lastSavedId}/sugerir-oc`, { method:'POST', credentials:'include' });
  const d = await r.json();
  const body = document.getElementById('oc-preview-body');
  let html = '';
  if (d.sin_proveedor?.length) {
    html += `<div class="mb-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-200 text-xs">
      <p class="font-bold mb-1">Productos sin proveedor asignado (no se incluirán):</p>
      <ul class="ml-4 list-disc">${d.sin_proveedor.map(s=>`<li>${s.sku||'—'}: ${s.nombre} (faltan ${s.faltante})</li>`).join('')}</ul>
    </div>`;
  }
  d.por_proveedor.forEach(p => {
    html += `<div class="mb-3 p-3 rounded-lg bg-slate-700/40 border border-slate-600">
      <p class="text-xs font-bold text-slate-200">Proveedor: ${p.proveedor_empresa || ('#'+p.proveedor_id)}</p>
      <p class="text-[10px] text-slate-400 mb-1">Subtotal estimado: $${p.subtotal.toLocaleString('en-US',{minimumFractionDigits:2})}</p>
      <ul class="text-[11px] text-slate-300 ml-4 list-disc">${p.items.map(i=>`<li>${i.sku} × ${i.cantidad} @ $${i.costo_unitario}</li>`).join('')}</ul>
    </div>`;
  });
  if (!d.por_proveedor.length && !d.sin_proveedor.length) {
    html = '<p class="text-sm text-slate-400 text-center py-6">No hay faltantes; no se requiere generar OC.</p>';
  }
  body.innerHTML = html;
  document.getElementById('btn-confirmar-oc').disabled = !d.por_proveedor.length;
  document.getElementById('modal-oc-preview').classList.remove('hidden');
}

async function confirmarGenerarOC() {
  const r = await fetch(`/api/ventas/${state.lastSavedId}/generar-oc`, { method:'POST', credentials:'include' });
  const d = await r.json();
  if (r.ok) {
    document.getElementById('modal-oc-preview').classList.add('hidden');
    Swal.fire('OCs generadas', d.ocs.map(o=>o.folio).join(', '), 'success');
  } else {
    Swal.fire('Error', d.detail?.mensaje || JSON.stringify(d.detail), 'error');
  }
}
```

- [ ] **Step 9.4: Guardar `lastSavedId` después de crear**

En `guardar()`, donde se hace `Swal.fire(...)` con éxito, antes agregá `state.lastSavedId = d.id;`.

- [ ] **Step 9.5: Smoke test**

```bash
curl -s -b /tmp/dasic-cookies -o /tmp/cot2.html "http://127.0.0.1:8001/ventas/cotizador"
grep -c "modal-oc-preview\|abrirSugerirOC\|confirmarGenerarOC\|dispBadgeColor" /tmp/cot2.html
```

Expected: HTTP 200, ≥4 hits.

- [ ] **Step 9.6: Commit**

```bash
git add app/templates/cotizador.html
git commit -m "feat(cotizador): badge stock por línea + modal sugerir/generar OC"
```

---

## Task 10 — Frontend inventario: Disponible + side-panel + ajuste manual

**Files:**
- Modify: `app/templates/inventario.html`

- [ ] **Step 10.1: Columna `Disponible` y filtro nuevo**

En la tabla, agregar columna después de Stock:

```html
<th class="text-right">Disponible</th>
```

Y en cada `<tr>`:

```html
<td class="text-right font-mono font-bold text-xs"
    :class="(p.stock_actual||0) - (disponibilidad[p.id]?.reservado||0) <= 0 ? 'text-rose-400' : 'text-cyan-300'"
    x-text="(p.stock_actual||0) - (disponibilidad[p.id]?.reservado||0)"></td>
```

Agregar al state: `disponibilidad: {}` y método `cargarDisponibilidades()` que itera productos y llama `/api/inventario/disponibilidad/{id}` (o batch endpoint si lo agregamos).

- [ ] **Step 10.2: Side-panel timeline al click en fila**

Reemplazar `@click="abrirEdicion(p)"` por un click más rico que abre side-panel con timeline. Reutilizar el modal Editar como modo "ficha". Para timeline:

```html
<div id="side-panel-prod" x-show="sidePanel.open" x-cloak
     class="fixed inset-y-0 right-0 w-full max-w-md bg-slate-900 border-l border-slate-700 shadow-2xl z-40 overflow-y-auto custom-scroll"
     @click.outside.away="sidePanel.open=false">
  <div class="p-5 space-y-4">
    <div class="flex justify-between items-center">
      <h3 class="text-sm font-bold text-slate-200" x-text="sidePanel.producto.nombre"></h3>
      <button @click="sidePanel.open=false" class="dax-btn-ghost p-1"><i class="fas fa-xmark"></i></button>
    </div>
    <div class="grid grid-cols-3 gap-2 text-center">
      <div class="rounded bg-slate-800 p-2">
        <p class="text-[9px] uppercase text-slate-500">Físico</p>
        <p class="text-lg font-bold text-slate-200" x-text="sidePanel.disp.stock_actual"></p>
      </div>
      <div class="rounded bg-amber-500/10 p-2">
        <p class="text-[9px] uppercase text-amber-300">Reservado</p>
        <p class="text-lg font-bold text-amber-200" x-text="sidePanel.disp.reservado"></p>
      </div>
      <div class="rounded bg-cyan-500/10 p-2">
        <p class="text-[9px] uppercase text-cyan-300">Disponible</p>
        <p class="text-lg font-bold text-cyan-200" x-text="sidePanel.disp.disponible"></p>
      </div>
    </div>
    <div>
      <p class="text-[10px] uppercase text-slate-500 font-bold mb-2">Movimientos (30d)</p>
      <div class="space-y-1.5 text-[11px]">
        <template x-for="m in sidePanel.movs" :key="m.id">
          <div class="flex justify-between items-center rounded px-2 py-1 hover:bg-slate-800">
            <div>
              <span class="font-bold uppercase" :class="movClass(m.tipo)" x-text="m.tipo"></span>
              <span class="text-slate-500 ml-1" x-text="m.referencia_tipo + (m.referencia_id ? ' #' + m.referencia_id : '')"></span>
            </div>
            <div class="font-mono">
              <span :class="m.cantidad>0?'text-emerald-300':'text-rose-300'" x-text="(m.cantidad>0?'+':'')+m.cantidad"></span>
              <span class="text-slate-500 ml-1" x-text="'→ '+m.stock_resultante"></span>
            </div>
          </div>
        </template>
        <p x-show="!sidePanel.movs.length" class="text-slate-500 text-center py-3">Sin movimientos en 30 días.</p>
      </div>
    </div>
    <div class="pt-2 border-t border-slate-700">
      <button @click="abrirAjusteManual(sidePanel.producto)" class="dax-btn-ghost text-xs w-full">
        <i class="fas fa-pen-to-square mr-1"></i> Ajuste manual
      </button>
    </div>
  </div>
</div>
```

```javascript
sidePanel: { open:false, producto:{}, disp:{}, movs:[] },
async abrirSidePanel(p) {
  this.sidePanel.producto = p;
  this.sidePanel.disp = { stock_actual:0, reservado:0, disponible:0 };
  this.sidePanel.movs = [];
  this.sidePanel.open = true;
  const [d, m] = await Promise.all([
    fetch(`/api/inventario/disponibilidad/${p.id}`, {credentials:'include'}).then(r=>r.json()),
    fetch(`/api/inventario/movimientos?producto_id=${p.id}&dias=30`, {credentials:'include'}).then(r=>r.json()),
  ]);
  this.sidePanel.disp = d;
  this.sidePanel.movs = m;
},
movClass(tipo) {
  return ({entrada:'text-emerald-300', salida:'text-rose-300', ajuste:'text-amber-300', reserva:'text-cyan-300', liberacion:'text-slate-300'})[tipo] || 'text-slate-300';
},
```

Cambiá `@click="abrirEdicion(p)"` en alguna acción (o doble click en la fila) para que dispare `abrirSidePanel(p)`.

- [ ] **Step 10.3: Modal ajuste manual con motivo**

```html
<div id="modal-ajuste" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
  <div class="dax-card w-full max-w-sm p-5 space-y-3" x-data="{ delta:0, motivo:'' }">
    <h3 class="text-base font-bold text-slate-200">Ajuste manual</h3>
    <p class="text-[10px] text-slate-500" x-text="ajuste.producto?.nombre"></p>
    <div>
      <label class="block text-xs font-semibold text-slate-400 uppercase">Cantidad (+entrada, -salida)</label>
      <input type="number" x-model.number="delta" class="dax-input text-right font-mono">
    </div>
    <div>
      <label class="block text-xs font-semibold text-slate-400 uppercase">Motivo *</label>
      <input type="text" x-model="motivo" placeholder="Ej. conteo físico Q2, daño, devolución" class="dax-input">
    </div>
    <div class="flex justify-end gap-2 pt-1">
      <button onclick="document.getElementById('modal-ajuste').classList.add('hidden')" class="dax-btn-ghost">Cancelar</button>
      <button @click="guardarAjuste(delta, motivo); delta=0; motivo=''" class="dax-btn-primary">Aplicar</button>
    </div>
  </div>
</div>
```

```javascript
ajuste: { producto: null },
abrirAjusteManual(p) { this.ajuste.producto = p; document.getElementById('modal-ajuste').classList.remove('hidden'); },
async guardarAjuste(delta, motivo) {
  if (!motivo || motivo.trim().length < 3) { Swal.fire('Falta motivo','','warning'); return; }
  const r = await fetch('/api/inventario/movimientos', {
    method:'POST', credentials:'include', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({producto_id: this.ajuste.producto.id, cantidad: delta, motivo}),
  });
  if (r.ok) {
    document.getElementById('modal-ajuste').classList.add('hidden');
    await this.init(); // recarga
    if (this.sidePanel.open) await this.abrirSidePanel(this.ajuste.producto);
  } else {
    const e = await r.json();
    Swal.fire('Error', e.detail || 'No se pudo aplicar el ajuste', 'error');
  }
},
```

- [ ] **Step 10.4: Smoke test inventario**

```bash
curl -s -b /tmp/dasic-cookies -o /tmp/inv2.html "http://127.0.0.1:8001/inventario"
grep -c "side-panel-prod\|modal-ajuste\|abrirAjusteManual\|abrirSidePanel\|disponibilidad" /tmp/inv2.html
```

Expected: HTTP 200, ≥5 hits.

- [ ] **Step 10.5: Commit**

```bash
git add app/templates/inventario.html
git commit -m "feat(inventario): columna Disponible + side-panel timeline + ajuste manual con motivo"
```

---

## Task 11 — Seeds + docs

**Files:**
- Modify: `scripts/import_context_data.py`
- Modify: `CLAUDE.md`
- Modify: `.env.example`

- [ ] **Step 11.1: Asignar proveedor_principal a productos en el script**

En `scripts/import_context_data.py`, antes de upsert_productos buscamos al proveedor "Dimeint" (el único que tenemos sembrado) y lo usamos como default para los productos que tengan marca "Allen Bradley" / "AUTOMATIONDIRECT" (que son del rubro de Dimeint). Resto sin proveedor.

```python
def _proveedor_default(db) -> "models.Proveedor | None":
    return db.query(models.Proveedor).filter(models.Proveedor.email == "aramirez@dimeint.com").first()


def upsert_productos(db, items, dry_run):
    prov = _proveedor_default(db)
    ...
    for it in items:
        ...
        # asignar proveedor para marcas conocidas que el script considera "del rubro Dimeint"
        marca_upper = (it["marca"] or "").upper()
        if prov and marca_upper in {"ALLEN BRADLEY", "AUTOMATIONDIRECT"}:
            if existing and not existing.proveedor_principal_id:
                existing.proveedor_principal_id = prov.id
            elif not existing:
                # set en el constructor del nuevo Producto
                ...
```

Aplicar al constructor `models.Producto(...)`:

```python
proveedor_principal_id=prov.id if (prov and marca_upper in {"ALLEN BRADLEY", "AUTOMATIONDIRECT"}) else None,
```

- [ ] **Step 11.2: Re-correr el script**

```bash
set -a && . ./.env && set +a && .venv/bin/python scripts/import_context_data.py 2>&1 | tail -10
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT sku, marca, proveedor_principal_id FROM productos ORDER BY id;"
```

Expected: productos Allen Bradley / AutomationDirect con `proveedor_principal_id=1`.

- [ ] **Step 11.3: `.env.example` + `CLAUDE.md`**

A `.env.example` agregar al final:

```
# Banxico (opcional). Token gratis tras registro en
# https://www.banxico.org.mx/SieAPIRest/service/v1/token/registro
BANXICO_TOKEN=
```

A `CLAUDE.md`, en la sección "Required env vars", documentar `BANXICO_TOKEN` como opcional con la nota del fallback.

- [ ] **Step 11.4: Commit**

```bash
git add scripts/import_context_data.py CLAUDE.md .env.example
git commit -m "chore: seed proveedor_principal por marca + doc BANXICO_TOKEN"
```

---

## Task 12 — Smoke end-to-end + push

**Files:** ninguno nuevo

- [ ] **Step 12.1: Login + estado inicial**

```bash
curl -s -c /tmp/dasic-cookies -X POST http://127.0.0.1:8001/api/auth/login -d 'username=admin@dasic.com&password=admin123' -H 'Content-Type: application/x-www-form-urlencoded' > /dev/null
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/inventario/disponibilidad/2" | python3 -m json.tool
```

Expected: `stock_actual=2, reservado=0, disponible=2`.

- [ ] **Step 12.2: Crear cotización mixta de 3 líneas**

```bash
QUOTE=$(curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/?tipo_orden=cotizacion" -H 'Content-Type: application/json' -d '{
  "cliente_id": 1, "moneda": "MXN", "tipo_cambio": 17.45,
  "detalles": [
    {"producto_id": 2, "cantidad": 5, "utilidad": 30, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "producto_catalogo"},
    {"producto_id": null, "cantidad": 2, "utilidad": 25, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "producto_fantasma", "sku_libre": "FANT-X1", "descripcion_libre": "Sensor especial bajo pedido", "costo_unitario": 2500, "proveedor_sugerido_id": 1},
    {"producto_id": null, "cantidad": 8, "utilidad": 0, "descuento": 0, "moneda_origen": "MXN", "tipo_linea": "servicio", "descripcion_libre": "Programación PLC 8 hrs", "costo_unitario": 800}
  ],
  "observaciones": "smoke E2E"
}')
QID=$(echo "$QUOTE" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "Folio: $(echo $QUOTE | python3 -c 'import sys,json;print(json.load(sys.stdin)["folio"])')"
```

Expected: folio `C-...`, JSON sin error.

- [ ] **Step 12.3: Verifica reservas y disponibilidad**

```bash
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/inventario/disponibilidad/2" | python3 -m json.tool
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT tipo, cantidad FROM movimientos_stock WHERE referencia_id=$QID ORDER BY id;"
```

Expected: disponible=−3 (stock 2, reservado 5); 1 RESERVA(+5).

- [ ] **Step 12.4: Sugerir + generar OC**

```bash
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/$QID/sugerir-oc" | python3 -m json.tool
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/$QID/generar-oc" | python3 -m json.tool
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT folio, proveedor_id, total FROM ordenes_compra WHERE cotizacion_id=$QID;"
```

Expected: 1 OC (proveedor Dimeint) con dos partidas (3 unidades GV2ME14 faltantes + 2 FANT-X1).

- [ ] **Step 12.5: Cancelar y verificar liberación**

```bash
curl -s -b /tmp/dasic-cookies -X POST "http://127.0.0.1:8001/api/ventas/$QID/cancelar" | python3 -m json.tool
curl -s -b /tmp/dasic-cookies "http://127.0.0.1:8001/api/inventario/disponibilidad/2" | python3 -m json.tool
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "SELECT tipo, cantidad FROM movimientos_stock WHERE referencia_id=$QID ORDER BY id;"
```

Expected: cot estatus CANCELADA; disponible vuelve a 2; movimientos muestran RESERVA(+5) + LIBERACION(-5).

- [ ] **Step 12.6: Limpieza**

```bash
PGPASSWORD=toor psql -h localhost -U postgres -d dasi_crm_local -c "DELETE FROM detalles_compra WHERE orden_compra_id IN (SELECT id FROM ordenes_compra WHERE cotizacion_id=$QID); DELETE FROM ordenes_compra WHERE cotizacion_id=$QID; DELETE FROM movimientos_stock WHERE referencia_id=$QID; DELETE FROM detalles_orden WHERE orden_id=$QID; DELETE FROM ordenes_venta WHERE id=$QID;"
```

- [ ] **Step 12.7: Push final**

```bash
git push origin main
```

---

## Criterios de listo

- [ ] Migración `20260430_01` aplicada sin errores; `\d productos`, `\d detalles_orden`, `\dt movimientos_stock`, `\dt tipos_cambio_dia` confirman estructura.
- [ ] `GET /api/fx/usd-mxn` devuelve 200 con TC del día y queda cacheado.
- [ ] `POST /api/ventas/` con producto del catálogo crea row `RESERVA` en `movimientos_stock`.
- [ ] `POST /api/ventas/{id}/convertir` transforma RESERVA→SALIDA y baja `stock_actual`.
- [ ] `POST /api/ventas/{id}/cancelar` libera reservas y deja LIBERACION en timeline.
- [ ] `POST /api/ventas/{id}/sugerir-oc` agrupa por proveedor; `generar-oc` persiste OCs en borrador vinculadas vía `cotizacion_id`.
- [ ] Cotizador frontend: badge `Banxico/EXCHANGERATE · fecha · valor`; 3 botones de tipo de línea; modal Servicio + Fantasma; carrito muestra badges; modal "Sugerir OC" funcional.
- [ ] Inventario frontend: columna `Disponible`; click en producto abre side-panel con tres KPIs (Físico/Reservado/Disponible) y timeline 30d; modal ajuste manual con motivo obligatorio.
- [ ] `scripts/import_context_data.py` asigna `proveedor_principal_id` a marcas Allen Bradley / AutomationDirect.
- [ ] `.env.example` y `CLAUDE.md` documentan `BANXICO_TOKEN` como opcional.
- [ ] Push a `main` ejecutado.
