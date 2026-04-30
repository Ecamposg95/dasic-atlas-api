# Cotizador Pro: robusto, intuitivo, automático, semántico

**Fecha:** 2026-04-30
**Estado:** spec aprobado por el usuario
**Tipo:** ola de mejoras al módulo cotizador (`app/templates/cotizador.html`, `app/routers/ventas.py` y endpoints nuevos).

## Contexto y problema

El cotizador hoy cumple su función transaccional: el vendedor arma un carrito, asigna utilidad, genera folio y guarda. Funciona, pero la experiencia es operativa, no premium. El sistema reacciona a cada acción del usuario en lugar de anticiparse. La sensación es la de una herramienta que el operador ejecuta paso a paso, no la de un copiloto que sugiere, recuerda y acelera.

Síntomas concretos detectados:

- Si el navegador se cierra o la pestaña se recarga, el carrito se pierde sin recuperación posible.
- Toda la operación se hace con mouse: no hay atajos para agregar línea, cambiar foco al buscador, abrir cliente.
- La utilidad se inicializa fija en 30% para todas las líneas, ignorando que cierto cliente recurrente ya viene cerrando al 22% o que cierto producto histórico se mueve al 45%.
- El buscador de productos exige match casi exacto del SKU o de la descripción. No tolera typos, sinónimos del rubro ("relevador" vs "relay", "breaker" vs "interruptor"), ni órdenes de palabras distintos.
- No existe un sistema de plantillas: cada cotización repetitiva (kit de mantenimiento, paquete de tableros) se reconstruye a mano.
- Faltan señales visuales de margen: una línea con utilidad 3% se ve igual que una con 35%.
- No hay manera rápida de ver "qué cotizaste a este cliente la última vez" sin abrir Seguimiento.

El objetivo de esta ola es cerrar esa brecha y entregar percepción de software que trabaja con el vendedor, no que el vendedor opera.

## Objetivos

Cuatro dimensiones explícitas, cada una con resultados verificables:

### 1. INTUITIVO — el sistema reduce fricción de teclado/ratón

- Auto-save del borrador en `localStorage` con propuesta de restauración al volver.
- Atajos: `/` enfoca buscador, `Enter` agrega producto top, `Alt+N` nueva línea libre, `Alt+S` guarda, `Esc` cierra modales.
- Drag & drop para reordenar líneas del carrito.
- Hover preview en resultados de búsqueda (mini-card con costo, stock, última venta).
- Semáforo de margen por línea (verde ≥20%, amarillo 5–20%, rojo <5%).
- Widget "última cotización a este cliente" con fecha, folio y total al seleccionar cliente.

### 2. AUTOMÁTICO — el sistema decide defaults inteligentes

- Auto-utilidad sugerida por cliente y producto (endpoint `auto-utilidad`).
- Vigencia default 5 días hábiles, configurable por cotización.
- Al guardar una cotización, prompt opcional "¿Generar borrador de OC ahora?".
- Cliente reciente preseleccionado si hay actividad <2h en el mismo navegador.

### 3. SEMÁNTICO — el sistema entiende intención, no solo strings

- Fuzzy search tolerante a typos (Levenshtein simplificado, max 2 errores).
- Diccionario de sinónimos ES/EN/abreviaturas para vocabulario industrial.
- Parser de cantidad: `"5 GV2ME14"` se interpreta como cantidad 5 + búsqueda `GV2ME14`.
- Búsqueda por marca: `"schneider c60n"` filtra primero por marca.
- Auto-clasificación de productos fantasma por prefijo de SKU (LC1 → contactor, GV2 → guardamotor, C60 → breaker).

### 4. ROBUSTO — el sistema previene errores y persiste contexto

- Modal de confirmación si alguna línea cierra con margen <5%.
- Export/import de cotización en JSON (backup, transferir entre vendedores).
- Plantillas guardadas reutilizables por usuario.
- Sugerencia de productos relacionados (co-ocurrencia histórica).

