# Cotizador robusto + Inventario "siempre saber qué se tiene"

**Fecha:** 2026-04-30
**Estado:** aprobado por el usuario (modo "reservar al cotizar"), listo para escribir plan de implementación.
**Módulos afectados:** ventas (cotizador), compras, productos, inventario, finance (no), schemas, migrations, frontend.

## Contexto y problema

DASIC contrató el sistema principalmente por el cotizador. Hoy el cotizador funciona pero le faltan piezas clave que la operación real necesita:

- Las cotizaciones en USD usan un tipo de cambio capturado a mano. La operación real exige el TC oficial del día (Banxico FIX).
- Cuando se cotiza un producto sin stock, no hay un mecanismo automático para emitir la orden de compra al proveedor.
- No se distingue entre productos catalogados, productos "fantasma" (especiales, no inventariados) y servicios puros (instalación, programación, capacitación).
- El inventario muestra `stock_actual` pero no refleja qué está comprometido por cotizaciones activas. La gente no sabe qué tiene realmente disponible.
- No hay historial de movimientos de stock; los ajustes son destructivos y no auditables.

## Objetivos

1. **Cotizar con TC del día**, automático, oficial (Banxico) con fallback público.
2. **Soportar tres tipos de línea**: producto catálogo · producto fantasma · servicio.
3. **Reservar stock al cotizar**; liberar al cancelar / vencer / convertir.
4. **Generar OCs automáticas** para faltantes, agrupadas por proveedor, en estado borrador para que el usuario revise antes de enviar.
5. **Visibilidad de inventario en tiempo real**: stock disponible (= físico − reservado), historial completo de movimientos por producto.

## No-objetivos (YAGNI)

- No envío automático de OCs por correo; sólo se generan en borrador.
- No conversión histórica de USD/MXN para cotizaciones ya guardadas: cada cotización conserva su `tipo_cambio` snapshot.
- No multi-bodega: stock es global por SKU.
- No reservas parciales: una línea reserva su `cantidad` completa o nada.
- No PDF de OC mejorado en este sprint (ya quedó decente).
- No integración WhatsApp ni IA en este sprint.

## Decisiones clave

### D1. Stock reservado al cotizar
Cuando se crea una cotización con `producto_id`, se inserta un `MovimientoStock` tipo `RESERVA` por cada línea. **No** modifica `stock_actual`; sí cuenta para el cálculo `stock_disponible = stock_actual − Σ reservas activas`.

Eventos que liberan reservas:
- Convertir cotización → venta: `RESERVA` → `SALIDA` (consume stock real).
- Cancelar cotización: `LIBERACION` (anula la reserva).
- Vencer cotización (fecha_vencimiento < hoy + N días tolerancia): job nocturno emite `LIBERACION`.
- Editar cotización (cambiar cantidad/producto): se ajustan los movimientos para reflejar el nuevo estado.

### D2. Fuente de tipo de cambio
- **Primaria:** Banxico SIE serie `SF63528` (TC FIX para liquidación 48h, oficial de la SHCP). Endpoint público pero requiere token gratuito (registro en `https://www.banxico.org.mx/SieAPIRest/service/v1/token/registro`). Token va en variable de entorno `BANXICO_TOKEN`.
- **Fallback:** `https://api.exchangerate.host/latest?base=USD&symbols=MXN` (sin token). Se usa solo si Banxico falla o no hay token.
- **Cache:** tabla `tipos_cambio_dia` indexada por fecha (UNIQUE). Una sola consulta a la fuente externa por día. Endpoint `/api/fx/usd-mxn?fecha=` resuelve cache → fuente → fallback.
- **Refresco manual:** `POST /api/fx/refresh` (admin) reemplaza el valor del día.

### D3. Tres tipos de línea
Se introduce `DetalleOrden.tipo_linea` (enum):

| tipo_linea | Origen del precio | Afecta inventario | Caso de uso |
|---|---|---|---|
| `PRODUCTO_CATALOGO` | `Producto.costo_compra` + utilidad | sí (reserva) | SKU del catálogo DASIC |
| `PRODUCTO_FANTASMA` | `costo_unitario` capturado | no | Producto físico no catalogado, requiere proveedor sugerido para auto-OC |
| `SERVICIO` | `costo_unitario` capturado | no | Programación PLC, instalación, capacitación |

Las primeras dos pueden disparar auto-OC; `SERVICIO` no.

Cuando se agrega al carrito un producto del catálogo cuyo `Producto.es_servicio = true`, el frontend setea `tipo_linea = SERVICIO` automáticamente (no reserva inventario aunque tenga `producto_id`).

