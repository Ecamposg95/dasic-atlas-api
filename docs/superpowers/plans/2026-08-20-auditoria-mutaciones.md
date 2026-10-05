# Auditoría de Mutaciones (Ola 4 · E5) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bitácora global `audit_log` + servicio `audit_service.registrar` capturando 7 mutaciones sensibles, expuesta (junto a los ajustes de stock ya registrados) en la consola de auditoría del superadmin.

**Architecture:** Tabla genérica + llamadas explícitas dentro de la transacción de cada mutación (sin listeners automáticos). La consola `GET /api/superadmin/audit` ya normaliza fuentes heterogéneas a `AuditEvent`; se le enchufan dos fuentes nuevas: `sistema` (tabla nueva) y `stock` (movimientos AJUSTE existentes).

**Tech Stack:** FastAPI + SQLAlchemy 2.x + Alembic (backend), pytest (fixtures `db`, `usuario`, `client_as` de `tests/conftest.py`), React/TS (un filtro en la página de Auditoría).

**Spec:** `docs/superpowers/specs/2026-08-20-auditoria-mutaciones-design.md`

## Global Constraints

- **Sin `organization_id`** en la tabla nueva (decisión mono-empresa 2026-08-19 supersede el invariante 15 del golden path).
- `registrar` **nunca hace commit** — participa en la transacción del caller.
- Tabla nueva: revisión Alembic con `down_revision = "20260806_01"`; **no** se toca `_BACKFILL_DDL` (solo aplica a columnas de tablas existentes; `create_all()` del lifespan crea la tabla en producción).
- Campo del RFC en `Cliente` es **`rfc_tax_id`** (no `rfc`).
- `UserService.create_user` **hace commit interno** — el evento de alta se registra y commitea inmediatamente después (ver Task 5).
- Commits en español, pequeños, un commit por task.
- Verificación por task: `python3 -m compileall app` + pytest del archivo tocado; al final suite completa + `cd web && npm run typecheck && npm run build`.

---

### Task 1: Modelo `AuditLog` + migración

**Files:**
- Create: `app/models/audit.py`
- Modify: `app/models/__init__.py` (import + `__all__`)
- Create: `migrations/versions/20260820_01_audit_log.py`
- Test: `tests/test_audit_service.py`

**Interfaces:**
- Produces: `models.AuditLog` con columnas `id, fecha, usuario_id, accion, entidad, entidad_id, resumen, datos` — Tasks 2–6 dependen de estos nombres exactos.

- [ ] **Step 1: Write the failing test**

Crear `tests/test_audit_service.py`:

```python
"""Bitácora global de mutaciones (audit_log) — modelo y servicio."""
from app import models


def test_modelo_audit_log_persiste_con_defaults(db, usuario):
    u = usuario()
    db.add(models.AuditLog(
        usuario_id=u.id,
        accion="eliminar",
        entidad="cliente",
        entidad_id=123,
        resumen="Eliminó cliente ACME",
    ))
    db.commit()
    row = db.query(models.AuditLog).one()
    assert row.fecha is not None           # server_default
    assert row.datos is None
    assert (row.accion, row.entidad, row.entidad_id) == ("eliminar", "cliente", 123)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_audit_service.py -v`
Expected: FAIL con `AttributeError: module 'app.models' has no attribute 'AuditLog'`

- [ ] **Step 3: Write minimal implementation**

Crear `app/models/audit.py`:

```python
"""Bitácora global de mutaciones sensibles (Ola 4 E5).

Sin FK en entidad_id: la entidad auditada puede ya no existir (deletes).
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    accion = Column(String(40), nullable=False)   # eliminar | cambio_precio | cambio_rol | desactivar | crear
    entidad = Column(String(40), nullable=False)  # cliente | contacto | producto | gasto | usuario
    entidad_id = Column(Integer, nullable=True)
    resumen = Column(String(400), nullable=False)
    datos = Column(Text, nullable=True)  # JSON: diff viejo→nuevo o snapshot del borrado

    usuario = relationship("Usuario", foreign_keys=[usuario_id])

    __table_args__ = (Index("ix_audit_log_entidad", "entidad", "entidad_id"),)
```

En `app/models/__init__.py`, junto a los demás imports (línea ~36):

```python
from app.models.audit import AuditLog  # noqa: F401
```