## No-objetivos

Esta ola **no** incluye:

- WebSocket o lock pesimista para edición concurrente del mismo borrador. El overhead de infra y los edge cases de reconexión exceden el alcance.
- Cron jobs de recordatorios automáticos (vigencia por vencer, cotización sin respuesta). Pertenece a una ola separada de notificaciones.
- Audit log granular de cambios línea por línea con diff. Hoy `quote_events` cubre lo crítico; un audit más fino se evalúa después.
- Servicios de NLU vía LLM para parseo libre de cotizaciones ("cotízame 3 contactores y un guardamotor"). Anthropic SDK ya está integrado pero el alcance se mantiene en heurísticas locales.

## Decisiones clave

### D1. Auto-save en localStorage

Cada cambio en el carrito (agregar línea, modificar cantidad, cambiar utilidad, cambiar cliente) dispara un debounce de 500 ms que serializa el estado completo a `localStorage` bajo la clave `dasic_cotizador_borrador_{userId}`. El payload incluye `cliente_id`, `moneda`, `tipo_cambio`, `vigencia`, `lineas[]` y `timestamp`.

Al cargar el cotizador, si existe un borrador con `timestamp` <24h, se muestra un banner: *"Tienes un borrador sin guardar de hace X minutos. ¿Restaurar o descartar?"*. Restaurar repuebla el state de Alpine. Descartar borra la clave.

TTL: 24h. Después de guardar la cotización en backend, la clave se borra inmediatamente.

### D2. Auto-utilidad por cliente y producto

Endpoint `GET /api/ventas/auto-utilidad?cliente_id=&producto_id=`. Lógica de fallback:

1. Si `cliente_id + producto_id` tienen ≥3 detalles previos cerrados, devuelve promedio ponderado por cantidad de los últimos 6 meses.
2. Si no, si el `cliente_id` tiene ≥5 detalles previos cualquiera, devuelve promedio del cliente.
3. Si no, si el `producto_id` tiene ≥10 detalles previos, devuelve promedio del producto.
4. Si nada aplica, devuelve `30.0` (default actual).

Respuesta: `{"utilidad": 28.5, "fuente": "cliente_producto" | "cliente" | "producto" | "default", "muestras": 14}`. El frontend usa `fuente` para decorar el input con un badge sutil ("histórico cliente").

### D3. Plantillas

Modelo `PlantillaCotizacion` (tabla `plantillas_cotizacion`):

- `id` UUID PK
- `organization_id` VARCHAR(36) FK
- `usuario_id` UUID FK
- `nombre` VARCHAR(120) NOT NULL
- `descripcion` TEXT NULL
- `lineas` JSONB (array de `{producto_id, cantidad, utilidad, descripcion_libre, sku_libre}`)
- `creado_en`, `actualizado_en` TIMESTAMP

Endpoints CRUD bajo `/api/ventas/plantillas` con scope por `organization_id` + `usuario_id` (cada vendedor ve sus propias). Admin puede listar las del tenant completo.

UI: dropdown "Cargar plantilla" en el header del cotizador, y botón "Guardar como plantilla" en el footer del carrito que abre modal con `nombre` + `descripcion`.

### D4. Sinónimos y fuzzy search

**Sinónimos**: archivo estático `app/data/sinonimos.json` con estructura `{ "canonico": ["sinonimo1", "sinonimo2", ...] }`. Diccionario inicial cubre el rubro de control industrial: relevador↔relay, contactor, breaker↔interruptor↔termomagnético, push button↔pulsador↔botón, guardamotor↔motor protector, variador↔drive↔VFD, PLC↔autómata, sensor↔detector, fuente↔power supply.

El backend expone el diccionario vía `GET /api/ventas/sinonimos` (cacheable agresivo). El frontend lo carga una vez y lo usa para expandir cada token de la query antes de hacer el match.

