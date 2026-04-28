# Fase 0 — Strip multi-tenant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar todo el scaffolding multi-tenant (`Organization`, `Branch`, `UserOrganization`, `organization_id`, header `X-Organization-ID`, ContextVar de tenant, claims `org_id`/`branch_id`) del código y del schema. Single-tenant implícito.

**Architecture:** Refactor por capas: primero rutas (consumidores), luego dependencias y schemas, luego seeds, luego modelos, finalmente migración Alembic que dropea columnas y tablas. Cada commit deja la app funcional.

**Tech Stack:** FastAPI · SQLAlchemy 2.x · Alembic · PostgreSQL · pytest (smoke tests opcionales en Task 11)

**Spec:** `docs/superpowers/specs/2026-04-28-mvp-dasic-design.md` §3

---

## File map

**Files to modify:**
- `app/routers/auth.py` — remove membership lookup; emit JWT sin `org_id`/`branch_id`
- `app/routers/clientes.py` — remove `Depends(get_current_active_organization)` + filtros
- `app/routers/dashboard.py` — same
- `app/routers/ventas.py` — same (mayor cantidad de ocurrencias)
- `app/core/__init__.py` — remove tenant context exports
- `app/schemas/auth.py` — remove `org_id`/`branch_id` de `TokenData`
- `app/db/seeds.py` — quitar todo lo de tenant, dejar solo `seed_super_admin`
- `app/models/__init__.py` — quitar exports de `Organization`/`Branch`/`UserOrganization`/`BranchType`
- `app/models/enums.py` — eliminar `BranchType`
- `app/models/users.py` — quitar relationship `memberships`
- `app/models/clients.py`, `finance.py`, `sales.py`, `quote_events.py` — quitar columna `organization_id`

**Files to delete:**
- `app/core/context.py`
- `app/dependencies.py` (queda vacío tras quitar `get_current_active_organization`; verificar si tiene otros usos antes de borrar)
- `app/models/nucleus.py`
- `scripts/bootstrap_tenant.py`

**Files to create:**
- `migrations/versions/20260429_01_drop_multitenant.py` — drop columnas + drop tablas

**Out of touch (leave as-is):**
- `app/models/users.py::Usuario` keeps everything except the `memberships` relationship
- Históricos de migraciones (`migrations/versions/2026042[8]_*.py`) no se editan

---

## Parallelization map

```
Sequential prerequisite (tasks 1-4): routers cleanup
  ├── Task 1: auth.py     ┐
  ├── Task 2: clientes.py ├── PARALLELIZABLE — different files, no shared edits
  ├── Task 3: dashboard.py┤
  └── Task 4: ventas.py   ┘

Sequential prerequisite (tasks 5-7): dependencies + schemas + seeds
  ├── Task 5: app/dependencies.py + app/core/*  ┐
  ├── Task 6: app/schemas/auth.py               ├── PARALLELIZABLE
  └── Task 7: app/db/seeds.py                   ┘

Sequential after tasks 5-7 (task 8): models cleanup — single subagent (entrelazado)

Sequential after task 8 (tasks 9-11): scripts + alembic + smoke
  ├── Task 9 + 10: scripts cleanup + alembic migration  (mismo subagente, secuenciales)
  └── Task 11: smoke test (manual o subagente final)
```

When dispatching parallel agents, the orchestrator MUST run all four router cleanups (1-4) and let them merge before moving to tasks 5+. Within each batch, conflicts are zero because each task touches distinct files.

---

## Task 1: Strip multi-tenant logic from `app/routers/auth.py`

**Files:**
- Modify: `app/routers/auth.py`

- [ ] **Step 1: Replace login flow — remove membership lookup, simplify JWT claims**

Current `login_for_access_token` queries `UserOrganization` and adds `org_id`/`branch_id` to JWT. Replace lines 31-55 of `app/routers/auth.py` with this simplified body:

```python
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "rol": user.rol.value,
        },
        expires_delta=access_token_expires,
    )
```

Resulting file (full content):

```python
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core import get_settings
from app.db import get_db
from app import schemas
from app.services import UserService
from app.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])
settings = get_settings()


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = UserService.get_user_by_email(db, form_data.username)
    if not user or not UserService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrecto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "rol": user.rol.value,
        },
        expires_delta=access_token_expires,
    )

    response.set_cookie(
        key=settings.token_cookie_name,
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=settings.cookie_secure,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.token_cookie_name)
    return {"ok": True}
```

