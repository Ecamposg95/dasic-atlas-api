# Auditoría de mutaciones — diseño (Ola 4 · E5)

**Fecha:** 2026-08-20 · **Estado:** aprobado en chat, pendiente de implementación
**Origen:** `docs/current-state/backlog.md` P1/Ola 4 — "hoy borrar un cliente, cambiar un precio o ajustar stock no dejan rastro: el mayor hueco de gobernanza del sistema".

## 1. Problema y hallazgo previo

La consola de auditoría (`GET /api/superadmin/audit`) normaliza hoy dos fuentes: `quote_events` (cotizaciones) y `cliente_merge_log` (fusiones). Todo lo demás muta sin rastro.

**Hallazgo que acota el problema:** los ajustes de stock **ya dejan rastro** — `movimientos_stock` registra tipo AJUSTE con `usuario_id` y `motivo` vía `stock_service.aplicar_movimiento`. Ahí el hueco es de *exposición* (la consola no los muestra), no de captura. Los huecos reales de captura son los deletes y las ediciones sensibles.

## 2. Alcance (decisión del usuario: "núcleo de gobernanza")

**Captura nueva (7 puntos):**

| Router | Endpoint | Acción registrada |
|---|---|---|
| `clientes.py` | `DELETE /{cliente_id}` | `eliminar` cliente — resumen con nombre, RFC y saldo |
| `clientes.py` | `DELETE /{cliente_id}/contactos/{contacto_id}` | `eliminar` contacto |
| `productos.py` | `DELETE /{id}` | `eliminar` producto — resumen con SKU y nombre |
| `productos.py` | `PUT` (update) | `cambio_precio` **solo si** cambió `costo_compra`, `moneda_compra` o `precio_publico`; diff viejo→nuevo en `datos` |
| `gastos.py` | `DELETE /{id}` | `eliminar` gasto — resumen con concepto y monto |
| `usuarios.py` | alta / edición | `crear` usuario; `cambio_rol` si cambió el rol; `desactivar` si `activo` pasó a falso |
| `usuarios.py` | `DELETE /{user_id}` | `eliminar` usuario |

**Exposición nueva (sin captura):** los `movimientos_stock` tipo AJUSTE se normalizan como fuente `stock` en la consola.

**Fuera de alcance (explícito):** deals/CRM, servicios, plantas, recordatorios, marcas, plantillas (candidatos a una segunda pasada con la misma mecánica); justificación obligatoria para cambios de precio (invariante 11 completo — pertenece al backlog CPQ); retención/purga de la bitácora; `POST /productos/upload-csv` (mutación masiva — un evento por fila inundaría la bitácora; auditarla pide un evento-resumen propio, segunda pasada); `POST /usuarios/{id}/password` (candidato a segunda pasada).

## 3. Enfoque elegido

**Tabla genérica + servicio explícito.** Se descartaron: listeners automáticos de SQLAlchemy (la sesión no conoce al usuario del request; ruido de seeds/backfill) y tablas por dominio (cada fuente exigiría tabla + normalizador propios).

## 4. Diseño

### 4.1 Modelo — `app/models/audit.py::AuditLog` (tabla `audit_log`)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | |
| `fecha` | DateTime, `server_default=func.now()`, NOT NULL | |
| `usuario_id` | Integer FK `usuarios.id`, nullable | quién ejecutó |
| `accion` | String(40) NOT NULL | `eliminar` · `cambio_precio` · `cambio_rol` · `desactivar` · `crear` |
| `entidad` | String(40) NOT NULL | `cliente` · `contacto` · `producto` · `gasto` · `usuario` |
| `entidad_id` | Integer, nullable | id del registro afectado (sin FK: la entidad puede ya no existir) |
| `resumen` | String(400) NOT NULL | frase legible para la consola |
| `datos` | Text, nullable | JSON con contexto (diff viejo→nuevo, atributos del registro borrado) |

Índices: `fecha`, `(entidad, entidad_id)`, `usuario_id`. Re-export en `app/models/__init__.py` y schema en `app/schemas/` según convención.

- **Migración:** revisión Alembic. Al ser **tabla nueva**, `create_all()` del lifespan la crea en producción; `_BACKFILL_DDL` no aplica (es para columnas sobre tablas existentes).
- **Sin `organization_id`:** la decisión de producto 2026-08-19 (mono-empresa DASIC, sin camino SaaS) supersede el invariante 15 del spec del golden path (2026-08-05), que pedía `organization_id` en toda tabla nueva.

### 4.2 Servicio — `app/services/audit_service.py`

```python
def registrar(db, *, usuario, accion, entidad, entidad_id, resumen, datos=None) -> AuditLog
```

Hace `db.add(...)` y **no hace commit**: participa en la transacción del caller, de modo que el evento se persiste atómicamente con la mutación (y se revierte con ella). `datos` acepta dict y se serializa a JSON. `usuario` puede ser None (acciones de sistema).

### 4.3 Captura en routers

Cada endpoint del alcance llama a `registrar(...)` **antes del commit**, dentro de la misma transacción, con el snapshot leído antes de mutar (para deletes: capturar los atributos del registro antes de borrarlo). En `productos.py`, el update compara los tres campos sensibles contra el estado previo y solo registra si hubo cambio real.

### 4.4 Consola — `GET /api/superadmin/audit`

- El parámetro `fuente` amplía su `Literal` a `"cotizacion" | "fusion_cliente" | "sistema" | "stock"`.
- Fuente `sistema`: filas de `audit_log`, normalizadas a `AuditEvent` (mismo shape actual: fuente/fecha/usuario/accion/entidad/detalle/link). Link según entidad cuando el destino existe (`/spa/clientes?id=…`, `/spa/productos`…).
- Fuente `stock`: `movimientos_stock` con `tipo == AJUSTE`, resumen con producto, delta y motivo; batch de nombres de usuario y productos sin N+1, siguiendo el patrón del endpoint.
- Frontend: `web/src/features/superadmin` — el filtro de fuente de la página de Auditoría gana las dos opciones nuevas. Sin más UI.

### 4.5 Permisos

Sin cambios: la captura corre server-side dentro de endpoints ya protegidos; la consola sigue `allow_superadmin`.

## 5. Pruebas (TDD, pytest)

1. `registrar` persiste con el commit del caller y **se revierte** si la transacción falla (atomicidad).
2. `DELETE` de cliente genera evento con resumen que incluye nombre/RFC/saldo; el cliente borrado no rompe la consola (entidad_id sin FK).
3. Update de producto **con** cambio de costo genera `cambio_precio` con diff correcto; update **sin** cambio de precio no genera evento.
4. Alta de usuario, cambio de rol y desactivación generan sus acciones respectivas.
5. `GET /audit` devuelve y filtra las fuentes `sistema` y `stock` normalizadas; el filtro `usuario_id` aplica a ambas.

Frontend: typecheck + build (el cambio de UI es un filtro).

## 6. Deuda anotada (consciente, fuera de esta entrega)

- `get_audit` carga todas las fuentes en memoria y pagina ahí. Con `audit_log` creciendo, migrar a paginación en SQL (o a una vista UNION) será necesario; se mantiene el patrón actual para no mezclar refactor con feature.
- Segunda pasada de captura (deals, servicios, plantas, etc.) reutiliza `registrar` tal cual.

## 7. Rollback

Tabla nueva sin dependencias entrantes: revertir es `alembic downgrade -1` (o ignorar la tabla). Los routers solo añaden llamadas a `registrar`; revertir el commit de código basta.