y `"AuditLog",` dentro de la lista `__all__` (línea ~83). **Omitir el re-export tumba el arranque** — es la regla nº 3 del README.

Crear `migrations/versions/20260820_01_audit_log.py`:

```python
"""audit_log: bitácora global de mutaciones sensibles (Ola 4 E5).

Revision ID: 20260820_01
Revises: 20260806_01
"""
import sqlalchemy as sa
from alembic import op

revision = "20260820_01"
down_revision = "20260806_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("accion", sa.String(40), nullable=False),
        sa.Column("entidad", sa.String(40), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("resumen", sa.String(400), nullable=False),
        sa.Column("datos", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_log_id", "audit_log", ["id"])
    op.create_index("ix_audit_log_fecha", "audit_log", ["fecha"])
    op.create_index("ix_audit_log_usuario_id", "audit_log", ["usuario_id"])
    op.create_index("ix_audit_log_entidad", "audit_log", ["entidad", "entidad_id"])


def downgrade():
    op.drop_table("audit_log")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_audit_service.py -v && python3 -m compileall app -q`
Expected: PASS (en modo SQLite la tabla la crea `create_all`; la migración la ejercita CI en modo PG)

- [ ] **Step 5: Commit**

```bash
git add app/models/audit.py app/models/__init__.py migrations/versions/20260820_01_audit_log.py tests/test_audit_service.py
git commit -m "feat(auditoria): modelo AuditLog y migración de la bitácora global"
```

---

### Task 2: Servicio `audit_service.registrar`

**Files:**
- Create: `app/services/audit_service.py`
- Test: `tests/test_audit_service.py` (ampliar)

**Interfaces:**
- Consumes: `models.AuditLog` (Task 1).
- Produces: `audit_service.registrar(db, *, usuario, accion, entidad, entidad_id, resumen, datos=None) -> models.AuditLog` — firma exacta que usan Tasks 3–5. `usuario` es `models.Usuario | None`; `datos` es `dict | None`.

- [ ] **Step 1: Write the failing tests**

Añadir a `tests/test_audit_service.py`:

```python
from app.services import audit_service


def test_registrar_participa_en_la_transaccion_del_caller(db, usuario):
    u = usuario()
    audit_service.registrar(
        db, usuario=u, accion="eliminar", entidad="cliente",
        entidad_id=1, resumen="x",
    )
    db.rollback()  # la mutación "falló": el evento debe irse con ella
    assert db.query(models.AuditLog).count() == 0

    audit_service.registrar(
        db, usuario=u, accion="eliminar", entidad="cliente",
        entidad_id=1, resumen="x",
    )
    db.commit()
    assert db.query(models.AuditLog).count() == 1


def test_registrar_serializa_datos_y_tolera_usuario_none(db):
    audit_service.registrar(
        db, usuario=None, accion="cambio_precio", entidad="producto",
        entidad_id=5, resumen="r" * 500,  # se trunca a 400
        datos={"costo_compra": {"antes": "10.00", "despues": "12.50"}},
    )
    db.commit()
    row = db.query(models.AuditLog).one()
    assert row.usuario_id is None
    assert len(row.resumen) == 400
    assert '"antes": "10.00"' in row.datos
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_audit_service.py -v`
Expected: FAIL con `ImportError: cannot import name 'audit_service'`

- [ ] **Step 3: Write minimal implementation**

Crear `app/services/audit_service.py`:

```python
"""Registro en la bitácora global de mutaciones (tabla audit_log).

`registrar` NO hace commit: participa en la transacción del caller para que
el evento se persista —o se revierta— atómicamente con la mutación auditada.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app import models


def registrar(
    db: Session,
    *,
    usuario: Optional["models.Usuario"],
    accion: str,
    entidad: str,
    entidad_id: Optional[int],
    resumen: str,
    datos: Optional[dict] = None,
) -> "models.AuditLog":
    evento = models.AuditLog(
        usuario_id=usuario.id if usuario is not None else None,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        resumen=resumen[:400],
        datos=json.dumps(datos, ensure_ascii=False, default=str) if datos else None,
    )
    db.add(evento)
    return evento
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_audit_service.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/audit_service.py tests/test_audit_service.py
git commit -m "feat(auditoria): audit_service.registrar — evento atómico con la transacción del caller"
```

---

### Task 3: Captura en `clientes.py` (eliminar cliente y contacto)

