# Flujos funcionales

## Vendedor — flujo principal: cotización → venta

1. Login en `/`. Sidebar muestra: Dashboard, Cotizador, Seguimiento, Clientes, Compras, Reportes.
2. **Cotizador** (`/ventas/cotizador`):
   - Selecciona cliente (sólo ve los suyos — los que él creó).
   - TC USD/MXN se autollena desde `/api/fx/usd-mxn` (Banxico FIX o fallback). Badge muestra fuente y fecha.
   - Tres botones para agregar líneas:
     - **+ Producto**: busca catálogo. La línea muestra badge stock (verde / amarillo si hay proveedor / rojo).
     - **+ Servicio**: descripción + tarifa + horas. No reserva stock.
     - **+ Fantasma**: producto especial fuera de catálogo, requiere costo + proveedor sugerido para auto-OC.
   - Cantidad / utilidad % por línea. Total recalcula al vuelo.
   - Guarda: genera folio `C-YYMMNNN`. Las líneas de catálogo emiten `RESERVA` en `movimientos_stock`.
3. **Sugerir OC** (botón): si hay faltantes, abre modal con preview agrupada por proveedor (cantidades = `linea.cantidad - stock_disponible_otros`). Click "Generar" crea OCs en estado `borrador`.
4. **Convertir a venta** (en /seguimiento o desde cotizador):
   - Verifica disponible considerando reservas de otras cotizaciones.
   - Emite `LIBERACION` (cierra reserva conceptual) + `SALIDA` (descuenta `stock_actual`).
   - Folio muta `C-…` → `V-…`.
5. **Cancelar cotización**: emite `LIBERACION` por el neto reservado. Stock vuelve a estar disponible.

## Gerente Comercial — supervisión

- **Dashboard premium**: ve KPIs del equipo (ventas mes, pipeline, conversión, margen). Pipeline kanban con todas las cotizaciones, no sólo las suyas. Top clientes/productos/vendedores.
- Puede actuar sobre cualquier cotización (convertir, cancelar, recotizar).
- Genera reportes y exporta CSV.
- No accede a usuarios.

## Operativo (almacén) — recepción y ajustes

- **Inventario** (`/inventario`):
  - Tabla con columnas Físico / Reservado / Disponible / Mínimo / Costo.
  - Click en fila abre side-panel con timeline de movimientos (30 días) y botón "Ajuste manual".
- **Ajuste manual** (admin/gerente/operativo): modal con cantidad signed (+entrada / -salida) y motivo obligatorio. Crea row tipo `AJUSTE` en `movimientos_stock`.
- **Recibir OC**: marca OC como recibida. Crea movimientos tipo `ENTRADA` para cada DetalleCompra. (En backlog si aún no está completado el endpoint).
- No accede a Cotizador, Clientes, Reportes, Usuarios.

## Admin — todo

- Todos los flujos anteriores +
- **Usuarios** (`/usuarios`): CRUD + reset password (botón llave). Cambia roles.
- **Productos**: alta/edit/delete con asignación de proveedor principal/alterno.
- **Configuración**: env vars (`BANXICO_TOKEN`, `SMTP_*`, `SEED_CONTEXT_DISABLED`) en Railway.
- **Seed manual**: `POST /api/admin/seed-context` desde DevTools.

## Flujo de stock end-to-end (clave para entender el sistema)

| Evento | Movimiento | Afecta `stock_actual`? | `disponible` cambia? |
|---|---|---|---|
| Crear cotización con producto catálogo | `RESERVA(+N)` | No | Sí (-N) |
| Editar cotización (cambio cantidad) | `LIBERACION(-old) + RESERVA(+new)` | No | Sí (delta) |
| Cancelar cotización | `LIBERACION(-N)` | No | Sí (+N) |
| Convertir cotización a venta | `LIBERACION(-N) + SALIDA(-N)` | Sí (-N) | Sí (+N de la liberación, -N de la salida = misma resta neta) |
| Ajuste manual entrada | `AJUSTE(+N)` | Sí (+N) | Sí (+N) |
| Ajuste manual salida | `AJUSTE(-N)` | Sí (-N) | Sí (-N) |
| Recibir OC | `ENTRADA(+N)` | Sí (+N) | Sí (+N) |

Donde:
- `disponible = stock_actual - sum(reservas activas en cotizaciones COTIZACION)`.
- "Reserva activa" = movimiento `RESERVA - LIBERACION` cuya `OrdenVenta` referenciada sigue en estatus `COTIZACION`.

Ver detalles en `app/services/stock_service.py`.

## Auto-OC

Cuando guardás una cotización con productos catálogo cuyo `stock_disponible < cantidad_pedida`, o con productos fantasma con `proveedor_sugerido_id`:

1. `POST /api/ventas/{id}/sugerir-oc` devuelve preview agrupada por proveedor.
2. Si algún producto del catálogo no tiene `proveedor_principal_id` ni `proveedor_alterno_id`, devuelve `sin_proveedor:[]` y el usuario debe asignar antes.
3. `POST /api/ventas/{id}/generar-oc` persiste OCs en estado `borrador`, vinculadas vía `OrdenCompra.cotizacion_id`.

Ver `app/services/auto_oc_service.py`.

## RBAC en una imagen

Para detalles ver [70_rbac_y_roles.md](70_rbac_y_roles.md). Resumen:

- **Admin**: todo.
- **Gerente**: todo excepto Usuarios.
- **Ventas**: cotiza y vende sólo lo suyo (filtra por `vendedor_id` y `creado_por_id`). No ve costos.
- **Operativo**: sólo Inventario y recepción de OCs. No ve cotizaciones ni Cotizador.
