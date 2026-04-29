# DASIC Seguimiento Cotizador e Inventario Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** cerrar el gap entre el cotizador/inventario actual y los acuerdos del seguimiento del 25 de abril de 2026, priorizando un avance funcional demostrable en inventario, cotizador, seguimiento y jerarquía básica de usuarios.

**Architecture:** el repo actual ya expone SSR con Jinja2 y APIs FastAPI, pero la lógica de negocio está demasiado concentrada en `routers/` y el cotizador sigue modelado como `precio_publico - descuento`. La estrategia correcta es estabilizar primero contratos de dominio y persistencia para productos, cotizaciones y compras, luego ajustar SSR/API sobre esos contratos y dejar IA/proveedor como fase exploratoria separada.

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2 SSR, Alpine.js, Tailwind CDN, PostgreSQL, Alembic.

---

## Resumen Ejecutivo

El repo ya tiene base para:
- usuarios y autenticación (`app/models/users.py`, `app/security/jwt.py`, `app/routers/usuarios.py`)
- productos e inventario (`app/models/catalog.py`, `app/routers/productos.py`, `app/templates/inventario.html`)
- cotizaciones/ventas (`app/models/sales.py`, `app/routers/ventas.py`, `app/templates/cotizador.html`, `app/templates/seguimiento.html`)
- compras (`app/models/purchases.py`, `app/routers/compras.py`)

Los acuerdos del seguimiento no caben como "parches" puntuales. Hay cuatro brechas estructurales:

1. El modelo actual de cotización usa `precio_publico` y `descuento`; el negocio pidió `costo_compra + utilidad`.
2. Producto/inventario no modela moneda de compra, SKU asistido, productos fantasmas ni importación Excel real.
3. Seguimiento y dashboard muestran historial simple, pero no antigüedad, recotizaciones, correos ni conversión a orden de compra.
4. El RBAC actual solo tiene `ADMIN`, `ASISTENTE`, `VENDEDOR`; la reunión definió `superadministrador`, `administrador` y `administrador operativo`.

## Hallazgos del Repo Actual

- `app/models/enums.py` solo define tres roles y cuatro estatus de orden.
- `app/models/catalog.py` obliga a convivir con `precio_publico`, `precio_mayorista` y `precio_distribuidor`; no hay `moneda_compra`, `tipo_cambio_base`, `es_fantasma`, `sku_generado`, `qr_code`.
- `app/models/sales.py` no diferencia entre cotización original, recotización, orden de compra derivada ni eventos de envío.
- `app/routers/ventas.py` genera folio con contador global por organización (`COT-ORG-0001`) y PDF con texto fijo "Cotización en Moneda Nacional".
- `app/routers/productos.py` solo importa CSV y la plantilla real esperada por negocio es Excel.
- `app/templates/dashboard.html` y `app/templates/seguimiento.html` trabajan con KPIs/historial mínimos.
- `app/static/js/cotizador.js` es código huérfano de otra generación del cotizador; hoy la pantalla viva embebe lógica directamente en `app/templates/cotizador.html`.
- No existe `app/repositories/` todavía, aunque `context/02_REPO_CURRENT_STATE.md` ya lo marca como deuda técnica inmediata.

## Trazabilidad Contra Los Bullets de Negocio

### Bugs / Problemas detectados

- `En cotizaciones en dólares, las condiciones comerciales siguen mostrando moneda nacional`
  - Mapea a: Epic 6
  - Impacta: `app/routers/ventas.py`
- `No se puede modificar moneda (USD/MXN) al agregar productos`
  - Mapea a: Epic 3
  - Impacta: `app/templates/cotizador.html`, `app/schemas/sales.py`, `app/routers/ventas.py`
- `El sistema obliga a poner precio público en inventario, lo cual no aplica a su modelo`
  - Mapea a: Epic 2
  - Impacta: `app/models/catalog.py`, `app/schemas/catalog.py`, `app/routers/productos.py`
- `El SKU interno se muestra completo en cotización (incluye info extra no deseada)`
  - Mapea a: Epic 2 y Epic 3
  - Impacta: `app/models/catalog.py`, `app/templates/cotizador.html`, PDF en `app/routers/ventas.py`

### Fixes / Ajustes solicitados

- `Corregir que la cotización refleje correctamente la moneda seleccionada`
  - Mapea a: Epic 3 y Epic 6
- `Permitir definir solo costo de compra en inventario (sin precio público)`
  - Mapea a: Epic 2