**Files:**
- Modify: `app/routers/clientes.py` (endpoints `eliminar_cliente` ~línea 409 y `eliminar_contacto` ~línea 1126)
- Test: `tests/test_auditoria_captura.py` (nuevo)

**Interfaces:**
- Consumes: `audit_service.registrar` (Task 2). `clientes.py` ya importa `get_current_user` (línea 15).
- Nota de campos: `Cliente.nombre_empresa`, `Cliente.rfc_tax_id`, `Cliente.saldo_actual`; `Contacto.nombre`, `Contacto.cargo`.

- [ ] **Step 1: Write the failing tests**

Crear `tests/test_auditoria_captura.py`:

```python
"""La captura de auditoría en los routers: deletes y ediciones sensibles."""
from decimal import Decimal

from app import models


def _cliente(db, nombre="ACME Industrial"):
    c = models.Cliente(nombre_empresa=nombre, rfc_tax_id="AAA010101AAA")
    db.add(c)
    db.commit()
    return c


def test_eliminar_cliente_registra_auditoria(db, client_as):
    c = _cliente(db)
    admin = client_as("administrador")
    r = admin.delete(f"/api/clientes/{c.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad, ev.entidad_id) == ("eliminar", "cliente", c.id)
    assert "ACME Industrial" in ev.resumen
    assert ev.usuario_id == admin.user.id


def test_eliminar_cliente_bloqueado_no_registra(db, client_as):
    c = _cliente(db)
    db.add(models.OrdenVenta(folio="C-X-1", cliente_id=c.id))
    db.commit()
    admin = client_as("administrador")
    r = admin.delete(f"/api/clientes/{c.id}")
    assert r.status_code == 409
    assert db.query(models.AuditLog).count() == 0


def test_eliminar_contacto_registra_auditoria(db, client_as):
    c = _cliente(db)
    contacto = models.Contacto(cliente_id=c.id, nombre="Juan Pérez", cargo="Compras")
    db.add(contacto)
    db.commit()
    admin = client_as("administrador")
    r = admin.delete(f"/api/clientes/{c.id}/contactos/{contacto.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad) == ("eliminar", "contacto")
    assert "Juan Pérez" in ev.resumen
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_auditoria_captura.py -v`
Expected: los 2 tests de registro FAIL (0 filas en `audit_log`); el de bloqueo PASS ya (guard-rail).

- [ ] **Step 3: Implement**

En `app/routers/clientes.py`, añadir el import junto a los demás de `app.*`:

```python
from app.services import audit_service
```

En `eliminar_cliente`, añadir el parámetro de usuario (hoy no lo tiene):

```python
def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
```

y dentro del `try`, inmediatamente **antes** de `db.delete(cliente)`:

```python
        audit_service.registrar(
            db,
            usuario=current_user,
            accion="eliminar",
            entidad="cliente",
            entidad_id=cliente.id,
            resumen=(
                f"Eliminó cliente {cliente.nombre_empresa} "
                f"(RFC {cliente.rfc_tax_id or '—'}, saldo {cliente.saldo_actual or 0})"
            ),
            datos={"nombre_empresa": cliente.nombre_empresa, "rfc_tax_id": cliente.rfc_tax_id},
        )
```

En `eliminar_contacto`, añadir `current_user: models.Usuario = Depends(get_current_user)` a la firma y, antes de `db.delete(c)`:

```python
    audit_service.registrar(
        db,
        usuario=current_user,
        accion="eliminar",
        entidad="contacto",
        entidad_id=c.id,
        resumen=f"Eliminó contacto {c.nombre} ({c.cargo or 'sin cargo'}) del cliente #{cliente_id}",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_auditoria_captura.py tests/test_audit_service.py -v && python3 -m compileall app -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/routers/clientes.py tests/test_auditoria_captura.py
git commit -m "feat(auditoria): eliminar cliente y contacto dejan rastro en audit_log"
```

---

### Task 4: Captura en `productos.py` (delete + cambio de precio)

**Files:**
- Modify: `app/routers/productos.py` (`actualizar_producto` ~línea 443, `eliminar_producto` ~línea 526)
- Test: `tests/test_auditoria_captura.py` (ampliar)

**Interfaces:**
- Consumes: `audit_service.registrar` (Task 2). `productos.py` ya importa `get_current_user` y `Decimal`.
- Produces: helper privado `_diff_precio(previo: dict, producto) -> dict` en `productos.py`.