**Fuzzy**: implementación liviana en JS — Levenshtein con corte temprano cuando la distancia supera 2. Solo se aplica a tokens ≥4 caracteres para evitar ruido en SKUs cortos. Se ejecuta sobre el resultado ya filtrado del autocomplete actual; no requiere cambios en el endpoint.

### D5. Parser de cantidad

Regex `^\s*(\d+)\s+(\S.*)$`. Si la query empieza con un entero seguido de espacio y al menos un caracter, se interpreta como `(cantidad, query_real)`. El frontend lanza la búsqueda solo con `query_real`; al seleccionar el primer resultado, lo agrega con la `cantidad` parseada en lugar de 1.

Hard guard: si `query_real` también es puramente numérica (caso SKU tipo `39.31.0.024.0060`), se aborta el parseo y se usa la query completa como string. El usuario puede forzar el modo con un prefijo explícito `x5 ` (futuro), pero no entra en este alcance.

### D6. Productos relacionados (co-ocurrencia)

Endpoint `GET /api/ventas/productos-relacionados/{producto_id}?limit=5`. Query agregada:

```sql
SELECT d2.producto_id, COUNT(DISTINCT d1.orden_id) AS coocurrencias
FROM detalle_orden d1
JOIN detalle_orden d2 ON d1.orden_id = d2.orden_id AND d1.producto_id <> d2.producto_id
WHERE d1.producto_id = :pid
  AND d1.organization_id = :org_id
GROUP BY d2.producto_id
HAVING COUNT(DISTINCT d1.orden_id) >= 2
ORDER BY coocurrencias DESC
LIMIT :limit
```

Se materializa el resultado con `Producto.descripcion`, `costo_compra` y `moneda_compra`. Threshold mínimo: ≥2 cotizaciones compartidas para evitar ruido. Performance: añadir índice compuesto `(organization_id, producto_id)` en `detalle_orden` si no existe.

UI: panel lateral "Suelen pedirse junto con esto" que aparece tras agregar una línea, con click-to-add directo.

### D7. Alerta de margen <5%

En el handler de submit del cotizador, antes de POST, se recorre `lineas[]`. Si alguna tiene `utilidad < 5`, se intercepta con un modal:

> *"3 líneas tienen margen menor a 5%. ¿Confirmas guardar la cotización? [Revisar] [Confirmar de todos modos]"*

Revisar cierra el modal y resalta las líneas en rojo. Confirmar continúa con el POST normal. Esta validación es solo UX; el backend no rechaza márgenes bajos (puede haber casos legítimos como recuperar cliente o vender stock obsoleto).

## Modelo de datos

Cambios mínimos:

**Nueva tabla `plantillas_cotizacion`**:

| columna | tipo | nullable | nota |
|---|---|---|---|
| `id` | VARCHAR(36) | no | PK UUID |
| `organization_id` | VARCHAR(36) | no | FK `organizations.id` |
| `usuario_id` | VARCHAR(36) | no | FK `usuarios.id` |
| `nombre` | VARCHAR(120) | no | único por `(organization_id, usuario_id)` |
| `descripcion` | TEXT | sí | |
| `lineas` | JSONB | no | array de objetos línea |
| `creado_en` | TIMESTAMP | no | default `now()` |
| `actualizado_en` | TIMESTAMP | no | default `now()` |

Migración Alembic dedicada. Se agrega también al `_BACKFILL_DDL` como red de seguridad para entornos pre-Alembic, pero la fuente de verdad es la revisión Alembic.

**Sin cambios** en `Producto`, `OrdenVenta`, `DetalleOrden`, `Cliente`. Toda la inteligencia adicional se calcula sobre datos existentes.