- `Cambiar lógica de descuento → utilidad (%) en el cotizador`
  - Mapea a: Epic 3
- `Ajustar formato de folios de cotización (estructura por año/mes/usuario)`
  - Mapea a: Epic 4
- `Permitir editar o definir moneda al crear cotizaciones`
  - Mapea a: Epic 3
- `Mejorar manejo de SKU para mostrar solo catálogo del fabricante`
  - Mapea a: Epic 2 y Epic 3

### Features / Nuevas funcionalidades

- `Niveles de usuario (super admin, admin, operativos)`
  - Mapea a: Epic 1
- `Dashboard con KPIs: cotizaciones, órdenes de compra, etc.`
  - Mapea a: Epic 7
- `Productos “fantasma” (cotizar sin estar en inventario)`
  - Mapea a: Epic 3
- `Generación automática de órdenes de compra desde cotizaciones`
  - Mapea a: Epic 5
- `Cotizador con utilidad configurable y variación por proveedor/tiempo`
  - Mapea a: Epic 3 y Epic 5
- `Soporte de multimoneda + tipo de cambio`
  - Mapea a: Epic 2, Epic 3 y Epic 6
- `Automatización de envío por correo + tracking`
  - Mapea a: Epic 6
- `Integración opcional con WhatsApp`
  - Mapea a: fase posterior, fuera del primer corte
- `Seguimiento de cotizaciones (estatus, antigüedad)`
  - Mapea a: Epic 4 y Epic 7
- `Generación automática de SKU y códigos QR`
  - Mapea a: Epic 2
- `Importación masiva de inventario desde Excel`
  - Mapea a: Epic 2
- `Posible uso de IA para seguimiento de cotizaciones/proveedores`
  - Mapea a: fase exploratoria posterior

## Alcance Incluido

- jerarquía de usuarios pedida por operación
- dashboard orientado a ventas, cotizaciones y órdenes de compra
- rediseño del cotizador para trabajar por costo/utilidad y moneda
- recotizaciones y antigüedad de cotizaciones
- conversión de cotización a orden de compra
- corrección de moneda en plantilla PDF/condiciones comerciales
- productos fantasmas
- generación automática de SKU
- QR por producto
- importación masiva por Excel
- registro de envíos de cotización por correo

## Alcance Excluido de Este Corte

- seguimiento asistido por IA con proveedores
- integración WhatsApp automática
- rediseño profundo del CRM de Deals/Pipelines
- warehouse flows avanzados o kardex completo

Eso debe quedar como fase exploratoria posterior, no dentro del primer avance funcional.

## Backlog por Tipo

### Bugs

- [ ] Corregir texto de moneda en condiciones comerciales cuando la cotización sea USD.
- [ ] Permitir cambiar moneda de salida y moneda por partida durante la captura de cotización.
- [ ] Eliminar obligatoriedad de `precio_publico` en altas de inventario y carga masiva.
- [ ] Mostrar solo el catálogo del fabricante en cotización/PDF, no el SKU interno completo.

### Fixes

- [ ] Reflejar moneda seleccionada de forma consistente en UI, persistencia y PDF.
- [ ] Cambiar cálculo de detalle de `descuento` a `utilidad (%)`.
- [ ] Implementar folio por año/mes/usuario con estrategia auditable.
- [ ] Permitir editar moneda y tipo de cambio antes de guardar o recotizar.
- [ ] Separar `sku_interno` de `codigo_fabricante` para presentación comercial.

### Features

- [ ] Implementar tres niveles de usuario operativos.
- [ ] Agregar dashboard de KPIs comerciales y operativos.
- [ ] Permitir productos fantasmas en cotización.
- [ ] Generar órdenes de compra desde cotizaciones.
- [ ] Soportar utilidad configurable por proveedor o condiciones de abastecimiento.
- [ ] Soportar multimoneda y tipo de cambio.
- [ ] Enviar cotizaciones por correo con tracking.
- [ ] Dejar WhatsApp como integración opcional desacoplada.
- [ ] Agregar seguimiento de cotizaciones por estatus y antigüedad.
- [ ] Generar SKU y QR automáticamente.
- [ ] Importar inventario desde Excel.
- [ ] Diseñar fase exploratoria de IA para seguimiento de proveedores/cotizaciones.

## Orden Recomendado

1. Base técnica y modelo de datos
2. Inventario y catálogo
3. Cotizador y recotización
4. Compras y conversión desde cotización
5. Dashboard, seguimiento y correo
6. Exploración IA/proveedores