Note: `from app import models` se elimina porque ya no se usa.

- [ ] **Step 2: Verify import + syntax**

Run: `python -m py_compile app/routers/auth.py`
Expected: no output (success).

- [ ] **Step 3: Commit**

```bash
git add app/routers/auth.py
git commit -m "refactor(auth): strip org_id/branch_id from JWT claims"
```

---

## Task 2: Strip multi-tenant from `app/routers/clientes.py`

**Files:**
- Modify: `app/routers/clientes.py`

- [ ] **Step 1: Remove import**

Delete the line `from app.dependencies import get_current_active_organization` near the top of the file.

- [ ] **Step 2: Remove `organization_id` parameter from every endpoint signature**

Wherever a function has `organization_id: str = Depends(get_current_active_organization),` as a parameter, delete that line entirely. Endpoints affected (per `git grep`): lines around 22, 41, 68, 87, 124, 260.

- [ ] **Step 3: Remove `organization_id` filters from all queries**

Replace every occurrence of pattern `models.Cliente.organization_id == organization_id,` and `models.TransaccionCliente.organization_id == organization_id,` with nothing (delete the line, including trailing comma if it leaves a dangling comma; check the surrounding `.filter(...)` chain for orphaned `,` or empty filters).

If a `.filter(...)` clause becomes empty (e.g., the org check was the only filter), remove the `.filter()` call entirely.

- [ ] **Step 4: Remove `organization_id=...` from model constructors**

Pattern: `nuevo_cliente = models.Cliente(**cliente.model_dump(), organization_id=organization_id)` → `nuevo_cliente = models.Cliente(**cliente.model_dump())`. Same for `models.TransaccionCliente(...)` if present. Check line 149 specifically.

- [ ] **Step 5: Verify**

```bash
python -m py_compile app/routers/clientes.py
git grep -n 'organization_id\|get_current_active_organization' app/routers/clientes.py
```

Expected first command: silent. Expected second command: zero results.

- [ ] **Step 6: Commit**

```bash
git add app/routers/clientes.py
git commit -m "refactor(clientes): drop organization_id scoping"
```

---

## Task 3: Strip multi-tenant from `app/routers/dashboard.py`

**Files:**
- Modify: `app/routers/dashboard.py`

- [ ] **Step 1: Remove import**

Delete `from app.dependencies import get_current_active_organization`.

- [ ] **Step 2: Remove `organization_id` parameter from endpoint signatures**

Lines ~23. Delete the dependency parameter.

- [ ] **Step 3: Remove `organization_id` filters from queries**

Affected lines per grep: 32, 50, 60, 88, 100. Same pattern as Task 2 — delete the `.filter()` arg or the entire `.filter()` chain if it's now empty. Also remove the comment at line 67 (`# OC (no scoping por organization_id...)`) — it's no longer relevant.

- [ ] **Step 4: Verify**

```bash
python -m py_compile app/routers/dashboard.py
git grep -n 'organization_id\|get_current_active_organization' app/routers/dashboard.py
```

Expected: silent + zero.

- [ ] **Step 5: Commit**

```bash
git add app/routers/dashboard.py
git commit -m "refactor(dashboard): drop organization_id scoping"
```

---

## Task 4: Strip multi-tenant from `app/routers/ventas.py`

**Files:**
- Modify: `app/routers/ventas.py`

This is the largest file (~1000 lines, ~30 occurrences). Take it in slices.

- [ ] **Step 1: Remove import**

Delete `from app.dependencies import get_current_active_organization`.

- [ ] **Step 2: Update `_generar_folio` signature**

Current signature (line 38):
```python
def _generar_folio(
    db: Session,
    organization_id: str,
    tipo_orden: "models.EstatusOrden",
    vendedor: "models.Usuario",
) -> str:
```

New signature:
```python
def _generar_folio(
    db: Session,
    tipo_orden: "models.EstatusOrden",
    vendedor: "models.Usuario",
) -> str:
```

Inside the function, remove the line `models.OrdenVenta.organization_id == organization_id,` from the consecutivo `.filter(...)`.

Update both call sites in this same file:
- Line 283: `folio = _generar_folio(db, organization_id, tipo_orden, current_user)` → `folio = _generar_folio(db, tipo_orden, current_user)`
- Line 526: `folio_nuevo = _generar_folio(db, organization_id, models.EstatusOrden.COTIZACION, current_user)` → `folio_nuevo = _generar_folio(db, models.EstatusOrden.COTIZACION, current_user)`