## API

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/api/ventas/auto-utilidad?cliente_id=&producto_id=` | Sugiere % utilidad con fallback en cascada | `allow_all_staff` |
| GET | `/api/ventas/plantillas` | Lista plantillas del usuario | `allow_all_staff` |
| POST | `/api/ventas/plantillas` | Crea plantilla (`nombre`, `descripcion`, `lineas`) | `allow_all_staff` |
| PATCH | `/api/ventas/plantillas/{id}` | Actualiza nombre/descripcion/líneas | `allow_all_staff` (owner) |
| DELETE | `/api/ventas/plantillas/{id}` | Elimina (owner o admin) | `allow_all_staff` |
| GET | `/api/ventas/productos-relacionados/{producto_id}?limit=5` | Co-ocurrencia histórica | `allow_all_staff` |
| GET | `/api/ventas/ultima-cotizacion-cliente/{cliente_id}` | Última cot del cliente: folio, fecha, total, líneas resumidas | `allow_all_staff` |
| GET | `/api/ventas/sinonimos` | Diccionario ES/EN/abreviatura → canónico (cacheable) | `allow_all_staff` |

Todos los endpoints filtran por `organization_id` desde el `ContextVar`. Las plantillas son por usuario; el resto es por tenant.

## Edge cases

1. **Producto sin historial alguno**: `auto-utilidad` cae al default 30%. El badge muestra "default" en gris para que el vendedor sepa que no hay señal.
2. **Plantilla con productos eliminados**: al cargar, se filtran las líneas cuyo `producto_id` ya no existe o está marcado `activo=false`. Se muestra warning "2 productos de la plantilla ya no están disponibles y fueron omitidos".
3. **Sinónimo ambiguo**: `"motor"` puede mapear a `motor eléctrico`, `guardamotor`, `motor protector`. Se devuelven todos los matches; el ranking del autocomplete los ordena por frecuencia de uso histórico del tenant.
4. **Parser de cantidad falla con SKU numérico**: SKUs como `39.31.0.024.0060` (Finder) empiezan con dígitos. El guard del regex (`query_real` no puede ser solo dígitos/puntos) evita el falso positivo. Caso adicional: `"5 39.31"` debe interpretarse como cantidad 5 + búsqueda `39.31`, lo cual el regex acepta correctamente.
5. **Auto-utilidad con datos contradictorios**: cliente histórico al 35% pero producto histórico al 15%. La cascada prioriza el match más específico (`cliente_producto` > `cliente` > `producto`), así que en ese caso devuelve el % del cliente. El badge revela la fuente para que el vendedor pueda corregir manualmente.
6. **localStorage lleno**: al guardar borrador, capturar `QuotaExceededError`. Si ocurre, intentar truncar borradores antiguos de otros días o caer a no persistir, con un toast discreto "no se pudo guardar el borrador localmente".
7. **Plantilla con líneas libres (`producto_id=null`)**: se preservan los campos `sku_libre` y `descripcion_libre` tal cual; el costo y la utilidad se mantienen como estaban en la plantilla.
8. **Productos relacionados sobre tenant chico**: si la query no llega al threshold de 2 co-ocurrencias, devuelve array vacío. El panel se oculta en ese caso, no muestra "sin sugerencias".

## Test plan smoke

| # | Escenario | Pasos | Resultado esperado |
|---|---|---|---|
| 1 | Auto-save y restore | Agregar 3 líneas, recargar pestaña sin guardar | Banner "restaurar borrador"; al aceptar, el carrito vuelve idéntico |
| 2 | Atajo `/` enfoca buscador | Abrir cotizador, presionar `/` | Foco en input de búsqueda; query vacía |
| 3 | Auto-utilidad por cliente | Seleccionar cliente con 5+ cotizaciones cerradas al ~25% | Nuevas líneas inician con utilidad ~25%, badge "histórico cliente" |
| 4 | Fuzzy search típico | Buscar `"contctor lc1"` | Devuelve `LC1D09M7` y similares (Levenshtein ≤2) |
| 5 | Sinónimo ES/EN | Buscar `"relay finder"` | Devuelve productos con descripción `relevador Finder` |
| 6 | Parser cantidad | Buscar `"10 GV2ME14"`, presionar Enter | Agrega 10 unidades de `GV2ME14` directo |
| 7 | Plantilla — guardar y cargar | Guardar carrito de 4 líneas como "Kit mant"; nuevo cotizador, cargar plantilla | Carrito repuebla con 4 líneas idénticas |
| 8 | Productos relacionados | Agregar `LC1D09M7`; revisar panel lateral | Aparecen al menos 1–2 productos co-ocurrentes (si hay datos) |
| 9 | Alerta margen <5% | Forzar utilidad 3% en una línea, presionar guardar | Modal de confirmación bloquea el submit hasta confirmar |
| 10 | Última cotización cliente | Seleccionar cliente con cotizaciones previas | Widget muestra folio, fecha y total de la última |

Validación: `python -m py_compile` sobre los routers nuevos, smoke manual con `uvicorn --reload`, verificación de `organization_id` en todas las queries con un grep dirigido.

## Riesgos

**Performance del endpoint productos-relacionados.** La query de co-ocurrencia hace self-join sobre `detalle_orden`, que crece linealmente con el volumen de cotizaciones. En tenants con >50k detalles puede degradarse a >500ms. Mitigación: índice compuesto `(organization_id, producto_id)`, cache en memoria por 5 minutos en el router (clave `org_id + producto_id + limit`), y opción de materializar a una tabla `producto_coocurrencia` precalculada nocturna si el problema escala. No se hace upfront.

**Cap de localStorage (~5MB por origen).** Borradores grandes (50+ líneas con descripciones largas) podrían acercarse al límite combinados con otros usos del navegador. El handler de `QuotaExceededError` mitiga, pero el peor caso es que el usuario pierde el borrador silenciosamente. Toast explícito y no fallback a memoria volátil — preferimos avisar.

**Carrito perdido si el usuario cambia de navegador o dispositivo.** localStorage es por origen + dispositivo. No es portable. Para casos legítimos (laptop a casa, móvil) la solución correcta es persistencia server-side de borradores, fuera de alcance. Se documenta como limitación conocida; el botón "exportar JSON" da una vía manual.

**Sinónimos faltantes generan ruido.** Un diccionario incompleto puede sumar tokens irrelevantes y bajar la precisión del match. Mitigación: el diccionario inicial es conservador (~30 entradas curadas), y el endpoint `/api/ventas/sinonimos` permite editarlo en el archivo sin redeploy de schema. Telemetría futura: registrar queries con cero resultados para detectar gaps reales.

## Próximos pasos

1. Crear migración Alembic para `plantillas_cotizacion` + agregar al `_BACKFILL_DDL` como shim.
2. Modelo SQLAlchemy `PlantillaCotizacion` en `app/models/sales.py` (o nuevo `templates.py` si crece).
3. Schemas Pydantic en `app/schemas/sales.py` para plantillas + responses de los endpoints nuevos.
4. Router `app/routers/ventas.py`: agregar handlers de `auto-utilidad`, `plantillas` (CRUD), `productos-relacionados`, `ultima-cotizacion-cliente`, `sinonimos`.
5. Crear `app/data/sinonimos.json` con diccionario inicial curado del rubro.
6. Frontend `app/templates/cotizador.html`: implementar auto-save, restore banner, atajos, semáforo, fuzzy + sinónimos en cliente, parser cantidad, panel relacionados, widget última cot, modal margen, dropdown plantillas, export/import JSON.
7. Smoke test manual sobre los 10 escenarios del plan.
8. Verificar que cada query nueva filtre por `organization_id` (auditoría dirigida).
9. Commit en olas pequeñas: (a) modelo+migración+schemas, (b) endpoints backend, (c) UI cotizador.
10. Documentar en `context/02_REPO_CURRENT_STATE.md` el cierre de esta fase y abrir issue separado para WebSocket lock + cron recordatorios + NLU LLM (los no-objetivos).