## Mapa de Archivos a Tocar

**Modelos y enums**
- Modificar: `app/models/enums.py`
- Modificar: `app/models/catalog.py`
- Modificar: `app/models/sales.py`
- Modificar: `app/models/purchases.py`
- Posible creación: `app/models/communications.py` o incorporar eventos en `sales.py`

**Schemas**
- Modificar: `app/schemas/auth.py`
- Modificar: `app/schemas/catalog.py`
- Modificar: `app/schemas/sales.py`
- Posible creación: `app/schemas/purchases.py`

**Routers / servicios**
- Modificar: `app/routers/usuarios.py`
- Modificar: `app/routers/productos.py`
- Modificar: `app/routers/ventas.py`
- Modificar: `app/routers/compras.py`
- Posible creación: `app/services/folios.py`
- Posible creación: `app/services/quotes.py`
- Posible creación: `app/services/imports.py`
- Posible creación: `app/services/emailing.py`

**SSR / frontend**
- Modificar: `app/templates/usuarios.html`
- Modificar: `app/templates/dashboard.html`
- Modificar: `app/templates/inventario.html`
- Modificar: `app/templates/cotizador.html`
- Modificar: `app/templates/seguimiento.html`
- Limpiar o retirar: `app/static/js/cotizador.js`

**Migraciones y contexto**
- Crear: `migrations/versions/<revision>_quote_inventory_followup.py`
- Modificar: `context/02_REPO_CURRENT_STATE.md`
- Modificar: `context/RBAC.md`

## Backlog Priorizado

### Epic 1: RBAC y jerarquía operativa

**Objetivo:** soportar `superadministrador`, `administrador` y `administrador operativo` sin romper login actual.

- [ ] Extender `RolUsuario` en `app/models/enums.py` para mapear la jerarquía pedida.
- [ ] Ajustar `RoleChecker` en `app/security/jwt.py` y dependencias de `app/routers/usuarios.py`.
- [ ] Redefinir permisos mínimos:
  - `SUPERADMIN`: alcance plataforma o multi-organización
  - `ADMIN`: configuración y visibilidad total org
  - `OPERATIVO`: operación diaria de cotizaciones, inventario y seguimiento
- [ ] Actualizar formularios/listados SSR de `app/templates/usuarios.html`.
- [ ] Alinear `context/RBAC.md` con la jerarquía realmente implementada.

**Dependencias:** ninguna.
**Prioridad:** alta.

### Epic 2: Normalización de catálogo e inventario

**Objetivo:** dejar de exigir precio público como verdad central y soportar importación/alta alineada al proceso real de compra.

- [ ] Agregar a `Producto` campos orientados a operación:
  - `moneda_compra`
  - `tipo_cambio_referencia` o `ultimo_tipo_cambio`
  - `es_fantasma`
  - `sku_autogenerado`
  - `qr_payload` o `qr_code_path`
  - campos auxiliares de marca/subdenominación/catálogo si la lógica SQ lo requiere
- [ ] Mantener `precio_publico` solo como compatibilidad temporal, no como campo obligatorio de negocio.
- [ ] Cambiar `schemas.ProductoCreate` y `ProductoUpdate` para permitir alta sin precio público final.
- [ ] Reemplazar importación CSV por importación Excel real en `app/routers/productos.py`.
- [ ] Exponer descarga de plantilla Excel con columnas oficiales.
- [ ] Definir estrategia de upsert por SKU/SQ.
- [ ] Agregar endpoint para generación previa o automática de SKU/SQ.
- [ ] Agregar endpoint para generar o consultar QR por producto.

**Dependencias:** Epic 1 solo si ciertas vistas deben ocultar costos por rol.
**Prioridad:** muy alta.

### Epic 3: Cotizador basado en costo, utilidad y moneda

**Objetivo:** que cada partida cotice desde costo de compra, utilidad y moneda, no desde descuento sobre precio público.

- [ ] Rediseñar `DetalleOrden` en `app/models/sales.py` para guardar:
  - `costo_compra_capturado`
  - `moneda_compra`
  - `tipo_cambio_aplicado`
  - `utilidad_porcentaje` o `utilidad_monto`
  - `precio_venta_calculado`
  - `es_fantasma`
