# Hotfix fechas en dashboard y cotizador — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que los cinco endpoints que hoy devuelven 500 en producción vuelvan a responder, con pruebas que impidan que la misma clase de fallo regrese, y dejar la actualización lista para subir junto con la auditoría de mutaciones.

**Architecture:** El commit `b0c5878` (2026-08-06) pasó `ordenes_venta.fecha_creacion` y `fecha_vencimiento` de instante a `DATE`. `app/routers/dashboard.py` y un endpoint de `app/routers/ventas.py` siguen tratándolas como `datetime` (`.tzinfo`, `.date()`, resta contra `datetime.utcnow()`). El arreglo sustituye esa aritmética de instantes por aritmética de **días de calendario** contra `app.core.fechas.hoy_negocio()`, que ya es la fuente única del "hoy" del negocio. No hay cambio de esquema ni de frontend.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, pytest (SQLite en memoria sin `TEST_DATABASE_URL`; PostgreSQL 16 en CI), ruff.

**Spec:** No hay documento de spec. La autoridad es la evidencia de producción resumida aquí:

- Logs de Railway (servicio `Dasic_Atlas_api`, entorno `production`), del 2026-09-07 al 2026-10-02: **859 respuestas 500**, todas de cuatro rutas — `GET /api/ventas/ultima-cotizacion-cliente/{id}` (332), `GET /api/dashboard/pipeline` (201), `GET /api/dashboard/heatmap` (201), `GET /api/dashboard/alertas` (125).
- Tracebacks: `AttributeError: 'datetime.date' object has no attribute 'tzinfo'` en `dashboard.py::_naive` (llamado desde `pipeline`, `alertas` vía `_serialize_orden_breve`) y `AttributeError: 'datetime.date' object has no attribute 'date'` en `dashboard.py::heatmap`.
- Reproducido en local sobre SQLite el 2026-10-05: fallan además `GET /api/dashboard/kpis` (legacy, llama a `pipeline` y `alertas`). `hero`, `tendencia` y `tops` responden 200.

## Global Constraints