- [ ] **Step 1: Write the failing tests**

Añadir a `tests/test_auditoria_captura.py`:

```python
def _producto(db, **kw):
    defaults = dict(sku="SKU-1", nombre="Bomba X", costo_compra=Decimal("100.00"),
                    moneda_compra="MXN", precio_publico=Decimal("150.00"))
    defaults.update(kw)
    p = models.Producto(**defaults)
    db.add(p)
    db.commit()
    return p


def test_cambio_de_costo_registra_diff(db, client_as):
    p = _producto(db)
    admin = client_as("administrador")
    r = admin.put(f"/api/productos/{p.id}", json={"costo_compra": 120.5})
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad, ev.entidad_id) == ("cambio_precio", "producto", p.id)
    assert '"antes": "100.00"' in ev.datos and '"despues": "120.5' in ev.datos


def test_update_sin_cambio_de_precio_no_registra(db, client_as):
    p = _producto(db)
    admin = client_as("administrador")
    r = admin.put(f"/api/productos/{p.id}", json={"nombre": "Bomba X v2", "costo_compra": 100.0})
    assert r.status_code == 200
    assert db.query(models.AuditLog).count() == 0


def test_eliminar_producto_registra_auditoria(db, client_as):
    p = _producto(db)
    admin = client_as("administrador")
    r = admin.delete(f"/api/productos/{p.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad) == ("eliminar", "producto")
    assert "SKU-1" in ev.resumen
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_auditoria_captura.py -v`
Expected: FAIL los 2 de registro; el de "sin cambio no registra" PASS ya.

- [ ] **Step 3: Implement**

En `app/routers/productos.py`, import junto a los demás:

```python
from app.services import audit_service
```

Helper a nivel de módulo (junto a `_normalize_currency` y compañía):

```python
def _diff_precio(previo: dict, producto) -> dict:
    """Diff viejo→nuevo de los campos sensibles de precio. Compara numéricos
    como Decimal para no reportar falsos cambios (100.00 vs 100.0)."""
    cambios = {}
    for campo in ("costo_compra", "precio_publico"):
        a, d = previo[campo], getattr(producto, campo)
        a_n = Decimal(str(a)) if a is not None else None
        d_n = Decimal(str(d)) if d is not None else None
        if a_n != d_n:
            cambios[campo] = {"antes": str(a_n), "despues": str(d_n)}
    if (previo["moneda_compra"] or "") != (getattr(producto, "moneda_compra") or ""):
        cambios["moneda_compra"] = {
            "antes": previo["moneda_compra"], "despues": producto.moneda_compra,
        }
    return cambios
```

En `actualizar_producto`, **antes** del loop `for key, value in update_data.items():` (el snapshot debe leerse antes de mutar):

```python
        previo_precio = {
            "costo_compra": db_producto.costo_compra,
            "moneda_compra": db_producto.moneda_compra,
            "precio_publico": db_producto.precio_publico,
        }
```

Después del loop de `setattr` y **antes** de `db.commit()` (tras el bloque de `nuevo_stock`):

```python
        cambios_precio = _diff_precio(previo_precio, db_producto)
        if cambios_precio:
            audit_service.registrar(
                db,
                usuario=current_user,
                accion="cambio_precio",
                entidad="producto",
                entidad_id=db_producto.id,
                resumen=(
                    f"Cambió precios de {db_producto.sku} — "
                    + ", ".join(sorted(cambios_precio))
                ),
                datos=cambios_precio,
            )
```

En `eliminar_producto`, añadir a la firma `current_user: models.Usuario = Depends(get_current_user)` y antes de `db.delete(db_producto)`:

```python
    audit_service.registrar(
        db,
        usuario=current_user,
        accion="eliminar",
        entidad="producto",
        entidad_id=db_producto.id,
        resumen=f"Eliminó producto {db_producto.sku} — {db_producto.nombre}",
        datos={"sku": db_producto.sku, "nombre": db_producto.nombre,
               "costo_compra": db_producto.costo_compra},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_auditoria_captura.py -v && python3 -m compileall app -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/routers/productos.py tests/test_auditoria_captura.py
git commit -m "feat(auditoria): delete de producto y cambio de precio/costo/moneda dejan rastro"
```

---

### Task 5: Captura en `gastos.py` y `usuarios.py`