- [ ] Ajustar `app/schemas/sales.py` para recibir utilidad, moneda y tipo de cambio por partida.
- [ ] Reescribir `crear_orden` y `actualizar_orden` en `app/routers/ventas.py` para calcular precio final desde costo/utilidad.
- [ ] Permitir agregar productos fantasmas desde el cotizador, persistiendo como producto provisional o como snapshot de detalle.
- [ ] Corregir `app/templates/cotizador.html`:
  - quitar columna de descuento
  - agregar utilidad
  - mostrar moneda de compra y moneda de salida
  - soportar recálculo por tipo de cambio
- [ ] Registrar si una cotización es original o recotización.

**Dependencias:** Epic 2.
**Prioridad:** muy alta.

### Epic 4: Folios, antigüedad y recotización

**Objetivo:** volver trazables las cotizaciones por usuario y periodo, sin colisiones y con visibilidad operativa.

- [ ] Extraer la lógica de folios de `app/routers/ventas.py` a un servicio dedicado (`app/services/folios.py`).
- [ ] Implementar formato configurable con componentes:
  - prefijo (`COT` / `OC`)
  - año/mes
  - secuencia
  - sufijo por usuario o hash corto
- [ ] Guardar metadata de folio para búsqueda y auditoría.
- [ ] Agregar a cotizaciones campos de:
  - `parent_quote_id`
  - `version`
  - `last_quoted_at`
  - `expires_at`
- [ ] En `app/templates/seguimiento.html`, mostrar antigüedad, vigencia y versiones/recotizaciones.

**Dependencias:** Epic 3.
**Prioridad:** alta.

### Epic 5: Conversión cotización -> orden de compra

**Objetivo:** permitir que una cotización validada genere orden de compra hacia proveedor con seguimiento.

- [ ] Separar conceptualmente cotización comercial y orden de compra; hoy `convertir_cotizacion` la convierte a venta, no a compra.
- [ ] Agregar relación entre cotización y orden de compra en modelos de ventas/compras.
- [ ] Crear endpoint nuevo tipo `POST /api/ventas/{id}/generar-orden-compra`.
- [ ] Permitir seleccionar proveedor por partida o proveedor principal.
- [ ] Persistir estado de abastecimiento y fechas clave.
- [ ] Ajustar `app/templates/seguimiento.html` para mostrar cotizaciones pendientes de compra y órdenes generadas.

**Dependencias:** Epic 3 y 4.
**Prioridad:** alta.

### Epic 6: Corrección PDF, correo y trazabilidad de envíos

**Objetivo:** cerrar el bug visible de moneda y habilitar el envío de cotizaciones con auditoría.

- [ ] Corregir en `app/routers/ventas.py` la plantilla PDF para que condiciones comerciales muestren la moneda real de la cotización.
- [ ] Incluir tipo de cambio visible cuando aplique.
- [ ] Crear modelo o tabla de eventos de envío:
  - `quote_id`
  - `recipient`
  - `sent_at`
  - `channel`
  - `status`
- [ ] Agregar endpoint para enviar cotización por correo.
- [ ] Preparar `app/services/emailing.py` con abstracción SMTP/API provider.
- [ ] En dashboard y seguimiento, mostrar contador de envíos por cotización.

**Dependencias:** Epic 3.
**Prioridad:** alta.

### Epic 7: Dashboard operativo

**Objetivo:** al iniciar sesión, mostrar los KPIs pedidos por dirección y operación.

- [ ] Cambiar `app/templates/dashboard.html` para incluir:
  - ventas del mes
  - cotizaciones activas
  - órdenes de compra generadas o pendientes
  - clientes activos
  - recotizaciones pendientes
  - stock crítico
- [ ] Crear agregaciones de backend en lugar de seguir calculando todo desde listados crudos del frontend.
- [ ] Si el corte no alcanza para gráficas nuevas, priorizar KPI cards y tabla accionable.

**Dependencias:** Epic 2, 3, 5 y 6.
**Prioridad:** media-alta.

### Epic 8: Limpieza técnica mínima para sostener el avance

**Objetivo:** reducir deuda inmediata que va a entorpecer cualquier entrega.

- [ ] Mover lógica reutilizable de cotizador/folios/importación a `app/services/`.
- [ ] Eliminar o documentar `app/static/js/cotizador.js` para evitar doble fuente de verdad.
- [ ] Crear primera versión de `app/repositories/` para ventas/productos si el router sigue creciendo.
- [ ] Agregar migración Alembic formal para todos los cambios de modelo.

**Dependencias:** transversal.
**Prioridad:** media, pero debe acompañar cada epic relevante.