- [ ] **Step 3: Strip every endpoint dependency parameter**

For each endpoint signature that contains `organization_id: str = Depends(get_current_active_organization),`, delete the line. Lines per grep: 265, 395, 496, 570, 612, 659, 690, 733, 815, 884, 918, 960. Use `git grep -n 'Depends(get_current_active_organization)' app/routers/ventas.py` to confirm zero remain.

- [ ] **Step 4: Strip `.filter(... organization_id == organization_id ...)`**

Affected query filter lines per grep: 54 (inside `_generar_folio`, already done in Step 2), 272, 401, 424, 505, 519, 576, 588, 618, 663, 696, 739, 822, 891, 925, 966, 977. For each: delete the `models.X.organization_id == organization_id,` line. If the `.filter()` clause becomes empty as a result, remove it entirely.

- [ ] **Step 5: Strip `organization_id=organization_id` from constructors**

Affected per grep: 286, 352, 372, 469, 530, 548, 640, 856, 900, 937. Pattern: `models.OrdenVenta(... organization_id=organization_id, ...)` → remove that kwarg. Same for `models.DetalleOrden`, `models.TransaccionCliente`, `models.QuoteEvent`.

- [ ] **Step 6: Verify**

```bash
python -m py_compile app/routers/ventas.py
git grep -n 'organization_id\|get_current_active_organization' app/routers/ventas.py
```

Expected: silent + zero.

- [ ] **Step 7: Commit**

```bash
git add app/routers/ventas.py
git commit -m "refactor(ventas): drop organization_id scoping"
```

---

## Task 5: Delete dependencies + core context

**Files:**
- Delete: `app/dependencies.py`
- Delete: `app/core/context.py`
- Modify: `app/core/__init__.py`

- [ ] **Step 1: Verify nothing else imports from `app.dependencies`**

```bash
git grep -n 'from app.dependencies\|import dependencies' app/
```

Expected: zero results (the only reference was in routers cleaned in Tasks 2-4). If results show, fix those callers BEFORE proceeding.

- [ ] **Step 2: Delete the file**

```bash
git rm app/dependencies.py
```

- [ ] **Step 3: Delete `app/core/context.py`**

```bash
git rm app/core/context.py
```

- [ ] **Step 4: Update `app/core/__init__.py`**

Replace the entire file with:

```python
from app.core.config import Settings, get_settings, normalize_database_url

__all__ = [
    "Settings",
    "get_settings",
    "normalize_database_url",
]
```

- [ ] **Step 5: Verify**

```bash
python -m py_compile app/core/__init__.py
python -c "from app.main import app; print('OK')"
```

Expected: silent + `OK`.

- [ ] **Step 6: Commit**

```bash
git add app/core/__init__.py
git commit -m "refactor(core): remove tenant ContextVar and dependencies module"
```

---

## Task 6: Strip tenant claims from `app/schemas/auth.py`

**Files:**
- Modify: `app/schemas/auth.py`

- [ ] **Step 1: Remove `org_id` and `branch_id` from `TokenData`**

Replace the `TokenData` class (current lines 16-27) with:

```python
class TokenData(BaseModel):
    username: Optional[str] = None
    rol: Optional[RolUsuario] = None

    @field_validator("rol", mode="before")
    @classmethod
    def normalize_role(cls, value: RolUsuario | str | None) -> RolUsuario | None:
        if value is None:
            return None
        return RolUsuario.from_input(value)
```

- [ ] **Step 2: Verify**

```bash
python -m py_compile app/schemas/auth.py
git grep -n 'org_id\|branch_id' app/schemas/
```

Expected: silent + zero.

- [ ] **Step 3: Commit**

```bash
git add app/schemas/auth.py
git commit -m "refactor(schemas): drop org_id/branch_id from TokenData"
```

---

## Task 7: Simplify seeds

**Files:**
- Modify: `app/db/seeds.py`

- [ ] **Step 1: Replace entire file with minimal version**