**Files:**
- Modify: `app/routers/gastos.py` (`eliminar_gasto` ~línea 196)
- Modify: `app/routers/usuarios.py` (`crear_usuario` ~44, `actualizar_usuario` ~69, `eliminar_usuario` ~174)
- Test: `tests/test_auditoria_captura.py` (ampliar)

**Interfaces:**
- Consumes: `audit_service.registrar` (Task 2). `gastos.py` ya importa `get_current_user` (línea 13). `Gasto` tiene `categoria`, `descripcion`, `monto`, `moneda`.
- **Restricción:** `UserService.create_user` hace commit interno → el evento de alta se registra después y se commitea aparte (no es atómico con el alta; aceptable y documentado aquí).

- [ ] **Step 1: Write the failing tests**

Añadir a `tests/test_auditoria_captura.py`:

```python
def test_eliminar_gasto_registra_auditoria(db, client_as):
    g = models.Gasto(categoria="Viáticos", descripcion="Gasolina", monto=Decimal("500.00"), moneda="MXN")
    db.add(g)
    db.commit()
    admin = client_as("administrador")
    r = admin.delete(f"/api/gastos/{g.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad) == ("eliminar", "gasto")
    assert "Viáticos" in ev.resumen and "500" in ev.resumen


def test_crear_usuario_registra_alta(db, client_as):
    admin = client_as("administrador")
    r = admin.post("/api/usuarios/", json={
        "nombre": "Nuevo Vendedor", "email": "nuevo@test.local",
        "password": "secreto123", "rol": "vendedor",
    })
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad) == ("crear", "usuario")
    assert "nuevo@test.local" in ev.resumen


def test_cambio_de_rol_y_desactivacion_registran(db, client_as, usuario):
    objetivo = usuario(rol="vendedor", email="objetivo@test.local")
    admin = client_as("administrador")

    r = admin.put(f"/api/usuarios/{objetivo.id}", json={"rol": "operativo"})
    assert r.status_code == 200
    r = admin.put(f"/api/usuarios/{objetivo.id}", json={"activo": False})
    assert r.status_code == 200

    acciones = {e.accion for e in db.query(models.AuditLog).all()}
    assert {"cambio_rol", "desactivar"} <= acciones


def test_update_usuario_sin_cambio_sensible_no_registra(db, client_as, usuario):
    objetivo = usuario(rol="vendedor", email="obj2@test.local")
    admin = client_as("administrador")
    r = admin.put(f"/api/usuarios/{objetivo.id}", json={"nombre": "Otro Nombre"})
    assert r.status_code == 200
    assert db.query(models.AuditLog).count() == 0


def test_eliminar_usuario_registra(db, client_as, usuario):
    objetivo = usuario(rol="vendedor", email="borrar@test.local")
    admin = client_as("administrador")
    r = admin.delete(f"/api/usuarios/{objetivo.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad, ev.entidad_id) == ("eliminar", "usuario", objetivo.id)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_auditoria_captura.py -v`
Expected: FAIL los de registro; "sin cambio sensible" PASS ya.

- [ ] **Step 3: Implement**

`app/routers/gastos.py` — import `from app.services import audit_service`; en `eliminar_gasto` añadir `current_user: models.Usuario = Depends(get_current_user)` y antes de `db.delete(g)`:

```python
    audit_service.registrar(
        db,
        usuario=current_user,
        accion="eliminar",
        entidad="gasto",
        entidad_id=g.id,
        resumen=f"Eliminó gasto {g.categoria} por {g.monto} {g.moneda} ({g.descripcion or 'sin descripción'})",
        datos={"categoria": g.categoria, "monto": g.monto, "moneda": g.moneda},
    )
```

`app/routers/usuarios.py` — import `from app.services import audit_service`. En `crear_usuario`, sustituir `return UserService.create_user(db, usuario)` por:

```python
        nuevo = UserService.create_user(db, usuario)  # hace commit interno
        audit_service.registrar(
            db,
            usuario=current_user,
            accion="crear",
            entidad="usuario",
            entidad_id=nuevo.id,
            resumen=f"Creó usuario {nuevo.email} con rol {RolUsuario.from_input(nuevo.rol).value}",
        )
        db.commit()
        return nuevo
```

En `actualizar_usuario`, capturar el estado previo justo después de calcular `target_rol` (ya existe):