- Rama de trabajo: `worktree-hotfix-fechas-dashboard`, creada desde `origin/main` (`3f25ab7`, el commit desplegado). **No hacer push ni merge a `main`**: `main` autodespliega a Railway y la ventana de despliegue la decide el usuario.
- Cualquier decisión sobre un **día de calendario** usa `app.core.fechas.hoy_negocio()`; nunca `datetime.utcnow().date()`.
- `fecha_creacion` y `fecha_vencimiento` de `OrdenVenta` son `datetime.date`. No se convierten a `datetime` para operar: se restan contra otra `date`.
- Cambio mínimo: no refactorizar `dashboard.py` ni `ventas.py` más allá de lo que cada tarea indica. `hero`, `tendencia` y `tops` no se tocan.
- Sin cambios en `app/models/`, sin migraciones, sin cambios en `web/` ni en `app/static/dist/`.
- Antes de cada commit: `python3 -m pytest -q` y `python3 -m ruff check .` en verde. Línea base de la rama: `143 passed, 13 skipped`.
- Mensajes de commit en español, estilo del repo (`fix(dashboard): …`), terminados con la línea `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

1. **Cotización que vence hoy** — debe aparecer como "por vencer" con `dias_restantes == 0`, no como vencida, y debe salir en las alertas. (Pruebas en Task 1.)
2. **Cotización sin fecha de vencimiento** (`fecha_vencimiento` nulo) — no debe reventar; `dias_restantes` es `None`. (Prueba en Task 1.)
3. **Cliente sin cotizaciones** en `ultima-cotizacion-cliente` — responde 200 con `null`. (Prueba en Task 2.)
4. **Dos cotizaciones del mismo cliente el mismo día** — con `DATE` empatan en fecha; "la última" debe ser la de `id` mayor, no una arbitraria. (Prueba en Task 2.)
5. **Usuario con rol `ventas`** (ve solo lo suyo) — el dashboard responde 200 y no muestra cotizaciones de otro vendedor. (Prueba en Task 1.)

---

## File Structure

| Archivo | Responsabilidad | Tarea |
|---|---|---|
| `app/routers/dashboard.py` | `pipeline`, `alertas`, `heatmap` y `_serialize_orden_breve` operan en días de calendario | 1 |
| `tests/test_dashboard_fechas.py` (nuevo) | Barrido de todos los `GET /api/dashboard/*` con datos + reglas de clasificación por día | 1 |
| `app/routers/ventas.py` | `ultima_cotizacion_cliente` calcula `dias_atras` en días de calendario y desempata por `id` | 2 |
| `tests/test_ventas_ultima_cotizacion.py` (nuevo) | Contrato del widget "última cotización del cliente" | 2 |
| `docs/current-state/backlog.md` | Nota en el anexo "Cerrado" | 2 |

La Task 3 no edita archivos a mano: crea la rama de integración `integracion/mantenimiento-2026-10` y fusiona `worktree-auditoria-mutaciones`.

---

### Task 1: Dashboard — `pipeline`, `alertas` y `heatmap` en días de calendario

**Files:**
- Modify: `app/routers/dashboard.py` (imports; `_serialize_orden_breve`; `pipeline`; `alertas`; `heatmap`)
- Test: `tests/test_dashboard_fechas.py` (nuevo)

**Interfaces:**
- Consumes: `app.core.fechas.hoy_negocio() -> datetime.date`; fixtures `db` y `client_as(rol)` de `tests/conftest.py`; `tests.test_endpoints_autenticacion._rutas_api() -> list[tuple[str, str]]` (método, path) de todas las rutas de API montadas.
- Produces: nada que otra tarea consuma. El contrato JSON de los endpoints no cambia de forma (mismas claves); `fecha` en los items sigue siendo un string ISO, ahora siempre `YYYY-MM-DD`.

- [ ] **Step 1: Escribir las pruebas que fallan**

Crear `tests/test_dashboard_fechas.py` con este contenido exacto:

```python
"""El dashboard opera en días de calendario, no en instantes.

`ordenes_venta.fecha_creacion` y `fecha_vencimiento` son `DATE` desde
2026-08-06. El dashboard siguió tratándolas como `datetime` (`.tzinfo`,
`.date()`, resta contra `utcnow()`) y cinco endpoints devolvieron 500 en
producción durante semanas sin que ninguna prueba lo notara: no había ni una
sola prueba que tocara este router.

El barrido de abajo es el guardián de esa clase de fallo: recorre **todas** las
rutas GET del dashboard con datos reales en la base. Las pruebas siguientes
fijan la regla de negocio que el arreglo introduce: los días se cuentan contra
`hoy_negocio()`, así que una cotización que vence hoy está por vencer, no
vencida.
"""
from datetime import timedelta

from app import models
from app.core.fechas import hoy_negocio
from tests.test_endpoints_autenticacion import _rutas_api


def _cliente(db, nombre="ACME"):
    c = models.Cliente(nombre_empresa=nombre)
    db.add(c)
    db.commit()
    return c


def _cotizacion(client, db, cliente_id, *, creada_hace=0, vence_en=15):
    """Crea una cotización por la API y le fija sus dos fechas de calendario.

    `creada_hace`: días atrás respecto a hoy. `vence_en`: días hacia adelante
    (negativo = ya venció; `None` = sin fecha de vencimiento). Devuelve el id.
    """
    r = client.post("/api/ventas/", json={
        "cliente_id": cliente_id,
        "moneda": "MXN",
        "detalles": [{
            "cantidad": "1", "utilidad": "0", "descuento": "0",
            "costo_unitario": "100", "descripcion_libre": "Línea",
            "tipo_linea": "producto_fantasma",
        }],
    })
    assert r.status_code in (200, 201), r.text
    oid = r.json()["id"]
    hoy = hoy_negocio()
    orden = db.get(models.OrdenVenta, oid)
    orden.fecha_creacion = hoy - timedelta(days=creada_hace)
    orden.fecha_vencimiento = None if vence_en is None else hoy + timedelta(days=vence_en)
    db.commit()
    return oid


def _rutas_get_dashboard():
    return sorted(
        path for metodo, path in _rutas_api()
        if metodo == "GET" and path.startswith("/api/dashboard/") and "{" not in path
    )


def test_el_barrido_ve_las_rutas_del_dashboard():
    """Guarda del guardián: si el filtro deja de encontrar rutas, el barrido
    de abajo pasaría vacío y en silencio."""
    rutas = _rutas_get_dashboard()
    assert len(rutas) >= 7, rutas
    assert "/api/dashboard/pipeline" in rutas
    assert "/api/dashboard/heatmap" in rutas


def test_ningun_endpoint_del_dashboard_revienta_con_datos(db, client_as):
    """Con cotizaciones nuevas, en seguimiento, por vencer, vencidas y sin
    vencimiento en la base, todos los GET del dashboard responden 200."""
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=5)
    _cotizacion(c, db, cli.id, creada_hace=3, vence_en=2)
    _cotizacion(c, db, cli.id, creada_hace=20, vence_en=-1)
    _cotizacion(c, db, cli.id, creada_hace=2, vence_en=None)

    fallos = []
    for ruta in _rutas_get_dashboard():
        try:
            r = c.get(ruta)
        except Exception as exc:  # noqa: BLE001 — se reporta cuál ruta y por qué
            fallos.append(f"{ruta} → {type(exc).__name__}: {exc}")
            continue
        if r.status_code != 200:
            fallos.append(f"{ruta} → {r.status_code}")
    assert not fallos, "\n".join(fallos)


def test_pipeline_clasifica_por_dias_de_calendario(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    nueva = _cotizacion(c, db, cli.id)
    seguimiento = _cotizacion(c, db, cli.id, creada_hace=5)
    vence_hoy = _cotizacion(c, db, cli.id, creada_hace=3, vence_en=0)
    vencida = _cotizacion(c, db, cli.id, creada_hace=20, vence_en=-1)
    sin_vencimiento = _cotizacion(c, db, cli.id, creada_hace=2, vence_en=None)

    r = c.get("/api/dashboard/pipeline")
    assert r.status_code == 200, r.text
    p = r.json()

    def ids(columna):
        return {i["id"] for i in p[columna]["items"]}

    def item(columna, oid):
        return next(i for i in p[columna]["items"] if i["id"] == oid)

    assert ids("nueva") == {nueva}
    assert ids("seguimiento") == {seguimiento, sin_vencimiento}
    assert ids("por_vencer") == {vence_hoy}
    assert ids("vencida") == {vencida}

    assert item("nueva", nueva)["edad_dias"] == 0
    assert item("nueva", nueva)["fecha"] == hoy_negocio().isoformat()
    assert item("por_vencer", vence_hoy)["dias_restantes"] == 0
    assert item("por_vencer", vence_hoy)["edad_dias"] == 3
    assert item("vencida", vencida)["dias_restantes"] == -1
    assert item("vencida", vencida)["edad_dias"] == 20
    assert item("seguimiento", sin_vencimiento)["dias_restantes"] is None


def test_alertas_por_vencer_abarca_de_hoy_a_tres_dias(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    hoy = _cotizacion(c, db, cli.id, vence_en=0)
    en_dos = _cotizacion(c, db, cli.id, vence_en=2)
    en_tres = _cotizacion(c, db, cli.id, vence_en=3)
    _cotizacion(c, db, cli.id, vence_en=4)
    _cotizacion(c, db, cli.id, vence_en=-1)

    r = c.get("/api/dashboard/alertas")
    assert r.status_code == 200, r.text
    dias = {i["id"]: i["dias_restantes"] for i in r.json()["por_vencer_3d"]}

    assert dias == {hoy: 0, en_dos: 2, en_tres: 3}


def test_heatmap_cuenta_por_dia_de_negocio(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=3)
    _cotizacion(c, db, cli.id, creada_hace=10)  # fuera de la ventana de 7 días

    r = c.get("/api/dashboard/heatmap?dias=7")
    assert r.status_code == 200, r.text
    h = r.json()
    hoy = hoy_negocio()
    por_dia = {x["d"]: x["v"] for x in h["days"]}

    assert len(h["days"]) == 7
    assert h["days"][0]["d"] == (hoy - timedelta(days=6)).isoformat()
    assert h["days"][-1] == {"d": hoy.isoformat(), "v": 2}
    assert por_dia[(hoy - timedelta(days=3)).isoformat()] == 1
    assert h["total"] == 3
    assert h["max"] == 2


def test_el_vendedor_solo_ve_sus_cotizaciones_en_el_pipeline(db, client_as):
    admin = client_as("administrador")
    vendedor = client_as("ventas")
    cli = _cliente(db)
    _cotizacion(admin, db, cli.id)
    propia = _cotizacion(vendedor, db, cli.id)

    r = vendedor.get("/api/dashboard/pipeline")
    assert r.status_code == 200, r.text
    p = r.json()
    vistos = {i["id"] for columna in p.values() for i in columna["items"]}

    assert vistos == {propia}
```

- [ ] **Step 2: Correr las pruebas y confirmar que fallan por la causa correcta**

Run: `python3 -m pytest tests/test_dashboard_fechas.py -q`

Expected: `test_el_barrido_ve_las_rutas_del_dashboard` PASA (solo enumera rutas). Las otras cinco FALLAN con `AttributeError: 'datetime.date' object has no attribute 'tzinfo'` o `... has no attribute 'date'`. En el barrido, el mensaje debe listar `/api/dashboard/alertas`, `/api/dashboard/heatmap`, `/api/dashboard/kpis` y `/api/dashboard/pipeline`. Si alguna falla por otra causa (por ejemplo un 4xx al crear la cotización), detente y repórtalo: la prueba estaría mal, no el código.

- [ ] **Step 3: Corregir los imports de `app/routers/dashboard.py`**

Después de la línea `from app import models` hay un bloque de imports de `app`. Añadir el import de `hoy_negocio` manteniendo el orden alfabético del bloque:

```python
from app import models
from app.core.fechas import hoy_negocio
from app.db import get_db
from app.security import allow_all_staff, get_current_user
```

No tocar el import `from datetime import datetime, timedelta, timezone`: `datetime` y `timezone` siguen usándose en otros endpoints y en `_naive`.

- [ ] **Step 4: Corregir `_serialize_orden_breve`**

Reemplazar su primera línea de cuerpo. Antes:

```python
def _serialize_orden_breve(o: "models.OrdenVenta") -> dict:
    fc = _naive(o.fecha_creacion)
```

Después:

```python
def _serialize_orden_breve(o: "models.OrdenVenta") -> dict:
    fc = o.fecha_creacion  # DATE: ya es un día de calendario, no un instante
```

El resto de la función (incluido `"fecha": fc.isoformat() if fc else None`) queda igual.

- [ ] **Step 5: Corregir `pipeline`**

En la función `pipeline`, reemplazar `now = datetime.utcnow()` por `hoy = hoy_negocio()` y usar `hoy` en los tres sitios donde se usaba `now`. Estado final de los fragmentos que cambian:

```python
    hoy = hoy_negocio()
```

```python
            models.OrdenVenta.fecha_creacion >= hoy - timedelta(days=30),
```

```python
    for o in abiertas:
        fc = o.fecha_creacion
        fv = o.fecha_vencimiento
        edad = (hoy - fc).days if fc else 0
        dias_rest = (fv - hoy).days if fv else None
```

No debe quedar ninguna referencia a `now` dentro de `pipeline` (ruff marcaría la variable sin usar). La clasificación en columnas que sigue no cambia.

- [ ] **Step 6: Corregir `alertas`**

En `alertas` se conserva `now = datetime.utcnow()` porque más abajo se usa contra `ultimo_abono.fecha`, que sí es un instante (`DateTime(timezone=True)`), y `_naive` sigue siendo correcto ahí. Añadir `hoy` justo debajo y usarlo en el bloque de cotizaciones por vencer. Estado final:

```python
    now = datetime.utcnow()
    hoy = hoy_negocio()

    por_vencer = _scope(
        db.query(models.OrdenVenta).filter(
            models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_vencimiento.is_not(None),
            models.OrdenVenta.fecha_vencimiento >= hoy,
            models.OrdenVenta.fecha_vencimiento <= hoy + timedelta(days=3),
        ),
        current_user,
    ).order_by(models.OrdenVenta.fecha_vencimiento.asc()).limit(15).all()

    por_vencer_items = []
    for o in por_vencer:
        item = _serialize_orden_breve(o)
        fv = o.fecha_vencimiento
        item["dias_restantes"] = (fv - hoy).days if fv else None
        por_vencer_items.append(item)
```

No tocar el bloque de `saldos_vencidos` (`ultima_fecha = _naive(ultimo_abono.fecha) ...`, `dias = (now - ultima_fecha).days`).

- [ ] **Step 7: Corregir `heatmap`**

Reemplazar el cuerpo desde `now = datetime.utcnow()` hasta el final del bucle que arma `series`. Estado final:

```python
    hoy = hoy_negocio()
    start = hoy - timedelta(days=dias - 1)

    rows = _scope(
        db.query(models.OrdenVenta.fecha_creacion).filter(
            models.OrdenVenta.fecha_creacion >= start,
        ),
        current_user,
    ).all()

    counts: dict[str, int] = defaultdict(int)
    for (f,) in rows:
        if f is None:
            continue
        counts[f.isoformat()] += 1

    series = []
    for i in range(dias):
        d = (start + timedelta(days=i)).isoformat()
        series.append({"d": d, "v": counts.get(d, 0)})
```

El `return` de `heatmap` no cambia.

- [ ] **Step 8: Correr las pruebas nuevas**

Run: `python3 -m pytest tests/test_dashboard_fechas.py -q`
Expected: `6 passed`.

- [ ] **Step 9: Suite completa y lint**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: `149 passed, 13 skipped` y `All checks passed!`.

- [ ] **Step 10: Commit**

```bash
git add app/routers/dashboard.py tests/test_dashboard_fechas.py
git commit -m "fix(dashboard): pipeline, alertas y heatmap devolvían 500 desde el paso de las fechas a DATE

fecha_creacion y fecha_vencimiento son DATE desde b0c5878, pero el dashboard
las seguía tratando como instantes (.tzinfo, .date(), resta contra utcnow).
Producción acumuló 859 respuestas 500 entre el 7-sep y el 2-oct.

Los días ahora se cuentan contra hoy_negocio(): una cotización que vence hoy
está por vencer (0 días), no vencida. El barrido nuevo recorre todos los GET
del dashboard con datos; este router no tenía ni una prueba.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Cotizador — `ultima-cotizacion-cliente` en días de calendario

**Files:**
- Modify: `app/routers/ventas.py` (función `ultima_cotizacion_cliente`, al final del archivo; localizar con `grep -n "def ultima_cotizacion_cliente" app/routers/ventas.py`)
- Modify: `docs/current-state/backlog.md` (anexo "Cerrado", al final del archivo)
- Test: `tests/test_ventas_ultima_cotizacion.py` (nuevo)

**Interfaces:**
- Consumes: `hoy_negocio` (ya importado en `ventas.py`: `from app.core.fechas import hoy_negocio`); `desc` (ya importado en `ventas.py`); fixtures `db` y `client_as`.
- Produces: nada que otra tarea consuma. El JSON del endpoint conserva sus claves: `id`, `folio`, `fecha`, `dias_atras`, `total`, `moneda`, `estatus`.

- [ ] **Step 1: Escribir las pruebas que fallan**

Crear `tests/test_ventas_ultima_cotizacion.py` con este contenido exacto:

```python
"""Widget "última cotización de este cliente" del cotizador.

Devolvió 500 en producción desde que `fecha_creacion` pasó a `DATE`: el
endpoint le pedía `.tzinfo` a un `date` y luego lo restaba de `utcnow()`.
Fue el más golpeado de los cinco (332 de 859 errores en cuatro semanas),
porque se consulta cada vez que alguien elige un cliente en el cotizador.

Además del 500, `DATE` trajo un empate que antes no existía: dos cotizaciones
del mismo cliente el mismo día tienen la misma fecha, así que "la última"
necesita desempatar por id.
"""
from datetime import timedelta

from app import models
from app.core.fechas import hoy_negocio


def _cliente(db, nombre="ACME"):
    c = models.Cliente(nombre_empresa=nombre)
    db.add(c)
    db.commit()
    return c


def _cotizacion(client, db, cliente_id, *, creada_hace=0):
    r = client.post("/api/ventas/", json={
        "cliente_id": cliente_id,
        "moneda": "MXN",
        "detalles": [{
            "cantidad": "1", "utilidad": "0", "descuento": "0",
            "costo_unitario": "100", "descripcion_libre": "Línea",
            "tipo_linea": "producto_fantasma",
        }],
    })
    assert r.status_code in (200, 201), r.text
    data = r.json()
    orden = db.get(models.OrdenVenta, data["id"])
    orden.fecha_creacion = hoy_negocio() - timedelta(days=creada_hace)
    db.commit()
    return data


def test_cliente_sin_cotizaciones_devuelve_null(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    assert r.json() is None


def test_cotizacion_de_hoy_tiene_cero_dias(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    cot = _cotizacion(c, db, cli.id)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == cot["id"]
    assert data["folio"] == cot["folio"]
    assert data["fecha"] == hoy_negocio().isoformat()
    assert data["dias_atras"] == 0
    assert data["moneda"] == "MXN"


def test_dias_atras_cuenta_dias_de_calendario(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id, creada_hace=3)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    assert r.json()["dias_atras"] == 3


def test_dos_cotizaciones_el_mismo_dia_gana_la_mas_reciente(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    segunda = _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=4)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    assert r.json()["id"] == segunda["id"]
```

- [ ] **Step 2: Correr las pruebas y confirmar que fallan por la causa correcta**

Run: `python3 -m pytest tests/test_ventas_ultima_cotizacion.py -q`

Expected: `test_cliente_sin_cotizaciones_devuelve_null` PASA (el endpoint sale antes de tocar la fecha). Las otras tres FALLAN con `AttributeError: 'datetime.date' object has no attribute 'tzinfo'`. Si fallan por otra causa, detente y repórtalo.

- [ ] **Step 3: Corregir `ultima_cotizacion_cliente`**

En `app/routers/ventas.py`, dentro de `ultima_cotizacion_cliente`, reemplazar estas cinco líneas:

```python
    o = q.order_by(desc(models.OrdenVenta.fecha_creacion)).first()
    if not o:
        return None
    fc = o.fecha_creacion.replace(tzinfo=None) if o.fecha_creacion and o.fecha_creacion.tzinfo else o.fecha_creacion
    dias = (datetime.utcnow() - fc).days if fc else None
```

por:

```python
    # `fecha_creacion` es DATE: dos cotizaciones del mismo día empatan, y el id
    # es lo que dice cuál se capturó después.
    o = q.order_by(desc(models.OrdenVenta.fecha_creacion), desc(models.OrdenVenta.id)).first()
    if not o:
        return None
    dias = (hoy_negocio() - o.fecha_creacion).days if o.fecha_creacion else None
```

El `return {...}` que sigue no cambia. No tocar los imports: `datetime` sigue usándose en otras partes del archivo (si `ruff` reporta lo contrario en el Step 5, quitar solo el nombre que señale).

- [ ] **Step 4: Correr las pruebas nuevas**

Run: `python3 -m pytest tests/test_ventas_ultima_cotizacion.py -q`
Expected: `4 passed`.

- [ ] **Step 5: Suite completa y lint**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: `153 passed, 13 skipped` y `All checks passed!`.

- [ ] **Step 6: Anotar el cierre en el backlog**

En `docs/current-state/backlog.md`, dentro del anexo final "Cerrado", insertar este párrafo inmediatamente después del párrafo que empieza con `**Fechas** — corregido de raíz.` (y antes del que empieza con `**Lint e higiene**`), dejando una línea en blanco antes y después:

```markdown
**Fechas, segunda parte (2026-10-05)** — el paso a `DATE` dejó cinco endpoints tratando la fecha como instante: `pipeline`, `alertas`, `heatmap` y `kpis` del dashboard, y `ultima-cotizacion-cliente` del cotizador. Devolvieron 500 en producción desde el despliegue del 6 de agosto; los logs de Railway conservan **859 errores entre el 7 de septiembre y el 2 de octubre**. Nadie lo reportó y ninguna prueba lo vio, porque `dashboard.py` no tenía ni una. Corregido contando días de calendario contra `hoy_negocio()`; el guardián es un barrido de todos los GET del dashboard con datos (`tests/test_dashboard_fechas.py`). Queda una lección operativa: **nadie mira los logs de producción** — el hallazgo salió de una revisión manual dos meses después.
```

- [ ] **Step 7: Commit**

```bash
git add app/routers/ventas.py tests/test_ventas_ultima_cotizacion.py docs/current-state/backlog.md
git commit -m "fix(cotizador): la última cotización del cliente devolvía 500

Mismo origen que el dashboard: el endpoint le pedía .tzinfo a un date. Fue el
más golpeado (332 de 859 errores), porque se consulta al elegir cliente.

dias_atras se cuenta contra hoy_negocio() y, como DATE hace empatar a las
cotizaciones del mismo día, el orden desempata por id.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Rama de integración con la auditoría de mutaciones

**Contexto:** `worktree-auditoria-mutaciones` contiene la Ola 4 E5 (tabla `audit_log`, `audit_service`, captura en 7 puntos, consola, 18 pruebas y el build de la SPA). Está terminada y con revisión final "Ready to merge" desde 2026-08-20, pero nunca se integró. Esta tarea **no la re-revisa**: la junta con el hotfix en una rama aparte y demuestra con evidencia que la combinación está sana. La rama del hotfix queda intacta para poder desplegarla sola.

**Files:**
- No se editan archivos a mano salvo para resolver conflictos de merge, si los hay. El único archivo que ambas ramas tocan es `docs/current-state/backlog.md` (el hotfix añade un párrafo en el anexo final; la auditoría edita dos viñetas más arriba).

**Interfaces:**
- Consumes: la rama `worktree-hotfix-fechas-dashboard` con las Tasks 1 y 2 commiteadas; la rama local `worktree-auditoria-mutaciones` (HEAD `6371215`).
- Produces: la rama local `integracion/mantenimiento-2026-10` y un reporte con la salida de cada verificación.

- [ ] **Step 1: Crear la rama de integración desde el hotfix**

```bash
git status --short            # debe estar vacío
git switch -c integracion/mantenimiento-2026-10
```

- [ ] **Step 2: Fusionar la auditoría**

```bash
git merge --no-ff worktree-auditoria-mutaciones -m "merge: auditoría de mutaciones (Ola 4 E5) sobre el hotfix de fechas

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Expected: merge limpio. Si `docs/current-state/backlog.md` entra en conflicto, resolver **conservando ambos lados** (las dos viñetas tachadas de la auditoría y el párrafo "Fechas, segunda parte" del hotfix), luego `git add docs/current-state/backlog.md && git commit --no-edit`. Cualquier conflicto en otro archivo: abortar con `git merge --abort` y reportar BLOCKED con la lista de archivos.

- [ ] **Step 3: Verificar que el hotfix sobrevivió al merge**

```bash
grep -c "hoy_negocio" app/routers/dashboard.py     # esperado: 4
grep -n "_naive(o.fecha" app/routers/dashboard.py  # esperado: sin resultados
grep -n "Fechas, segunda parte" docs/current-state/backlog.md   # esperado: 1 línea
```

- [ ] **Step 4: Backend — suite completa, lint y sintaxis**

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m compileall -q app
```

Expected: pytest sin fallos. El total esperado es la suma de ambas ramas: **171 passed, 13 skipped** (153 del hotfix + 18 de la auditoría). Si el conteo difiere pero no hay fallos, reportar el número real. ruff: `All checks passed!`. compileall: sin salida.

- [ ] **Step 5: Frontend — typecheck, pruebas y build**

El worktree no tiene `node_modules`. `web/package.json` y `web/package-lock.json` son idénticos en ambas ramas, así que se reutiliza la instalación del checkout principal con un enlace simbólico (está ignorado por git):

```bash
ln -s /mnt/d/Devs/dasic-atlas-api/web/node_modules web/node_modules
cd web && npm run typecheck && npm run test && npm run build; cd ..
git status --short
```

Expected: typecheck sin errores; vitest en verde; build exitoso. `git status --short` debe quedar **vacío**: el `app/static/dist/` commiteado por la auditoría tiene que coincidir con lo que produce el build. Si el build deja diferencias en `app/static/dist/`, **no las commitees**: lista los archivos que cambiaron y repórtalo como DONE_WITH_CONCERNS (puede ser solo ruido de hashes o puede indicar un `dist` desactualizado; lo decide el controlador). Al terminar, quitar el enlace: `rm web/node_modules`.

- [ ] **Step 6: Confirmar el estado final de las ramas**

```bash
git log --oneline -4
git log --oneline origin/main..integracion/mantenimiento-2026-10 | wc -l
git log --oneline origin/main..worktree-hotfix-fechas-dashboard | wc -l
git status --short
```

Expected: la rama de integración contiene los commits del hotfix, los de la auditoría y el commit de merge; la del hotfix sigue con solo sus commits; árbol limpio. **No hacer push de ninguna rama.**
