# Fundación: reorg de IA/sidebar + estandarización de listados (A+B)

**Fecha:** 2026-06-11
**Estado:** Aprobado para plan
**Alcance:** Workstreams A (estandarización de listados + consistencia visual) y B (arquitectura de información / sidebar). Primer spec de una serie; C (de-duplicación) y D (profundidad funcional) van en specs aparte.

## Contexto

Auditoría de los 24 módulos (5 subagentes read-only, 2026-06-11) reveló 5 patrones transversales: (1) listados sin estandarizar — falta paginación/búsqueda/filtros en muchos módulos, cada uno reinventa su barra de filtros/skeleton/paginación; (2) inconsistencia visual — badges de estatus con colores arbitrarios por módulo, tabs con estilos distintos; (3) duplicaciones/solapamientos de módulos; (4) arquitectura del sidebar desbalanceada y con nombres confusos; (5) falta de profundidad funcional.

El scroll largo de Borradores (resuelto 2026-06-10 con `DataTable maxBodyHeight` + header sticky) era un síntoma del patrón (1). Este spec ataca (1), (2) y (4). Los solapamientos (3) y la profundidad (4-funcional) quedan para C y D.

## Objetivos

- Construir primitivas de listado compartidas una sola vez y aplicarlas a todos los módulos-lista.
- Una paleta semántica única de estatus y un estilo de tabs único.
- Reorganizar el sidebar para balancear secciones y eliminar la confusión de nombres (documento vs analítica).
- Cero regresiones funcionales: B reubica/renombra/envuelve; no fusiona lógica de negocio.

## No-objetivos (explícitos)

- NO fusionar Contactos global con el tab de Clientes (→ C).
- NO unificar Usuarios con Superadmin/Usuarios (→ C).
- NO matar la duplicación drawer/página de Borradores (→ C).
- NO absorber Servicios en Inventario ni redefinir el modelo de Precios (→ C).
- NO sincronizar Deal↔Orden, drill-downs, FX tendencia, bulk actions (→ D).

---

## Sección B — Arquitectura de información / sidebar

### Estructura nueva

```
Comercial
  · Dashboard · CRM Pipeline · Cotizador · Borradores · Seguimiento · Recordatorios
Clientes                 (NUEVA sección; descarga a Comercial que tenía 8)
  · Empresas (hoy "Clientes") · Contactos
Operación
  · Compras · Remisiones · Reportes de servicio
Catálogo
  · Catálogo de productos · Servicios · Precios · Fantasmas(movido) · Diccionarios
Finanzas
  · Cuentas por cobrar · Gastos(movido) · Tipo de cambio
Analítica                (antes "Reportes")
  · KPIs                 (UNIFICA "Reportes (ventas)" + "Analítica de servicios"; tabs Ventas/Operativo/Servicios)
Sistema · Usuarios
Plataforma · Consola (solo superadmin)
```

### Decisiones y restricciones

1. **"Reportes de servicio" SE QUEDA** con ese nombre y en Operación. Es el **documento robusto que se entrega al cliente** (acta de lo ejecutado), NO un dashboard. Ruta `/spa/reportes-servicio-docs` sin cambios.
2. **"Diccionarios" SE QUEDA** con ese nombre (no renombrar).
3. **Módulo analítico unificado = "KPIs"** dentro de sección **"Analítica"**. Absorbe `features/reportes` (ventas) + `features/reportes_servicio` (operativo/servicios) en **una página con tabs: Ventas · Operativo · Servicios**.
   - Implementación = **shell con tabs que envuelve el contenido existente de ambas páginas**, sin reescribir su lógica interna. Bajo riesgo.
   - Ruta nueva canónica **`/spa/analitica`** (con `?tab=ventas|operativo|servicios`). Mantener `/spa/reportes` → redirect a `?tab=ventas` y `/spa/reportes-servicio` → redirect a `?tab=operativo`, para no romper enlaces/bookmarks.
4. **Nueva sección "Clientes"** = Empresas (hoy "Clientes", label cambia a "Empresas") + Contactos. Comercial baja de 8 a 6 ítems.
5. **Fantasmas movido** de Operación → Catálogo (es curación de datos previa al catálogo).
6. **Gastos movido** de Operación → Finanzas (es un egreso).

### Impacto en archivos (B)

- `web/src/components/layout/Sidebar.tsx` — reescribir `SECTIONS` con la estructura nueva (orden, labels, secciones).
- Router (App/router): agregar ruta `/spa/analitica` (página KPIs con tabs); redirects de `/spa/reportes` y `/spa/reportes-servicio` a ella. Verificar la ruta real del router SPA.
- Nueva feature host `web/src/features/analitica/pages/KpisPage.tsx` que renderiza las tabs (Ventas/Operativo/Servicios) y monta el contenido de `features/reportes` y `features/reportes_servicio` como sub-vistas. NO se borran esas features; se re-exponen como componentes embebidos.
- `_serve_spa_protected` handlers backend si alguna ruta SSR nueva lo requiere (verificar; probablemente solo front-routing).

---

## Sección A — Estandarización de listados + consistencia visual

### Primitivas compartidas (`web/src/components/ui/`)