```python
"""
Database seeding.

Single-tenant: solo crea el usuario administrador inicial si la tabla está vacía.
"""

import logging

from sqlalchemy.orm import Session

from app import models
from app.schemas import UsuarioCreate
from app.services import UserService

logger = logging.getLogger(__name__)


def seed_super_admin(db: Session) -> None:
    """Crea el usuario administrador inicial si no existe ningún usuario."""
    if db.query(models.Usuario).first():
        logger.info("DASIC ERP online")
        return

    logger.info("Inicializando sistema DASIC ERP — creando administrador...")
    admin = UsuarioCreate(
        nombre="Administrador Principal",
        email="admin@dasic.com",
        password="admin123",
        rol=models.RolUsuario.ADMIN,
        activo=True,
    )
    UserService.create_user(db, admin)
    logger.info("Admin creado: admin@dasic.com / admin123")


def run_all_seeds(db: Session) -> None:
    """Punto de entrada único para tareas de startup."""
    seed_super_admin(db)
    logger.info("Startup completado correctamente.")
```

- [ ] **Step 2: Verify**

```bash
python -m py_compile app/db/seeds.py
git grep -n 'organization_id\|Organization\|Branch\|UserOrganization\|BranchType' app/db/seeds.py
```

Expected: silent + zero.

- [ ] **Step 3: Commit**

```bash
git add app/db/seeds.py
git commit -m "refactor(seeds): drop tenant seeding, keep only admin bootstrap"
```

---

## Task 8: Strip `organization_id` from domain models + delete nucleus

**Files:**
- Modify: `app/models/clients.py`
- Modify: `app/models/finance.py`
- Modify: `app/models/sales.py`
- Modify: `app/models/quote_events.py`
- Modify: `app/models/users.py`
- Modify: `app/models/enums.py`
- Modify: `app/models/__init__.py`
- Delete: `app/models/nucleus.py`

This task can be split across **multiple parallel subagents** by file (sub-tasks 8a-8h are independent).

- [ ] **Step 1: `app/models/clients.py` — drop column from `Cliente`**

Delete line 15:
```python
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
```

Also adjust the import line to remove `ForeignKey` if no other column uses it. In this file, `Cliente` no longer uses `ForeignKey` after the change — but `Proveedor` doesn't use it either. Final imports:

```python
from sqlalchemy import Column, DECIMAL, Integer, String, Text
from sqlalchemy.orm import relationship
```

(Removes `ForeignKey` since neither model uses it — `relationship` is still used.)

- [ ] **Step 2: `app/models/finance.py` — drop column from `TransaccionCliente`**

Delete line 17:
```python
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
```

`ForeignKey` is still used elsewhere in this file (cliente_id, proveedor_id), keep import.

- [ ] **Step 3: `app/models/sales.py` — drop column from `OrdenVenta` and `DetalleOrden`**

Delete line 17 (OrdenVenta) and line 52 (DetalleOrden):
```python
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
```

Keep `ForeignKey` import (used by other columns).

- [ ] **Step 4: `app/models/quote_events.py` — drop column from `QuoteEvent`**

Delete line 16:
```python
    organization_id = Column(String(36), nullable=True, index=True)
```

- [ ] **Step 5: `app/models/users.py` — drop `memberships` relationship**

Delete line 26:
```python
    memberships = relationship("UserOrganization", back_populates="user")
```

- [ ] **Step 6: `app/models/enums.py` — remove `BranchType`**

Delete lines 79-83 (the entire `BranchType` class and trailing blank line).

- [ ] **Step 7: Delete `app/models/nucleus.py`**

```bash
git rm app/models/nucleus.py
```

- [ ] **Step 8: Update `app/models/__init__.py`**

Replace entire file with:

```python
"""
ORM models — re-export central.

Import de aquí para compatibilidad con el código existente.
Modelos organizados por dominio:

  enums.py      → RolUsuario, EstatusOrden, TipoMovimiento
  users.py      → Usuario
  catalog.py    → Producto, Promocion
  clients.py    → Cliente, Proveedor
  finance.py    → TransaccionCliente, TransaccionProveedor
  sales.py      → OrdenVenta, DetalleOrden
  purchases.py  → OrdenCompra, DetalleCompra
  quote_events.py → QuoteEvent
"""

from app.db import Base  # noqa: F401

from app.models.enums import (  # noqa: F401
    RolUsuario,
    EstatusOrden,
    TipoMovimiento,
)
from app.models.users import Usuario  # noqa: F401
from app.models.catalog import Producto, Promocion  # noqa: F401
from app.models.clients import Cliente, Proveedor  # noqa: F401
from app.models.finance import (  # noqa: F401
    TransaccionCliente,
    TransaccionProveedor,
)
from app.models.sales import OrdenVenta, DetalleOrden  # noqa: F401
from app.models.purchases import OrdenCompra, DetalleCompra  # noqa: F401
from app.models.quote_events import QuoteEvent  # noqa: F401

__all__ = [
    "Base",
    "RolUsuario", "EstatusOrden", "TipoMovimiento",
    "Usuario",
    "Producto", "Promocion",
    "Cliente", "Proveedor",
    "TransaccionCliente", "TransaccionProveedor",
    "OrdenVenta", "DetalleOrden",
    "OrdenCompra", "DetalleCompra",
    "QuoteEvent",
]
```

