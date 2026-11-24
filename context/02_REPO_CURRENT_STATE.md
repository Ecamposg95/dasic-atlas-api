# Estado Actual del Repo (dasic-atlas-api / Atlas ONE)

> **Actualizado:** 2026-11-23. Rama de referencia: `main` (autodeploy a Railway). Último cambio de código: 2026-10-05 (PR #8).
> Fuente de verdad del stack: `CLAUDE.md` (raíz) + `docs/Atlas-ONE-Proyecto.md`.

Es un **ERP/CRM en producción**: SPA React (migrada 2026-05-22) sobre FastAPI, con design system CIRCUITO, CRM v2, cotizador robusto, remisiones v2 con arquitectura por dominios, centro de cobranza, base instalada y consola de plataforma (super-admin). **Mono-tenant** — `app/models/nucleus.py` (Organization/Branch/UserOrganization) fue retirado; solo quedan columnas `organization_id` inertes.

## Cifras (verificadas 2026-11-23)

| | |
|---|---|
| Routers `app/routers/` | 24 (+ el router del dominio remisiones) |
| Dominios `app/domains/` | 1 (`remisiones`) |
| Modelos `app/models/` | 24 módulos de dominio (+ `__init__`), incluye `audit.py` |
| Servicios `app/services/` | 12 |
| Revisiones Alembic | 55 |
| Features SPA `web/src/features/` | 25 · 35 páginas |
| Primitivas `web/src/components/ui/` | 24 |
| Tests backend (`pytest`) | 185 funciones de prueba en `tests/` (28 archivos) |
| Tests frontend (`vitest`) | 117 bloques `it`/`test` en 9 archivos |
| Templates Jinja `app/templates/` | 20 (respaldo histórico, `_SSR_ROUTES` vacía) |

## Stack (resumen — ver `CLAUDE.md` para detalle)

- **Backend:** FastAPI + SQLAlchemy 2.x + Alembic + PostgreSQL (`psycopg`), Python 3.11 (`runtime.txt`).
- **Frontend:** SPA React 18 + Vite 5 + TypeScript + Tailwind (compilado) + shadcn/ui + Zustand + TanStack Query v5 + React Router v6 + recharts + `@dnd-kit`, en `web/src/features/<x>/`. Build a `app/static/dist/` (commiteado).
- **Auth:** JWT en cookie HttpOnly `access_token`.
- **Tests:** `pytest` (backend; SQLite en memoria sin `TEST_DATABASE_URL`, PostgreSQL real con ella — así corre CI) + `vitest` (frontend, colocated, con jsdom por archivo para componentes). **CI** (`.github/workflows/ci.yml`) corre ruff + pytest sobre PostgreSQL 16 + typecheck + vitest + build en cada push y PR; valida pero **no bloquea** el deploy. `pytest` vive en `requirements-dev.txt`, no en `requirements.txt` (Railway no lo instala).
- **Deploy:** Railway (builder **Railpack**: solo instala dependencias Python; **NO compila la SPA** → el `app/static/dist/` commiteado ES el frontend de producción); Procfile = `uvicorn`. **Alembic NO corre en deploy** → shim `_BACKFILL_DDL` para columnas en tablas existentes; `create_all()` en lifespan crea tablas nuevas.

## Arquitectura por dominios (patrón vigente para módulos nuevos)

`app/domains/remisiones/` = `router.py` (HTTP/permisos) · `service.py` (reglas + transacciones) · `repository.py` (queries) · `schemas.py` · `documents.py` · `templates/`. El router legacy `app/routers/remisiones.py` fue **retirado**. Todo módulo nuevo va aquí; `ventas.py`/`productos.py`/`compras.py` siguen gordos y se migrarán por dominio.

## Qué está construido (módulos en producción)

**Comercial:** Dashboard (KPIs + recharts + panel recordatorios) · **CRM v2** (Kanban DnD + detalle de deal `/spa/crm/deals/:id`, actividades con timeline automático de eventos `sistema`, métricas de conversión por etapa con `tasa_ganado_pct`, CRUD/reorden de etapas, deal→cotización con re-vinculación automática) · **Cotizador** (costo+utilidad, multimoneda direccional, plantillas, recotización versionada, PDF desglose/unificado + Word + remisión + reporte de servicio, fase 1 móvil) · Borradores · Seguimiento · **Recordatorios** · Clientes/Empresas + Contactos (detalle en 8 tabs, dedup, estado de cuenta + PDF) · **Base instalada** (`Planta` + `ActivoInstalado` con garantía y estado, tabs Plantas/Activos en el detalle de empresa).

**Operación:** Compras (OC desde cotización) · Fantasmas (promover a producto) · **Remisiones v2** (ver abajo) · Reportes de servicio · Gastos.

**Catálogo:** Inventario (costo-first, kardex auditable, reservas, import Excel) · Servicios · Precios proveedor · Diccionarios (marcas/categorías + **catálogo administrable `unidades_medida`** + navegador SAT).

**Finanzas:** Centro de cobranza (aging 0-30/31-60/61-90/90+, top deudores, pago distribuido FIFO, estado de cuenta PDF) · FX (Banxico + fallback, override manual).

**Reportes:** `/spa/analitica` con tabs `ventas`/`operativo` (las rutas viejas `/spa/reportes` y `/spa/reportes-servicio` redirigen ahí).

**Marca (2026-11-24):** la app conserva la paleta esmeralda de DASIC; Atlas Tech firma el producto. Tipografía Inter + JetBrains Mono, lockup de Atlas en login, sidebar y pie (`web/src/components/brand/Atlas.tsx`), favicon con la marca. La consola de plataforma y la pantalla de acceso suspendido usan la identidad de Atlas (Niebla en tema claro, Horizon en oscuro) mediante la clase `.atlas-console` en `<html>`, que redefine los tokens semánticos y `accent-glow`/`accent-deep` (ahora CSS vars). Los colores de marca viven en `tailwind.config.ts` como `atlas-*` y **solo** se usan para la firma de Atlas y la consola. Reglas de marca: skill `atlas-tech-brand`.

**Plataforma (Consola Super-Admin, solo dev — skin propio vía `PlatformShell`):** Usuarios de plataforma (CRUD + rol superadmin, blindajes anti-escalada) · **Acceso a la plataforma** (interruptor suspender/reactivar en `/spa/superadmin/acceso`: con la plataforma suspendida todo usuario que no sea SUPERADMIN recibe 423 en el login y en cualquier endpoint autenticado, y la SPA muestra la pantalla de suspensión; estado en `platform_config`, sin redeploy — `app/services/acceso_service.py`) · Configuración runtime (IVA/vigencia/tolerancia TC sin redeploy) · Auditoría global (`audit_log` + `audit_service`: deletes de cliente/contacto/producto/gasto, cambios de precio, ciclo de vida de usuarios, ajustes de stock) · Salud del sistema · Mantenimiento (re-seeds, jobs, seed-context, zona roja drop-all-tables con doble guarda).

## Remisiones v2

- **Estados** `EstadoRemision`: `BORRADOR → EMITIDA → RECIBIDA`, con `CANCELADA` como salida. Emisión asigna folio bajo `pg_advisory_xact_lock` y descuenta stock; cancelación revierte.
- **Patrón lock → refresh → re-check** en toda mutación con estado (evita TOCTOU), con 404 explícito si la fila fue borrada durante la espera del lock.
- **Entregas parciales con acumulados:** `repository.entregado_por_detalle` / `pendientes_por_detalle`; emitir sobre el pendiente exige sobre-entrega autorizada. Stock híbrido: solo mueven inventario las líneas ligadas a partida de orden con producto real.
- **Unidades comerciales:** `cantidad` en `Numeric(12,3)`; `unidad` es snapshot string del catálogo `unidades_medida`. Documentos formatean a máx. 2 decimales (`app/services/formato.py`).
- **Remisión → cotización:** `POST /api/remisiones/{id}/crear-cotizacion`.
- **Editor híbrido:** `/spa/remisiones` **es el editor** (espejo del cotizador, comparte `web/src/components/document/`); historial en `/spa/remisiones/historial`; `/spa/remisiones/:id/editar`; `/spa/remisiones-nueva?orden=N` redirige conservando el query string.
- **Documentos** desde plantillas en archivo (branding configurable, marca de agua en borrador), PDF/HTML imprimible + Word.
- **Permisos:** recurso `remision` en la matriz (`read/create/emitir/recibir/cancel/sobreentrega/convertir`) con owner-scoping para VENTAS.

## Design system CIRCUITO (2026-08-04)

Reemplaza el "premium cyan" del 2026-06-04. Acento **esmeralda técnica `#2ee6a8`**; **sidebar negro absoluto en ambos temas** (solo el contenido responde a claro/oscuro). Tokens semánticos HSL en `web/src/index.css` + `tailwind.config.ts` (light = neutros verdosos + esmeralda profunda; dark = negro verdoso). **Marco fijo:** `.app-frame` a `100dvh`, solo `<main class="app-canvas">` scrollea. Primitivas nuevas: `page-header`, `empty-state`, `skeleton`, `drawer`, `timeline`, `form-field`. Componentes de documento compartidos en `components/document/`.

**Branding por tenant:** `web/src/lib/branding.ts` — presets seleccionados por `VITE_TENANT` (`dasic` default, `atlas` neutro). Nombre de organización, tagline, producto, logo, placeholders y copy del login salen de ahí. Nuevo tenant = nuevo preset, nunca un fork.

## Tipo de cambio — modelo direccional (2026-08-04)

USD→MN multiplica por **DOF + tolerancia**; MN→USD divide entre **DOF − tolerancia**; el costo de OC al proveedor usa **DOF puro**. Sustituye al modelo unificado del 2026-06-10 (una sola tasa espejo) que dejaba MN→USD sin protección. Espejo exacto entre `app/routers/ventas.py::_resolve_directional_tcs` y `web/src/features/cotizador/lib/calc.ts::resolveDirectionalTcs`. Overrides del payload solo se honran dentro de la banda `[DOF·0.5, DOF·1.5]` (descarta el sentinela legacy `0.000001` que reventaba importes ×1,000,000).

## RBAC

Roles: `SUPERADMIN`, `ADMINISTRADOR` (="admin"), `GERENTE_COMERCIAL` (="asistente"), `VENTAS` (="vendedor"), `OPERATIVO`. **Matriz declarativa** en `app/security/permissions.py`: tuplas `(action, resource)`, helpers `can()` / `require()` (403) / `scope_query_by_owner()` para `:own`. ADMIN y SUPERADMIN tienen wildcard. Flags `can_*` + `modulos_visibles` se sirven a `/api/me` y el front los lee vía `lib/permissions.ts`. Decoradores `allow_*` de `jwt.py` siguen por compatibilidad; endpoints nuevos usan `require()`.

## Riesgos / deuda

1. **Routers gordos:** `ventas.py` (2 460 líneas), `compras.py` (1 191), `clientes.py` (1 189), `productos.py` (1 003) mezclan dominio/persistencia/presentación. Solo `remisiones` migró al patrón `app/domains/`.
2. **Cobertura de tests:** ya no está concentrada en remisiones — totales, redondeo, fechas, stock, cobranza, auditoría y los GET de dashboard/reportes tienen pruebas, y el frontend tiene harness de componentes (jsdom por archivo). Siguen sin suite E2E el golden path y sin pruebas dedicadas CRM y compras.
3. **`create_all()` + `_BACKFILL_DDL` coexisten con Alembic** (Railway no corre migraciones): 84 `ADD COLUMN IF NOT EXISTS` en `seeds.py`. Columna nueva sin entrada doble = 500.
4. **Decimales** serializados como string; los types TS los modelan como `number | string`.
5. **RBAC en dos mecanismos:** 217 usos de helpers `allow_*` en `app/routers/` contra 27 de `require()`.
6. **Multi-tenancy retirada a medias:** columnas `organization_id` siguen en varias tablas sin ninguna semántica de aislamiento.
7. **Operación sin vigilancia:** nadie mira los logs de producción (859 errores 500 pasaron dos meses sin detectarse) y staging sigue desplegando `main`, así que no es compuerta previa.

## Pendientes (roadmap activo)

> **La fuente única y priorizada de pendientes es `docs/current-state/backlog.md`.** Lo de abajo es solo el resumen; si discrepan, manda el backlog.

1. **Decisiones de producto abiertas (P0)** — ocho preguntas para Vania, Axel, Administración y Emmanuel; tres de ellas bloquean el golden path.
2. **Golden path remisión → factura → pago:** Ola 2 (documento oficial) y Ola 3 (facturación) bloqueadas por decisiones; Ola 4 abierta: retirar el editor legacy de remisiones, quitar la carga completa de catálogo del KPI legacy, suite E2E, segunda pasada de auditoría (upload-csv masivo y cambio de contraseña).
3. **A medias (P2):** estado de error en las 10 páginas que faltan (18 de 35 usan `QueryError`), mitad abierta del bug #7 del cotizador, `B904` ignorado en `ruff.toml`.
4. **Migrar más módulos a `app/domains/`** (ventas/cotizador, compras, inventario).
5. **RBAC:** terminar de mover endpoints viejos de `allow_*` a `require()`; resolver la contradicción del módulo `compras` en la matriz.
6. **Fechas:** filtros con `utcnow()` en `dashboard.py`/`reportes.py` y `liberar_vencidas` (libera reservas un día antes).
7. **Fase 6 Alembic-only:** retirar `create_all()` y `_BACKFILL_DDL`.
8. **Consistencia visual (P4)** y **quick wins de producto (P5)** — modal de pago en cobranza, export CSV, filtros del Kanban, carga/promoción masiva de fantasmas.
9. **Más lejos:** super-admin (impersonación, feature flags, log de mantenimiento), aprobaciones de descuento por rol, WhatsApp nivel B.
10. **Railway:** apuntar el servicio de staging a la rama `staging` (hoy 73 commits detrás de `main`).

## Histórico (lanes cerrados — resumen)

RBAC fase 1 · catálogo costo-first · cotizador fase 2 (multimoneda) · seguimiento · folios/recotización · OC real · migración SPA (2026-05-22) · Atlas ONE rebrand + theme · arquitectura de documentos (OC/remisión/reporte desde cotización) · empresas+contactos · auditoría paralela · super-admin Módulos 0/A/B/C/D · design system premium (2026-06) · paginación · módulos activados (estado cuenta/kardex/SAT) · CRM Kanban · centro de cobranza · recordatorios · **2026-08:** base instalada (plantas/activos) · harness vitest · fase 1 móvil del cotizador · dominio remisiones (repository/service/router/documents) · remisiones v2 UI completa · unidades administrables · CRM v2 (detalle, actividades, métricas, etapas, deal→cotización) · editor híbrido de remisiones · modelo direccional de TC · design system CIRCUITO · branding por tenant · golden path olas 0 y 1 (staging, CI con PostgreSQL, 15 bugs de la auditoría) · cierre de seis endpoints sin autenticación · fechas de orden a `DATE` · auditoría de mutaciones (Ola 4 E5) · **2026-10:** hotfix de fechas en dashboard, cotizador y reportes. Detalle por commit en `git log`.
