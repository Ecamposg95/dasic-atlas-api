# US-009 — Promover Fantasma a Producto + Stock — Design

**Fecha:** 2026-06-01
**Alcance:** US-009 (EPIC 02, "Spec b"). Convertir un producto fantasma en producto real del catálogo con entrada de stock auditada (kardex), como acción manual ejecutable tras la llegada del producto.

## Contexto actual (auditado)

- `POST /api/fantasmas/{id}/promover` (`app/routers/fantasmas.py:202-242`) ya existe: crea `Producto` con `stock_actual=0` **sin kardex**, copia solo 6 campos (sku, nombre, descripcion, costo_compra, moneda_compra, proveedor_principal_id), **exige** `sku_libre`, marca el fantasma `estado=PROMOVIDO` + `promovido_a_producto_id`.
- `app/services/stock_service.py::aplicar_movimiento(db, *, producto, tipo, cantidad, referencia_tipo, referencia_id, motivo, usuario)` es el único camino auditado para mover stock; tipo `ENTRADA` aumenta `stock_actual` y registra una fila en `movimientos_stock`.
- `siguiente_sku_para(db, abreviatura)` (`app/routers/catalogos.py:60-87`) genera SKU interno `{ABREV}-NNNN` desde `Marca.abreviatura`.
- `ProductoFantasma` ya tiene marca/marca_id/clave_prod_serv/clave_unidad_sat/observaciones (EPIC 02) — pero `promover` no los copia.
- `Producto` requiere `sku` (unique, NOT NULL), `nombre` (NOT NULL); el resto tiene defaults. No tiene columna `observaciones`.
- La recepción de OC (`compras.py::recibir_oc`) salta líneas sin `producto_id`; los fantasmas **no** son líneas físicas de OC (solo pasan a `estado=EN_OC`). `DetalleCompra` no tiene `fantasma_id`.

## Decisiones de producto (acordadas)

1. **Disparo: manual mejorado.** Se conserva el botón "Promover" manual; se ejecuta cuando el producto llegó. No se automatiza en la recepción de OC ni se toca el flujo de compras.
2. **SKU editable y sugerido.** El modal pre-llena el SKU (sku_libre del fantasma; si no, `{ABREV_MARCA}-NNNN` cuando hay marca; si no, vacío), editable y validado único antes de crear.
3. **Stock auditado.** La entrada inicial pasa por `aplicar_movimiento` (kardex), no por asignación directa.

## Arquitectura

### 1. Backend — `POST /api/fantasmas/{id}/promover` (extendido)

Nuevo body Pydantic en `app/schemas/fantasmas.py`:

```
class PromoverFantasmaInput(BaseModel):
    sku: str
    cantidad: int = 0          # entrada inicial; 0 = solo crear catálogo
    stock_minimo: Optional[int] = None
```

Flujo del endpoint (reemplaza el cuerpo actual):
- Carga el fantasma (404 si no existe).
- Si `estado` in (`PROMOVIDO`, `DESCARTADO`) → 409.
- `sku = payload.sku.strip()`; si vacío → 400.
- Si `cantidad < 0` → 400.
- Si ya existe un `Producto` con ese `sku` → 409 "SKU ya existe".
- Crea `Producto` copiando: `sku`, `nombre`=descripcion_original[:150], `descripcion`=descripcion_original, `costo_compra`=costo_referencia, `moneda_compra`=moneda_referencia, `marca`=fantasma.marca, `marca_id`=fantasma.marca_id, `clave_prod_serv`, `clave_unidad_sat`, `proveedor_principal_id`=proveedor_sugerido_id, `stock_minimo` si viene. `stock_actual` arranca en 0.
- `db.flush()` (asigna `nuevo.id`).
- Si `cantidad > 0`: `aplicar_movimiento(db, producto=nuevo, tipo=ENTRADA, cantidad=cantidad, referencia_tipo="promocion_fantasma", referencia_id=fantasma.id, motivo=f"Promoción fantasma {sku}", usuario=current_user)` → fija `stock_actual` y registra kardex.
- Marca `fantasma.estado="PROMOVIDO"`, `promovido_a_producto_id=nuevo.id`.
- `db.commit()`. Retorna `{ fantasma_id, producto_id, sku, stock_inicial: cantidad }`.

Manejo de errores: try/except con rollback y `HTTPException(500, ...)` como el resto del router; las validaciones lanzan 400/409 antes del movimiento.

### 2. Backend — sugerencia de SKU: `GET /api/fantasmas/{id}/sugerir-sku`

Devuelve `{ "sku_sugerido": str }`:
- Si `fantasma.sku_libre` → ese valor.
- Elif `fantasma.marca_id` y la marca tiene `abreviatura` → `siguiente_sku_para(db, abreviatura)`.
- Else → `""`.

(Reusa `siguiente_sku_para` importándola de `app/routers/catalogos.py`.)

### 3. Frontend — `PromoverModal` (feature fantasmas)

- `web/src/features/fantasmas/components/PromoverModal.tsx` (nuevo): campos **SKU** (editable, pre-llenado), **cantidad recibida** (number, default 0), **stock mínimo** (opcional). Al abrir, consulta `GET /api/fantasmas/{id}/sugerir-sku` para pre-llenar el SKU.
- Hook `usePromoverFantasma` (mutation POST) + `useSugerirSku` (query) en el hook existente de la feature.
- `FantasmasPage`: el botón/acción "Promover" existente abre el modal en vez de llamar directo. Tras éxito: toast con folio/SKU, `invalidateQueries(['fantasmas'])` y `invalidateQueries(['productos'])`. Errores 409 (SKU duplicado / ya promovido) se muestran en el modal.

### 4. Cobertura US-009

| Criterio | Cómo se cubre |
|----------|---------------|
| Acción "Promover/Agregar a stock" | Botón existente → `PromoverModal`. |
| Conserva datos del fantasma | Copia nombre/descripcion/costo/moneda/marca/SAT/proveedor. |
| Crea producto real en catálogo | Crea `Producto` con SKU validado único. |
| Registra stock inicial / entrada | `aplicar_movimiento` ENTRADA (kardex) si cantidad > 0. |
| Fantasma vinculado al producto | `estado=PROMOVIDO`, `promovido_a_producto_id`. |
| Ejecutable tras OC / llegada | Acción manual disponible en cualquier momento post-llegada. |

## Fuera de alcance (YAGNI)

- Automatizar la promoción en la recepción de OC.
- Agregar `fantasma_id` a `DetalleCompra` / incluir fantasmas como líneas físicas de OC (US-026/027).
- Referenciar la OC en el movimiento de kardex (se eligió disparo manual sin OC).
- Columna `observaciones` en `Producto` (no existe; la descripción ya conserva el texto del fantasma).
- Migraciones de esquema: este diseño **no agrega columnas** — usa modelos y servicios existentes.

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend con `python3 -m py_compile`; frontend con `cd web && npm run build`. Checks manuales recomendados post-deploy.
- **Sin migración** → riesgo de esquema nulo. El único cambio de datos es crear `Producto` + `MovimientoStock`, ya soportados.
- **SKU único**: validación explícita evita romper la constraint unique; el modal permite corregir.
- **Idempotencia**: `estado` PROMOVIDO/DESCARTADO bloquea re-promover (409).
- **Stock auditado**: toda entrada pasa por `aplicar_movimiento` (cumple la regla de inventario auditable de CLAUDE.md).
