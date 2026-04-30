# Glosario

| Término | Definición |
|---|---|
| **Auto-OC** | Generación automática de Órdenes de Compra a partir de una cotización con faltantes de stock. Agrupa por proveedor. Ver `app/services/auto_oc_service.py`. |
| **Backfill DDL** | Sentencias `ALTER TABLE … ADD COLUMN IF NOT EXISTS …` que se ejecutan en `lifespan` cada vez que la app arranca. Compensa que el deploy en Railway no corre `alembic upgrade head`. Vive en `app/db/seeds.py::_BACKFILL_DDL`. |
| **Cotización** | `OrdenVenta` con `estatus = COTIZACION`. Folio `C-YYMMNNN`. Genera reservas de stock. |
| **Detalle (línea)** | Fila de una cotización u OC. Tiene `cantidad`, `costo_base_linea`, `precio_unitario`, `subtotal`. |
| **Disponible** | `stock_actual - reservado`. Lo que un nuevo cliente puede comprar. |
| **Físico** | `stock_actual` real del producto. Lo que está en el almacén. |
| **Folio** | Identificador legible. Formato real DASIC: `C-YYMMNNN` cot, `V-YYMMNNN` venta, `OC-YYMMNNN` orden compra, `R-YYMMNNN` remisión. |
| **Línea fantasma** | `DetalleOrden` sin `producto_id`, con `sku_libre` + `descripcion_libre` + `costo_unitario`. Producto físico no catalogado. Puede ir a auto-OC si tiene `proveedor_sugerido_id`. |
| **Línea servicio** | `DetalleOrden.tipo_linea = 'servicio'`. Programación, instalación, capacitación. **No reserva inventario**. |
| **MovimientoStock** | Audit trail de cambios de stock. Tipos: `ENTRADA`, `SALIDA`, `AJUSTE`, `RESERVA`, `LIBERACION`. Cada row tiene `cantidad` (signed), `referencia_tipo/id`, `motivo`, `usuario_id`, `stock_resultante`. |
| **OC borrador** | `OrdenCompra.estatus = 'borrador'`. Generada por auto-OC. Aún no enviada al proveedor. |
| **Owner scoping** | Filtro de queries por dueño cuando el rol es VENTAS. `OrdenVenta.vendedor_id = current_user.id` y `Cliente.creado_por_id = current_user.id`. Helper: `app/security/permissions.py::scope_query_by_owner`. |
| **Pipeline kanban** | Tablero de cotizaciones agrupadas por estado: Nueva (<24h), Seguimiento, Por vencer (≤3d), Vencida, Convertida (30d). En el dashboard premium. |
| **Producto comercial** | `sku_comercial`: el código que ve el cliente en el PDF. Suele ser el catalog # del fabricante. |
| **Producto interno** | `sku`: identificador interno DASIC, único en la tabla. Si es vacío al crear, se autogenera (`DAS-YYMM-XXXX`). |
| **Reservado** | Suma de cantidades en líneas de cotizaciones activas (`estatus = COTIZACION`). No descuenta stock_actual; sí descuenta disponible. |
| **Recotizar** | Clonar una cotización con un nuevo folio versionado (`C-2604227V2`). La original queda archivada. Endpoint `POST /api/ventas/{id}/recotizar`. |
| **Seed** | Carga inicial idempotente de productos / clientes / proveedores / cotizaciones de muestra desde `context/`. Corre en `lifespan` por default. |
| **TC FIX (Banxico)** | Tipo de cambio FIX para liquidación 48h, oficial de la SHCP. Serie `SF63528` en Banxico SIE API. Requiere token gratis registrado. |
| **Utilidad aplicada** | Margen porcentual sobre `costo_base_linea`. `precio_unitario = costo_base * (1 + utilidad/100)`. |
| **Vendedor (rol)** | `RolUsuario.VENTAS` (alias `VENDEDOR`). Ve y edita sólo sus propios recursos. |