```python
    activo_previo = bool(target.activo)
```

y dentro del `try`, después del loop `for k, v in data.items():` y **antes** de `db.commit()`:

```python
        if nuevo_rol is not None and nuevo_rol != target_rol:
            audit_service.registrar(
                db,
                usuario=current_user,
                accion="cambio_rol",
                entidad="usuario",
                entidad_id=target.id,
                resumen=f"Cambió rol de {target.email}: {target_rol.value} → {nuevo_rol.value}",
                datos={"antes": target_rol.value, "despues": nuevo_rol.value},
            )
        if nuevo_activo is False and activo_previo:
            audit_service.registrar(
                db,
                usuario=current_user,
                accion="desactivar",
                entidad="usuario",
                entidad_id=target.id,
                resumen=f"Desactivó al usuario {target.email}",
            )
```

En `eliminar_usuario`, dentro del `try` antes de `db.delete(user_to_delete)`:

```python
        audit_service.registrar(
            db,
            usuario=current_user,
            accion="eliminar",
            entidad="usuario",
            entidad_id=user_to_delete.id,
            resumen=f"Eliminó al usuario {user_to_delete.email} (rol {RolUsuario.from_input(user_to_delete.rol).value})",
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_auditoria_captura.py -v && python3 -m compileall app -q`
Expected: PASS (los 6 nuevos + los 5 previos)

- [ ] **Step 5: Commit**

```bash
git add app/routers/gastos.py app/routers/usuarios.py tests/test_auditoria_captura.py
git commit -m "feat(auditoria): gastos y ciclo de vida de usuarios dejan rastro"
```

---

### Task 6: Consola — fuentes `sistema` y `stock` + filtro en frontend

**Files:**
- Modify: `app/routers/superadmin.py` (clase `AuditEvent` ~línea 81, normalizadores ~93–155, `get_audit` ~155–222)
- Modify: `web/src/features/superadmin/hooks/useAudit.ts` (línea 4)
- Modify: `web/src/features/superadmin/pages/AuditPage.tsx` (~líneas 84 y 162)
- Test: `tests/test_auditoria_consola.py` (nuevo)

**Interfaces:**
- Consumes: `models.AuditLog` (Task 1); `models.MovimientoStock` (campos `tipo`, `cantidad`, `motivo`, `usuario_id`, `creado_en`, `stock_resultante`); enum `TipoMovimientoStock.AJUSTE` con valor `"ajuste"`.
- Produces: `GET /api/superadmin/audit?fuente=sistema|stock` — mismo shape `AuditEvent` de siempre.

- [ ] **Step 1: Write the failing tests**

Crear `tests/test_auditoria_consola.py`:

```python
"""GET /api/superadmin/audit — fuentes sistema y stock."""
from app import models
from app.services import audit_service
from app.services.stock_service import aplicar_movimiento
from app.models.enums import TipoMovimientoStock


def _sembrar(db, usuario):
    u = usuario(rol="superadmin", email="root@test.local")
    audit_service.registrar(
        db, usuario=u, accion="eliminar", entidad="cliente",
        entidad_id=9, resumen="Eliminó cliente ACME",
    )
    p = models.Producto(sku="SKU-9", nombre="Válvula", stock_actual=10)
    db.add(p)
    db.commit()
    aplicar_movimiento(
        db, producto=p, tipo=TipoMovimientoStock.AJUSTE.value,
        cantidad=-3, motivo="merma", usuario=u,
    )
    db.commit()
    return u


def test_fuente_sistema_y_stock_aparecen(db, client_as, usuario):
    _sembrar(db, usuario)
    root = client_as("superadmin", email="root2@test.local")
    r = root.get("/api/superadmin/audit")
    assert r.status_code == 200
    fuentes = {e["fuente"] for e in r.json()["items"]}
    assert {"sistema", "stock"} <= fuentes


def test_filtro_fuente_stock(db, client_as, usuario):
    _sembrar(db, usuario)
    root = client_as("superadmin", email="root2@test.local")
    r = root.get("/api/superadmin/audit?fuente=stock")
    items = r.json()["items"]
    assert items and all(e["fuente"] == "stock" for e in items)
    assert any("merma" in e["detalle"] for e in items)


def test_filtro_usuario_aplica_a_fuentes_nuevas(db, client_as, usuario):
    u = _sembrar(db, usuario)
    root = client_as("superadmin", email="root2@test.local")
    r = root.get(f"/api/superadmin/audit?usuario_id={u.id}")
    items = r.json()["items"]
    assert items and all(e["usuario_id"] == u.id for e in items)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_auditoria_consola.py -v`