## Sprint Propuesto

### Sprint 1: Base para demo de miércoles

- RBAC mínimo con tres niveles operativos
- corrección de moneda en PDF
- producto con costo y moneda de compra
- importación Excel básica
- cotizador con utilidad en lugar de descuento
- seguimiento con antigüedad simple

**Resultado esperado:** demo funcional de alta/importación de producto y generación de cotización en MXN/USD con utilidad.

### Sprint 2: Cierre operativo inmediato

- recotizaciones/versionado
- productos fantasmas
- folios configurables
- conversión de cotización a orden de compra
- dashboard con KPIs nuevos

**Resultado esperado:** flujo completo desde catálogo/cotización hasta seguimiento y abastecimiento.

### Sprint 3: Automatización y endurecimiento

- envío por correo con registro
- QR por producto
- limpieza de servicios/repositorios
- endurecimiento Alembic y pruebas

**Resultado esperado:** flujo trazable y presentable para operación real.

## Plan de Ejecución Técnico por Sprint

### Sprint 1A: Base de acceso y contratos

**Objetivo:** fijar permisos y contratos mínimos antes de tocar lógica de negocio sensible.

- `Track A1 - RBAC`
  - archivos principales: `app/models/enums.py`, `app/security/jwt.py`, `app/schemas/auth.py`, `app/routers/usuarios.py`, `app/templates/usuarios.html`, `context/RBAC.md`
  - entregable: tres niveles operativos funcionales y visibles en UI/API
- `Track A2 - Contratos de catálogo`
  - archivos principales: `app/models/catalog.py`, `app/schemas/catalog.py`, `app/routers/productos.py`
  - entregable: producto puede existir con costo de compra y moneda sin requerir precio público

**Dependencia:** A1 y A2 pueden analizarse en paralelo, pero A2 no debe cerrar API pública final sin validar visibilidad por rol.

### Sprint 1B: Inventario y cotizador mínimo funcional

**Objetivo:** habilitar demo real de captura/importación y cotización en MXN/USD.

- `Track B1 - Inventario`
  - archivos principales: `app/models/catalog.py`, `app/schemas/catalog.py`, `app/routers/productos.py`, `app/templates/inventario.html`
  - entregable: alta manual sin precio público e importación Excel básica
- `Track B2 - Cotizador`
  - archivos principales: `app/models/sales.py`, `app/schemas/sales.py`, `app/routers/ventas.py`, `app/templates/cotizador.html`
  - entregable: utilidad, moneda editable, tipo de cambio, corrección PDF de moneda

**Dependencia:** B2 depende de la definición de campos finales de B1 para no duplicar criterios de moneda/costo.

### Sprint 2: Trazabilidad comercial

**Objetivo:** hacer que lo cotizado pueda seguirse, reversionarse y transformarse en abastecimiento.

- `Track C1 - Folios y recotizaciones`
  - archivos principales: `app/models/sales.py`, `app/routers/ventas.py`, `app/services/folios.py`, `app/templates/seguimiento.html`
  - entregable: folios por año/mes/usuario, antigüedad y versionado
- `Track C2 - Orden de compra desde cotización`
  - archivos principales: `app/models/purchases.py`, `app/models/sales.py`, `app/routers/compras.py`, `app/routers/ventas.py`, `app/templates/seguimiento.html`
  - entregable: generación inicial de orden de compra desde cotización
- `Track C3 - Dashboard`
  - archivos principales: `app/templates/dashboard.html`, backend agregado en `app/routers/ventas.py` o servicio dedicado
  - entregable: KPIs de cotizaciones, órdenes de compra y stock crítico

**Dependencia:** C1 debe cerrarse antes de C2 y C3 porque redefine la identidad operativa de las cotizaciones.

### Sprint 3: Automatización y extensiones

**Objetivo:** agregar automatización no crítica para operación inicial.

- `Track D1 - Correo y tracking`
  - archivos principales: `app/models/sales.py` o `app/models/communications.py`, `app/routers/ventas.py`, `app/services/emailing.py`
  - entregable: envío manual-asistido con bitácora de envíos
- `Track D2 - SKU/QR`
  - archivos principales: `app/models/catalog.py`, `app/routers/productos.py`, `app/services/imports.py`
  - entregable: generación automática y consulta/descarga de QR
- `Track D3 - Exploración opcional`
  - alcance: WhatsApp opcional e IA de seguimiento
  - entregable: ADR o spike, no feature cerrada