- [ ] **Step 9: Verify**

```bash
python -c "from app.main import app; print('OK')"
git grep -nE 'Organization|Branch|UserOrganization|BranchType' app/ | grep -v 'migrations/'
```

Expected: `OK` + only references inside `migrations/versions/` (history is preserved).

- [ ] **Step 10: Commit**

```bash
git add app/models/
git commit -m "refactor(models): drop organization_id columns and nucleus module"
```

---

## Task 9: Delete bootstrap script

**Files:**
- Delete: `scripts/bootstrap_tenant.py`

- [ ] **Step 1: Verify no callers**

```bash
git grep -n 'bootstrap_tenant' .
```

Expected: only references inside `scripts/bootstrap_tenant.py` itself (no imports from elsewhere).

- [ ] **Step 2: Delete**

```bash
git rm scripts/bootstrap_tenant.py
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove bootstrap_tenant script"
```

---

## Task 10: Alembic migration — drop columns and nucleus tables

**Files:**
- Create: `migrations/versions/20260429_01_drop_multitenant.py`

- [ ] **Step 1: Determine the previous revision id**

Run: `ls migrations/versions/ | sort | tail -5`
Open the most recent file (`20260428_04_quote_events.py`) and read its `revision = "..."` line. Copy that value as the `down_revision` of the new migration. Record both:

```bash
grep '^revision' migrations/versions/20260428_04_quote_events.py
```

Expected output is something like `revision = "20260428_04"`. Use that exact string as `down_revision` below.

- [ ] **Step 2: Write the migration file**

Create `migrations/versions/20260429_01_drop_multitenant.py`:

```python
"""drop multi-tenant scaffolding (organization_id + nucleus tables)

Revision ID: 20260429_01
Revises: 20260428_04
Create Date: 2026-04-29
"""
from alembic import op


revision = "20260429_01"
down_revision = "20260428_04"  # <-- replace if Step 1 showed a different value
branch_labels = None
depends_on = None


# Tablas que tenían organization_id (FK a organizations) + sus índices.
_TENANT_COLUMNS = [
    ("clientes", "ix_clientes_organization_id"),
    ("transacciones_clientes", "ix_transacciones_clientes_organization_id"),
    ("ordenes_venta", "ix_ordenes_venta_organization_id"),
    ("detalles_orden", "ix_detalles_orden_organization_id"),
    ("quote_events", "ix_quote_events_organization_id"),
]


def upgrade() -> None:
    # 1. Drop columns organization_id de cada tabla referente.
    for table, index_name in _TENANT_COLUMNS:
        op.execute(f"DROP INDEX IF EXISTS {index_name}")
        op.execute(f"ALTER TABLE IF EXISTS {table} DROP COLUMN IF EXISTS organization_id")

    # 2. Drop tablas nucleus (orden por dependencia FK).
    op.execute("DROP TABLE IF EXISTS user_organizations CASCADE")
    op.execute("DROP TABLE IF EXISTS branches CASCADE")
    op.execute("DROP TABLE IF EXISTS organizations CASCADE")


def downgrade() -> None:
    # No-op: la fase de strip es one-way. Si se necesita rollback,
    # restaurar desde backup pre-migración.
    raise NotImplementedError("Downgrade no soportado — restaurar desde backup.")
```

> **Why no real downgrade?** Recrear tablas/columnas no devuelve los datos. Si algo sale mal, el rollback es restaurar el backup de Postgres tomado antes de aplicar la migración (Riesgo R1 del spec).

- [ ] **Step 3: Validate file syntax**

```bash
python -m py_compile migrations/versions/20260429_01_drop_multitenant.py
```

Expected: silent.

- [ ] **Step 4: Commit migration (no aplicar todavía)**

```bash
git add migrations/versions/20260429_01_drop_multitenant.py
git commit -m "feat(migrations): drop multi-tenant scaffolding"
```

---

## Task 11: Smoke test + apply migration

**Files:**
- None (runtime verification only)