### D4. Auto-OC
Lógica:
1. Recorrer detalles de una cotización.
2. Para cada `PRODUCTO_CATALOGO` con `stock_disponible < cantidad`: agregar a faltantes.
3. Para cada `PRODUCTO_FANTASMA` con `proveedor_sugerido_id` no nulo: agregar a faltantes.
4. Agrupar por `proveedor_id`. Cada grupo se vuelve una `OrdenCompra` estatus `borrador`.
5. Si hay productos `PRODUCTO_CATALOGO` sin `proveedor_principal_id` y `proveedor_alterno_id`, devolver warning `productos_sin_proveedor`. El frontend bloquea la generación hasta que se asignen.
6. La OC creada se vincula via el campo existente `OrdenCompra.cotizacion_id`.

Cantidad a comprar = `cantidad_cotizada − stock_disponible`, mínimo 0.

### D5. Producto: nuevos campos y relaciones
- `proveedor_principal_id` (FK proveedores, nullable)
- `proveedor_alterno_id` (FK proveedores, nullable)
- `tiempo_entrega_dias` (int, default 7)
- `es_servicio` (bool, default false) — productos del catálogo marcados como servicio (no afectan inventario aunque sean del catálogo)

### D6. Cotizador frontend
- TC autollenado al cargar y al cambiar moneda a USD. Badge `Banxico · 30 abr · 17.45` con popover (refrescar / ver histórico).
- Selector de tipo de línea: tres botones `+ Producto · + Servicio · + Fantasma`. La búsqueda actual queda detrás de `+ Producto`.
- Cada renglón del carrito muestra badge de stock — verde / amarillo (sin stock pero hay proveedor) / rojo (sin stock y sin proveedor).
- Footer: botón **"Sugerir OC"** que abre modal con preview agrupada por proveedor; botón **"Generar OCs"** persiste.
- Side-panel post-guardado: muestra OCs vinculadas con su folio.

### D7. Inventario frontend
- Columna nueva `Disponible` (= actual − reservado), ordenable.
- Click en producto → side-panel con: ficha, proveedor principal/alterno, último costo, **timeline de movimientos (30 días)**, cotizaciones activas que reservan.
- Modal "Ajuste de inventario" con motivo obligatorio.
- Filtros: en stock / agotado / con cotizaciones / sin proveedor asignado.

## Modelo de datos

### Cambios en tablas existentes

**`productos`** (alembic upgrade):
- + `proveedor_principal_id INTEGER NULL` (FK proveedores)
- + `proveedor_alterno_id INTEGER NULL` (FK proveedores)
- + `tiempo_entrega_dias INTEGER NOT NULL DEFAULT 7`
- + `es_servicio BOOLEAN NOT NULL DEFAULT false`

**`detalles_orden`**:
- + `tipo_linea VARCHAR(20) NOT NULL DEFAULT 'PRODUCTO_CATALOGO'` (enum: PRODUCTO_CATALOGO, PRODUCTO_FANTASMA, SERVICIO)
- + `proveedor_sugerido_id INTEGER NULL` (FK proveedores) — para fantasmas que vayan a auto-OC

### Tablas nuevas

**`movimientos_stock`**:
- `id PK`
- `producto_id FK NOT NULL`
- `tipo VARCHAR(20)` (ENTRADA · SALIDA · AJUSTE · RESERVA · LIBERACION)
- `cantidad INTEGER NOT NULL` (signed; reserva positiva, liberación negativa, salida negativa, entrada positiva)
- `referencia_tipo VARCHAR(20)` (cotizacion · venta · oc · manual)
- `referencia_id INTEGER NULL`
- `motivo TEXT NULL`
- `usuario_id FK NULL`
- `creado_en TIMESTAMPTZ DEFAULT now()`
- `stock_resultante INTEGER NOT NULL` (snapshot post-movimiento, para auditoría rápida)
- INDEX (producto_id, creado_en DESC)