Expected: FAIL — `fuente=stock` devuelve 422 (Literal no lo admite) y las fuentes nuevas no aparecen.

- [ ] **Step 3: Implement backend**

En `app/routers/superadmin.py`:

1. Import nuevo junto a `from app import models`:

```python
from app.models.enums import TipoMovimientoStock
```

2. Ampliar el Literal de la clase `AuditEvent` y del parámetro `fuente` de `get_audit` a:

```python
Literal["cotizacion", "fusion_cliente", "sistema", "stock"]
```

3. Normalizadores nuevos, después de `_normalize_merge_log`:

```python
_ACCION_SISTEMA = {
    "eliminar": "Eliminación",
    "cambio_precio": "Cambio de precio",
    "cambio_rol": "Cambio de rol",
    "desactivar": "Desactivación",
    "crear": "Alta",
}

_LINK_SISTEMA = {
    "cliente": "/spa/clientes",
    "producto": "/spa/productos",
    "usuario": "/spa/usuarios",
    "gasto": "/spa/gastos",
}


def _normalize_audit_log(row, nombre_map: dict) -> AuditEvent:
    return AuditEvent(
        fuente="sistema",
        fecha=row.fecha,
        usuario=(nombre_map.get(row.usuario_id) or "—") if row.usuario_id else "—",
        usuario_id=row.usuario_id,
        accion=f"{_ACCION_SISTEMA.get(row.accion, row.accion)} de {row.entidad}",
        entidad=f"{row.entidad} #{row.entidad_id}" if row.entidad_id else row.entidad,
        detalle=row.resumen,
        link=_LINK_SISTEMA.get(row.entidad),
    )


def _normalize_stock_ajuste(mov, producto_map: dict, nombre_map: dict) -> AuditEvent:
    prod = producto_map.get(mov.producto_id)
    return AuditEvent(
        fuente="stock",
        fecha=mov.creado_en,
        usuario=(nombre_map.get(mov.usuario_id) or "—") if mov.usuario_id else "—",
        usuario_id=mov.usuario_id,
        accion="Ajuste de stock",
        entidad=prod or f"Producto #{mov.producto_id}",
        detalle=(
            f"{'+' if mov.cantidad >= 0 else ''}{mov.cantidad} → stock {mov.stock_resultante}"
            + (f" · {mov.motivo}" if mov.motivo else "")
        ),
        link="/spa/inventario",
    )
```

4. En `get_audit`, después del bloque de `cliente_merge_log` añadir los dos bloques de consulta (mismo patrón de filtros de fecha que los existentes):

```python
    # --- audit_log (fuente sistema) ---
    if fuente in (None, "sistema"):
        a = db.query(models.AuditLog)
        if usuario_id is not None:
            a = a.filter(models.AuditLog.usuario_id == usuario_id)
        if desde is not None:
            a = a.filter(models.AuditLog.fecha >= datetime.combine(desde, time.min))
        if hasta is not None:
            a = a.filter(models.AuditLog.fecha < datetime.combine(hasta + timedelta(days=1), time.min))
        arows = a.all()
    else:
        arows = []

    # --- movimientos_stock tipo AJUSTE (fuente stock) ---
    if fuente in (None, "stock"):
        s = db.query(models.MovimientoStock).filter(
            models.MovimientoStock.tipo == TipoMovimientoStock.AJUSTE.value
        )
        if usuario_id is not None:
            s = s.filter(models.MovimientoStock.usuario_id == usuario_id)
        if desde is not None:
            s = s.filter(models.MovimientoStock.creado_en >= datetime.combine(desde, time.min))
        if hasta is not None:
            s = s.filter(models.MovimientoStock.creado_en < datetime.combine(hasta + timedelta(days=1), time.min))
        srows = s.all()
        producto_map: dict = {}
        pids = {m.producto_id for m in srows}
        if pids:
            for pid, sku, nombre in (
                db.query(models.Producto.id, models.Producto.sku, models.Producto.nombre)
                .filter(models.Producto.id.in_(pids))
                .all()
            ):
                producto_map[pid] = f"{sku} — {nombre}"
    else:
        srows, producto_map = [], {}
```