1. **`DataTable`** (ya existe, mejorado 2026-06-10): props `maxBodyHeight` + `DataTableHead sticky`. Pasa a ser el patrón default de toda página-lista. Sin cambios nuevos salvo documentación de uso.
2. **`<ListToolbar>`** (NUEVO): layout estándar de barra superior de lista — slot de búsqueda (input con debounce 300ms), slot de filtros (dropdowns), slot de acciones a la derecha (`+ Nuevo`, Exportar). Reemplaza las filas de filtros ad-hoc.
3. **`<Pagination>`** (NUEVO): extrae el patrón de Borradores — botones Anterior/Siguiente + texto "Página X de Y · N total", manejado por `total` y `page_size`. Props: `page`, `totalPages` (o `total`+`pageSize`), `onPageChange`, `isLoading`.
4. **`<StatusBadge tone>`** (NUEVO): un set de tonos semánticos sobre tokens. Más un helper de mapeo `estatus crudo → tono` por dominio (cotización, recordatorio, compra, etc.).
5. **Tabs estándar**: un solo estilo (subrayado con `accent-glow`). Si ya existe primitiva tabs en `@/components/ui`, estandarizar su uso; si no, crear `<Tabs>` mínima. Reemplaza el estilo redondeado-arriba (Recordatorios) y unifica con el subrayado (EmpresaDetalle).

### Paleta semántica de estatus

| Tono | Token/color | Estatus que cubre |
|------|-------------|-------------------|
| `success` | esmeralda | activo · pagada · completado · vigente · recibido |
| `warning` | ámbar | pendiente · pospuesto · prospecto · por_vencer · parcial |
| `info` | acento/cian | cotizacion · borrador · en_proceso · en_oc |
| `danger` | rosa | cancelado · vencido · descartado · inactivo |
| `neutral` | muted | sin estado / default |

El componente recibe `tone`; un mapa por dominio traduce el valor crudo del backend (lowercase, [[reference-spa-frontend-conventions]]) al tono. Mantener tonos sobre tokens semánticos (no colores hardcodeados) por la migración slate→tokens previa.

### Soporte backend requerido

- Devolver `total` en endpoints paginados que no lo exponen (patrón ya aplicado a `/api/ventas/borradores`). Auditar: compras, fantasmas, remisiones, reportes-servicio-docs, contactos, clientes, etc.
- **Servicios**: hoy carga todo en memoria. Agregar `page/page_size + q` al endpoint y migrar el front a paginación server-side.
- **Precios**: el endpoint ya soporta page/page_size; exponer paginación en UI.
- **Gastos**: hoy `limit=500`. Agregar paginación server-side.
- **Recordatorios**: **BUG** — la UI no tiene paginación (rompe con >50). Verificar/añadir page/page_size en endpoint y prev/next en UI.
- **Marcas (Diccionarios)** y **CxC vencimientos**: evaluar paginación si el endpoint la soporta; si no, acotar con `DataTable maxBodyHeight` como mínimo.

Recordar: toda migración de esquema requiere espejo en `_BACKFILL_DDL` [[feedback-backfill-ddl-railway]] — aunque este spec NO prevé cambios de esquema (solo params de query y conteos), confirmarlo en el plan.

### Despliegue por olas (A)

- **A0 — Primitivas:** `ListToolbar`, `Pagination`, `StatusBadge` + mapa de tonos, tabs estándar. Sin tocar módulos aún.
- **A1 — Arreglar lo roto (paginación faltante):** Recordatorios (paginación + botón `+ Nuevo recordatorio` que abre el modal con `orden_id` opcional), Gastos, Precios, Servicios, Marcas/Diccionarios, CxC vencimientos.
- **A2 — Agregar búsqueda/filtros donde faltan:** Remisiones, Reportes de servicio (lista de documentos), Usuarios, orden por columnas en Contactos.
- **A3 — Consistencia visual:** migrar TODOS los badges de estatus a `<StatusBadge>`; unificar tabs al estilo subrayado.

### Impacto en archivos (A)

- Nuevos: `web/src/components/ui/list-toolbar.tsx`, `pagination.tsx`, `status-badge.tsx`, (`tabs.tsx` si no existe), `web/src/lib/status-tones.ts` (mapeo).
- Por módulo (A1/A2/A3): editar la `pages/<X>Page.tsx` de cada feature para consumir las primitivas + su `hooks/use<X>.ts` para los params de paginación/búsqueda. Backend: endpoints de servicios/gastos/precios/recordatorios para params + `total`.
- Tras cambios de front: `cd web && npm run build` (dist se commitea) [[reference-spa-frontend-conventions]].

---

## Riesgos

- **Sidebar reorg** cambia rutas mentales del usuario; mitigado con redirects para Analítica. Riesgo bajo.
- **Unificación de Analítica**: si el router SPA tiene supuestos sobre las rutas viejas, los redirects deben cubrirlos. Verificar el router antes de implementar.
- **Barrido de badges/tabs (A3)**: es amplio y mecánico; riesgo de tocar muchos archivos. Mitigar haciéndolo por feature, con build verde por ola.
- **Backend paginación**: cambios de query params son aditivos y compatibles; sin cambio de esquema esperado.
- **Sin suite de tests** [[reference-spa-frontend-conventions]]: validación con `py_compile` + `npm run build` + QA visual del usuario por ola.

## Validación

- `python -m py_compile` sobre routers backend tocados; `cd web && npm run build` verde por ola.
- QA visual del usuario por ola (light/dark, ~375px móvil): sidebar nuevo navegable, KPIs con tabs, listados con paginación/filtros, badges/tabs consistentes.
- Cada ola es un commit (o pocos) auto-contenido y pusheable (push directo a main → Railway, [[reference-git-push-workflow]]).

## Secuencia sugerida de implementación

1. **B** (sidebar + redirects + shell de KPIs) — entrega visible inmediata, bajo riesgo.
2. **A0** (primitivas).
3. **A1** (arreglar paginación rota, incl. bug de Recordatorios).
4. **A2** (filtros/búsqueda faltantes).
5. **A3** (barrido de consistencia badges/tabs).