**`tipos_cambio_dia`**:
- `id PK`
- `fecha DATE UNIQUE NOT NULL`
- `usd_mxn DECIMAL(12,6) NOT NULL`
- `fuente VARCHAR(20)` (BANXICO · EXCHANGERATE · MANUAL)
- `obtenido_en TIMESTAMPTZ DEFAULT now()`

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/fx/usd-mxn?fecha=YYYY-MM-DD` | TC del día (cache → fuente → fallback). Default hoy. |
| POST | `/api/fx/refresh` | Fuerza refetch del TC del día (admin). |
| POST | `/api/ventas/{id}/sugerir-oc` | Devuelve `{ por_proveedor: [...], sin_proveedor: [...] }`. No persiste. |
| POST | `/api/ventas/{id}/generar-oc` | Crea las OCs en estado borrador. Devuelve folios generados. |
| GET | `/api/inventario/movimientos?producto_id=&dias=30` | Timeline de movimientos. |
| POST | `/api/inventario/movimientos` | Ajuste manual con `tipo`, `cantidad`, `motivo`. Admin/asistente. |
| GET | `/api/productos/{id}/disponibilidad` | `{ stock_actual, reservado, disponible, en_oc_pendiente }`. |
| PUT | `/api/productos/{id}` | Existente; ahora acepta los nuevos campos (proveedores, tiempo_entrega, es_servicio). |
| POST | `/api/inventario/liberar-vencidas` | Emite LIBERACION para cotizaciones con fecha_vencimiento < hoy. Idempotente. Admin. |

Endpoints existentes que cambian comportamiento internamente (sin cambiar contrato externo):
- `POST /api/ventas/`: crea movimientos `RESERVA` por cada línea de catálogo.
- `POST /api/ventas/{id}/convertir`: convierte `RESERVA` → `SALIDA` y descuenta `stock_actual`.
- `DELETE/cancel cotización`: emite `LIBERACION`.

## Edge cases relevantes

- **Editar cotización con cambio de cantidad:** se calcula delta y se aplica un único `RESERVA` o `LIBERACION` por la diferencia, no se borra y recrea.
- **Convertir cotización con stock insuficiente:** falla con HTTP 400 indicando los SKUs problemáticos. Sugerir generar OC primero.
- **Producto cambia de proveedor entre cotizar y generar OC:** se usa el proveedor vigente al momento de generar OC; el guardado de cotización no congela proveedor.
- **TC de Banxico no disponible (fines de semana / días feriados):** Banxico devuelve el último día hábil, lo aceptamos. Si la respuesta tiene fecha distinta a la solicitada, lo registramos pero usamos ese valor.
- **Cotización con líneas mixtas (USD origen, MXN cotización):** ya soportado; sigue convirtiendo línea a línea según `moneda_origen_linea` y `tipo_cambio` de la cotización.
- **Cotización vencida con stock reservado:** un job (CronCreate o tarea on-demand) corre diariamente y emite `LIBERACION` para cotizaciones cuya `fecha_vencimiento < (hoy − 1 día)` y siguen en estatus COTIZACION. Por ahora MVP: endpoint manual `POST /api/inventario/liberar-vencidas` para que el usuario lo dispare desde inventario o se programe vía `/loop`.
- **Producto eliminado con movimientos:** ya bloqueamos delete si está en órdenes; ahora también si tiene movimientos. La opción es marcar inactivo en una iteración futura.

## Testing manual (sin suite automatizada hoy)

1. Crear cotización con un producto stock=0, sin proveedor asignado → ver badge rojo + warning al generar OC.
2. Asignar proveedor al producto → ver badge amarillo + auto-OC genera 1 OC con folio correcto.
3. Cotización con 3 líneas: producto catálogo (stock OK), fantasma con proveedor, servicio → al guardar, sólo la primera reserva inventario.
4. TC del día: borrar `tipos_cambio_dia` y abrir cotizador → ver fetch a Banxico, segundo refresh es cache.
5. Convertir cotización → ver `stock_actual` baja y `RESERVA` se transforma en `SALIDA` en `movimientos_stock`.
6. Inventario: nueva columna `Disponible` refleja stock − reservas; click abre side-panel con timeline real.
7. Ajuste manual de inventario: motivo obligatorio, deja registro.

## Riesgos

- **Token Banxico:** si el usuario no se registra para obtener el token, el sistema usa fallback. Documentamos el registro en CLAUDE.md.
- **Reservas huérfanas:** si una cotización se borra de DB sin pasar por el endpoint, las reservas quedan colgadas. Mitigación: endpoint manual de "limpieza de reservas huérfanas" que detecta movimientos RESERVA cuya orden ya no existe y los anula.
- **Concurrencia:** dos usuarios reservando el último ítem al mismo tiempo. Mitigación: `SELECT … FOR UPDATE` en producto al insertar reserva. Aceptable en single-tenant single-DB.

## Listo para plan de implementación

Próximo paso: invocar `superpowers:writing-plans` para producir el plan táctico (orden de archivos, comandos de migración, tests manuales por bloque, criterios de listo).