5. Ampliar el set `uids` (para el batch de nombres):

```python
    uids = (
        {e.creado_por_id for e in qrows if e.creado_por_id}
        | {r.merged_by_id for r in mrows if r.merged_by_id}
        | {a.usuario_id for a in arows if a.usuario_id}
        | {m.usuario_id for m in srows if m.usuario_id}
    )
```

6. Sumar los eventos normalizados antes del sort:

```python
    eventos += [_normalize_audit_log(a, nombre_map) for a in arows]
    eventos += [_normalize_stock_ajuste(m, producto_map, nombre_map) for m in srows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_auditoria_consola.py tests/test_auditoria_captura.py -v && python3 -m compileall app -q`
Expected: PASS

- [ ] **Step 5: Implement frontend**

`web/src/features/superadmin/hooks/useAudit.ts`, línea 4:

```ts
export type AuditFuente = 'cotizacion' | 'fusion_cliente' | 'sistema' | 'stock';
```

`web/src/features/superadmin/pages/AuditPage.tsx`, en el `<select>` de fuente (~línea 84), añadir tras la opción de Fusiones:

```tsx
              <option value="sistema">Sistema</option>
              <option value="stock">Ajustes de stock</option>
```

y en el Badge de la fila (~línea 162), sustituir el ternario por un mapa:

```tsx
const FUENTE_BADGE: Record<string, 'emerald' | 'slate' | 'sky' | 'amber'> = {
  cotizacion: 'emerald',
  fusion_cliente: 'slate',
  sistema: 'sky',
  stock: 'amber',
};
```

(declarado a nivel de módulo, fuera del componente) y en el JSX:

```tsx
                      <Badge variant={FUENTE_BADGE[e.fuente] ?? 'default'}>
```

- [ ] **Step 6: Verify frontend**

Run: `cd web && npm run typecheck`
Expected: sin errores

- [ ] **Step 7: Commit**

```bash
git add app/routers/superadmin.py web/src/features/superadmin/hooks/useAudit.ts web/src/features/superadmin/pages/AuditPage.tsx tests/test_auditoria_consola.py
git commit -m "feat(auditoria): la consola expone las fuentes sistema y stock con filtro"
```

---

### Task 7: Verificación final, build y documentación

**Files:**
- Modify: `docs/current-state/backlog.md` (Ola 4 y la nota operativa de CI)
- Modify: `app/static/dist/` (build)

**Interfaces:**
- Consumes: todo lo anterior.

- [ ] **Step 1: Run full verification**

```bash
python3 -m compileall app -q
python3 -m pytest -q
cd web && npm run typecheck && npm run test && npm run build
```

Expected: todo verde. El build regenera `app/static/dist/` (obligatorio commitearlo: Railway no compila la SPA).

- [ ] **Step 2: Update backlog**

En `docs/current-state/backlog.md`:

1. En la sección "P1 · Golden path", línea de la Ola 4, marcar el primer punto:

```markdown
- ~~Ampliar la auditoría más allá de cotizaciones y fusiones~~ **Hecho (2026-08-20):** `audit_log` + `audit_service` capturan deletes de cliente/contacto/producto/gasto, cambios de precio y ciclo de vida de usuarios; la consola expone además los ajustes de stock. Spec: `docs/superpowers/specs/2026-08-20-auditoria-mutaciones-design.md`. Fuera de esa entrega: upload-csv masivo y cambio de contraseña (segunda pasada).
```

2. En "Operativos, no de producto", sustituir el párrafo de GitHub Actions por:

```markdown
- ~~GitHub Actions dejó de crear runs el 6 de agosto~~ **Resuelto solo:** desde el 8 de agosto los runs se crean y pasan en verde con normalidad (verificado 2026-08-20).
```

- [ ] **Step 3: Commit**

```bash
git add docs/current-state/backlog.md app/static/dist/
git commit -m "feat(auditoria): build de la SPA y backlog al día — Ola 4 E5 entregada"
```

- [ ] **Step 4: Report**

No hacer push (regla del repo: el push a `main` lo decide el usuario). Reportar: tests corridos, archivos tocados, y que el diccionario de datos de `docs/reference/` quedó desactualizado (47→48 tablas) — regenerarlo es opcional y se ofrece como siguiente paso.
