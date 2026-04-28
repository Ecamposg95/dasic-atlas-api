# Estado Actual del Repo (Dasic_Atlas_api)

> **Actualizado:** 2026-04-28 (Post-RBAC fase 1, catalogo fase 1, cotizador fase 2, seguimiento inicial)

Este repositorio ya no está solo en etapa de refactor base. La rama activa de referencia es `main` y ahora contiene un primer bloque funcional orientado a la operación comercial real de DASIC: RBAC transicional, catálogo costo-first, cotizador multimoneda basado en utilidad y seguimiento de cotizaciones con borrador de OC.

## Estructura Actual (Refactorizada)

**Core y Bootstrap:**
- `app/main.py`: Limpio (~90 líneas). Solo bootstrap de FastAPI, montado de SSR y middlewares.
- `app/core/lifespan.py`: Maneja los eventos de startup de manera moderna (reemplaza `@on_event`).
- `app/core/logging.py`: Configuración central de logging estructurado.

**Base de Datos y Modelos:**
- `app/db/session.py` (y `db/__init__.py`): Manejan el session engine de SQLAlchemy para PostgreSQL.
- `app/db/seeds.py`: Rutinas de backfill retroactivo de DDL y creación de tenant base en el startup.
- `app/models/`: Separado por dominio de negocio (`nucleus.py`, `users.py`, `catalog.py`, `clients.py`, `sales.py`, `purchases.py`, `finance.py`, `enums.py`).
- `app/schemas/`: Espejeado con los subdominios de los modelos para Pydantic.

**API y SSR:**
- `app/routers/`: Mantienen endpoints por áreas (próximo a incorporar capa de Repositories).
- `app/templates/`: Vistas de SSR con Jinja2 (dashboard, cotizador, inventario, clientes, etc).
- `app/static/`: Assets crudos CSS/JS. **Se usa Tailwind CDN y Alpine.js** globalmente.

## Cumplimiento con DASIC_Plataforma_Base

Se ha consolidado el documento `context/DASIC_Plataforma_Base.md` que detalla el Plan de Operaciones a 90 días:
1. **Live Stock:** Kardex, inventario en tiempo real, banderas de stock crítico.
2. **Smart Quoter:** Generar cotizaciones en < 10 mins con reservas por 48 horas de stock.
3. **Dashboard:** Para Dirección General y KPIs.

## Lanes Cerrados en Esta Sesion

### 1. RBAC fase 1 segura

- `app/models/enums.py` y `app/security/jwt.py` quedaron alineados a vocabulario canonico:
  - `ADMINISTRADOR`
  - `GERENTE_COMERCIAL`
  - `VENTAS`
- Se mantuvo compatibilidad con roles legacy:
  - `ADMIN`
  - `ASISTENTE`
  - `VENDEDOR`
- `app/templates/usuarios.html` y `app/routers/usuarios.py` ya reflejan esa fase 1.
- Se aplico hotfix adicional en `app/models/users.py` para aceptar aliases legacy al leer filas existentes desde Railway (`omit_aliases=False`).

### 2. Catalogo / inventario fase 1

- `app/models/catalog.py` agrega:
  - `sku_comercial`
  - `moneda_compra`
- `precio_publico` deja de ser obligatorio en el contrato API, pero se mantiene compatibilidad con el cotizador legacy.
- Existe migracion:
  - `migrations/versions/20260428_01_catalog_purchase_currency.py`
- `app/templates/inventario.html` tolera mejor productos sin precio publico fijo.

### 3. Cotizador fase 2

- `app/models/sales.py` ahora persiste:
  - `moneda`
  - `tipo_cambio`
  - `utilidad_aplicada`
- `app/schemas/sales.py` y `app/routers/ventas.py` ya trabajan con cotizacion basada en:
  - `costo_compra + utilidad`
  - no `precio_publico - descuento`
- El PDF de cotizacion ya refleja la moneda real (`MXN` / `USD`) y el tipo de cambio cuando aplica.
- Existe migracion:
  - `migrations/versions/20260428_02_sales_quote_currency.py`

### 4. Seguimiento comercial inicial

- `/api/ventas/historial` ya expone datos de vigencia/antiguedad:
  - `fecha_vencimiento`
  - `edad_dias`
  - `dias_restantes`
  - `esta_vencida`
- `app/templates/seguimiento.html` ya muestra seguimiento read-only con filtros de vigencia.
- `app/routers/compras.py` expone:
  - `GET /api/compras/cotizacion/{quote_id}/borrador`
- Ese endpoint genera un borrador de OC sin persistir compra, sin mover stock y sin crear cuentas por pagar.

### 5. Hotfixes de despliegue cerrados

- `app/main.py` fue corregido para usar la firma correcta de `Jinja2Templates.TemplateResponse(...)`.
- `app/models/users.py` fue corregido para que Railway no truene al leer enums legacy en `usuarios.rol`.

## Riesgos Actuales

1. **RBAC incompleto:** la fase actual es solo de vocabulario/plataforma. Todavia no existe enforcement real tenant-aware usando `UserOrganization`.
2. **Compatibilidad transicional:** el sistema sigue conviviendo con datos y helpers legacy. Funciona, pero no es el estado final.
3. **Routers muy cargados:** `app/routers/ventas.py`, `app/routers/productos.py` y `app/routers/compras.py` siguen mezclando dominio, persistencia y presentacion.
4. **Cobertura de pruebas baja:** se validaron cambios con `py_compile` y checks de diff, pero no hay suite automatizada fuerte para regresiones funcionales.

## Siguientes Fases Recomendadas

1. **Folios y recotizaciones**
   - folio por año/mes/usuario
   - versionado de cotizaciones
   - trazabilidad de recotizacion
2. **Orden de compra real desde cotizacion**
   - pasar de borrador a persistencia real
   - relacionar cotizacion y OC
   - seleccionar proveedor de forma segura
3. **Correo + tracking**
   - envio de cotizaciones
   - bitacora de envios
   - KPIs simples de entrega
4. **Dashboard operativo**
   - cotizaciones activas
   - vencidas / por vencer
   - stock critico
   - OC generadas / pendientes
5. **Capa repository / services**
   - extraer logica pesada fuera de routers
6. **RBAC tenant real**
   - usar `UserOrganization` para autorizacion
   - branch scope y visibilidad por ownership