## Orquestación Paralela Recomendada

### Se puede correr en paralelo desde ahora

- `Track A1 - RBAC`
- `Track A2 - Contratos de catálogo`
- `Análisis técnico de Track B2 - Cotizador`

Esto es seguro porque:
- RBAC toca `users/security/auth/templates/usuarios`
- catálogo toca `catalog/productos/inventario`
- cotizador puede arrancar como análisis sobre `sales/ventas/cotizador` sin cerrar implementación hasta que catálogo fije campos

### No se debe implementar en paralelo todavía

- `Track B1 - Inventario` y `Track B2 - Cotizador` como cambios finales de modelo
- `Track C1 - Folios` y `Track C2 - Orden de compra`

Razón:
- comparten contratos de persistencia
- comparten semántica de cotización
- si se implementan a ciegas generan churn de migraciones y schemas

## Orquestación Inicial

### Ola 1: descubrimiento y diseño técnico en paralelo

- `Agente 1`
  - ownership: RBAC y usuarios
  - meta: proponer cambio exacto de roles, permisos y archivos
- `Agente 2`
  - ownership: catálogo e inventario
  - meta: proponer modelo final de producto, importación Excel y SKU comercial vs interno
- `Agente 3`
  - ownership: cotizador, moneda, utilidad, PDF y seguimiento
  - meta: proponer contrato final de cotización y dependencias sobre catálogo

### Ola 2: implementación escalonada

- cerrar primero `A2`
- luego ejecutar `B2` con el contrato fijo
- en paralelo con `B2`, cerrar `A1`
- después abrir `C1`
- luego `C2` y `C3`

## Definición de Done por Track

- `RBAC`: roles nuevos visibles en API y SSR, sin romper login
- `Catálogo`: producto se puede crear sin precio público y con moneda de compra
- `Cotizador`: utilidad reemplaza descuento y la moneda se refleja en UI/PDF
- `Folios`: estructura año/mes/usuario persistida y visible
- `Orden de compra`: cotización puede generar OC vinculada
- `Dashboard`: KPIs salen de agregados backend, no de heurísticas de frontend

## Riesgos

- Cambiar roles en caliente puede romper seeds, JWTs y validaciones de UI si no se hace en una sola pasada.
- Si se conserva `precio_publico` como obligatorio en schemas o UI, el cambio de negocio quedará a medias.
- Mezclar "cotización comercial", "venta" y "orden de compra" en la misma entidad seguirá generando bugs de estado.
- Excel import requiere definir plantilla cerrada antes de codificar; sin eso se desarrollará contra supuestos falsos.
- SKU/SQ automático depende de reglas que todavía debe compartir Vania; debe quedar como contrato configurable, no hardcodeado arbitrariamente.

## Decisiones de Diseño Recomendadas

- No implementar el seguimiento con IA dentro del mismo bloque de trabajo del cotizador.
- No usar el endpoint actual de conversión a venta para simular órdenes de compra; debe existir flujo separado.
- No seguir calculando KPIs desde datos crudos en frontend; mover agregados al backend.
- No introducir más lógica compleja directamente en `routers/`; crear servicios nuevos desde este corte.

## Entregables del Plan

1. Modelo de datos extendido y migración Alembic.
2. Inventario con importación Excel, SKU y QR base.
3. Cotizador nuevo por costo/utilidad/moneda.
4. Seguimiento con antigüedad y recotizaciones.
5. Conversión de cotización a orden de compra.
6. PDF corregido y correo con bitácora de envío.
7. Dashboard operativo mínimo.

## Criterio de Aceptación para la Próxima Reunión

- un usuario operativo puede crear o importar productos sin depender de precio público fijo
- una cotización puede capturar costo, utilidad, moneda y tipo de cambio
- el PDF muestra correctamente MXN o USD en condiciones comerciales
- seguimiento muestra antigüedad y estado de cotizaciones
- existe ruta inicial para generar orden de compra desde cotización
- dashboard muestra KPIs útiles para ventas/cotizaciones/inventario

## Recomendación de Ejecución

Este trabajo debe ejecutarse en dos tracks paralelos:
- track funcional: inventario, cotizador, seguimiento
- track técnico: modelos, migraciones, servicios y RBAC

Si solo se ataca la UI, el demo va a verse bien pero seguirá montado sobre estados y contratos incorrectos.

Plan complete and saved to `docs/superpowers/plans/2026-04-28-dasic-seguimiento-cotizador-inventario.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