- [ ] **Step 1: Backup de la DB de desarrollo**

Si tienes datos importantes en local:
```bash
pg_dump "$DATABASE_URL" > /tmp/dasic_pre_strip.sql
```

(Skipear si la DB local es desechable.)

- [ ] **Step 2: Aplicar migración**

```bash
alembic upgrade head
```

Expected: log de `Running upgrade ... -> 20260429_01, drop multi-tenant scaffolding`. Sin errores.

- [ ] **Step 3: Verificar schema en Postgres**

```bash
psql "$DATABASE_URL" -c "\d clientes" | grep -i organization_id
psql "$DATABASE_URL" -c "\dt organizations branches user_organizations"
```

Expected: primer comando vacío (columna ya no existe). Segundo comando: "Did not find any relation named …".

- [ ] **Step 4: Levantar la app**

```bash
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://127.0.0.1:8000/health | head
```

Expected: `{"status":"ok","db":"ok"}`.

- [ ] **Step 5: Login smoke test**

```bash
curl -s -c /tmp/cookies.txt -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@dasic.com&password=admin123" | head
```

Expected: JSON `{"access_token":"...","token_type":"bearer"}`.

- [ ] **Step 6: Browse SSR routes con cookie**

```bash
for path in /dashboard /clientes /ventas/cotizador /seguimiento /inventario /compras /gastos /reportes /usuarios; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b /tmp/cookies.txt "http://127.0.0.1:8000${path}")
  echo "${path} → ${code}"
done
```

Expected: every line ends in `200`. Si alguna devuelve 500, leer logs (`uvicorn` los imprimirá en stderr) y abrir issue puntual — la mayoría serán filtros que dejaron un `.filter()` vacío o un kwarg removido a destiempo.

- [ ] **Step 7: Smoke de cotización**

```bash
# Crear una cotización mínima para verificar que folios siguen funcionando.
curl -s -b /tmp/cookies.txt -X POST http://127.0.0.1:8000/api/ventas/cotizaciones \
  -H "Content-Type: application/json" \
  -d '{"cliente_id": 1, "moneda": "MXN", "tipo_cambio": 1.0, "lineas": []}' | head
```

Expected: respuesta con `"folio": "COT-YYYYMM-..."` (sin error 500). Si no hay cliente_id=1 en la DB, crear uno antes via `/api/clientes` o `psql`.

- [ ] **Step 8: Apagar uvicorn**

```bash
kill %1 2>/dev/null || pkill -f 'uvicorn app.main:app'
```

- [ ] **Step 9: Final cross-check**

```bash
git grep -nE 'organization_id|UserOrganization|get_current_active_organization|set_tenant_context|X-Organization-ID' \
  app/ scripts/ 2>/dev/null
```

Expected: zero results. Cualquier hit indica que algo se escapó del refactor.

- [ ] **Step 10: Commit (si quedó configuración o doc edits)**

```bash
git status
# si hay cambios sin commitear, hacer un último commit:
git commit -am "chore: post-strip cleanups"
```

- [ ] **Step 11: Cierre de fase**

Actualizar el spec si descubriste un edge case no documentado:
```bash
# Editar docs/superpowers/specs/2026-04-28-mvp-dasic-design.md sección 9 (Riesgos)
# si surgió algo no previsto. Commit.
```

---

## Definition of Done — Fase 0

- [ ] `git grep -E 'organization_id|UserOrganization|get_current_active_organization|set_tenant_context|X-Organization-ID' app/ scripts/` → cero resultados
- [ ] `alembic upgrade head` aplicó `20260429_01_drop_multitenant` sin error
- [ ] DB Postgres ya no tiene columnas `organization_id` ni tablas `organizations`/`branches`/`user_organizations`
- [ ] Login funciona; el JWT emitido **no** contiene `org_id` ni `branch_id`
- [ ] Las 9 vistas SSR (`/dashboard`, `/clientes`, `/ventas/cotizador`, `/seguimiento`, `/inventario`, `/compras`, `/gastos`, `/reportes`, `/usuarios`) devuelven 200 con sesión válida
- [ ] Crear una cotización via API sigue devolviendo folio válido
- [ ] CI / pipelines de Railway no rotos (verificar después de deploy)

---

## Next phase

Una vez Fase 0 esté merged a `main` y deployed, escribir el plan de Fase 1 (Live Stock + Kardex) — vía `superpowers:writing-plans` con la sección §4 del spec como input.
