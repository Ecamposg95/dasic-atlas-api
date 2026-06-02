# Cotizador Fase 1 — Costo de origen fijo + robustez P0/P1 — Design

**Fecha:** 2026-06-02
**Contexto:** El cotizador es el módulo más importante. Trabajo dividido en 3 fases: **Fase 1** (este spec) = costo de origen siempre visible/fijo + robustez P0/P1; Fase 2 = migración del tema a theme-aware; Fase 3 = refactor profundo (autosave, split de archivos, Decimal cleanup, validación de cálculo). Este spec cubre solo la Fase 1.

## Hallazgos relevantes (auditados)

- El **costo de origen** mostrado en `CartRow.tsx` es `{item.productCurrency} ${item.cost}` y **NO se convierte** al cambiar la moneda de la cotización (correcto). Pero solo se muestra cuando `mostrarOrigen = item.productCurrency !== moneda || descuento_proveedor > 0` → cuando la línea coincide con la moneda de la cotización, **se oculta**, lo que parece inconsistente. El "Costo OC" (con etiqueta "OC") SÍ convierte (correcto: es lo que se paga al proveedor en la moneda de la cotización).
- `TotalsBar.tsx`: el botón de guardar **avisa** las razones (sin cliente, sin líneas) pero **no bloquea** duro; al **fallar** el guardado el `onError` setea error pero el flujo de éxito hace `window.location.href = /seguimiento?folio=...` (riesgo: redirección/pérdida de carrito). `cantidad` ya se valida `gt=0` en el schema de línea del backend.
- No hay guard `beforeunload` para cambios sin guardar.
- `OrdenVentaCreate` no valida que `detalles` tenga ≥1 línea ni un `max_items`.

## Decisiones (acordadas)

1. Mostrar **siempre** el costo de origen (divisa + valor), fijo, claramente diferenciado del OC.
2. Bloquear (no solo avisar) guardar sin cliente / sin líneas / con cantidad ≤ 0.
3. Al fallar el guardado: conservar el carrito y mostrar error claro; redirigir solo en éxito.
4. Aviso `beforeunload` con cambios sin guardar.
5. Backend: `detalles` no vacío + `max_items` + mensaje amable si falta cliente.

## Arquitectura

### A. Costo de origen siempre visible y fijo

`web/src/features/cotizador/components/CartRow.tsx`:
- Eliminar el gating por `mostrarOrigen`: el bloque del costo de origen (`{item.productCurrency} ${fmt(Number(item.cost))}`) se renderiza **siempre**, con una etiqueta breve "Origen" y su tooltip actual. Se conserva el bloque "Costo OC" convertido tal cual. (La variable `mostrarOrigen` puede eliminarse si queda sin uso.)
- `web/src/features/cotizador/components/RowExpanded.tsx`: asegurar que el costo de origen mostrado use `item.cost` + `item.productCurrency` (fijo) y esté etiquetado; el costo OC convertido se conserva.

> Sin cambios de cálculo: el costo de origen ya es fijo; el cambio es de visibilidad/etiquetado para eliminar la confusión.

### B. Robustez P0/P1

**Bloqueo de guardado** (`TotalsBar.tsx`):
- Calcular `puedeGuardar = cliente_id != null && cart.length > 0 && cart.every((l) => l.qty > 0) && !tcInvalido`.
- El botón de guardar usa `disabled={!puedeGuardar || guardar.isPending}`. Se conserva el listado de razones (ya existe) como ayuda visual.

**Manejo de fallo al guardar** (`TotalsBar.tsx` / hook de guardado):
- En éxito: redirigir/navegar como hoy (con el folio devuelto).
- En error: **no** redirigir; conservar el carrito y el estado; mostrar un toast `kind:'error'` + el banner de error existente con `e.detail`. Asegurar que ninguna ruta de error limpie el carrito.

**Guard `beforeunload`** (`CotizadorPage.tsx`):
- `useEffect` que registra `beforeunload`: si `cart.length > 0` (cambios potenciales sin guardar), `e.preventDefault()` + `e.returnValue = ''` para que el navegador muestre el aviso nativo. Cleanup al desmontar.

**Backend** (`app/schemas/sales.py::OrdenVentaCreate` + `app/routers/ventas.py`):
- `detalles: List[DetalleOrdenCreate] = Field(..., min_length=1, max_length=500)` (≥1 línea, tope de 500).
- En `ventas.py`, donde hoy responde 404 si no encuentra el cliente, devolver **422** con mensaje amable ("Selecciona un cliente válido para guardar la cotización."). (El `gt=0` de cantidad ya existe.)

### C. Cobertura

| Ask del usuario | Cómo |
|------------------|------|
| Costo de origen fijo (divisa+valor), no convierte | Siempre visible, usa `item.cost`/`productCurrency`, sin conversión. |
| Robustez (no guardar basura, no perder carrito) | Bloqueo de guardado + manejo de error + beforeunload + validación backend. |

## Fuera de alcance (Fase 1)

- Migración del tema claro (Fase 2).
- Autosave, split de `store.ts`/`CotizadorPage.tsx`, Decimal/number cleanup, endpoint de validación de cálculo (Fase 3).
- Exponer `descuento_proveedor` en la UI / tooltips de fantasma (P2, posible en Fase 3).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`. Checks manuales recomendados.
- **Bajo riesgo:** cambios aditivos/de visibilidad + validaciones; no se altera la lógica de cálculo ni el contrato de guardado (salvo endurecer validación).
- **Backend `min_length`/`max_length` en List:** Pydantic v2 (`Field(min_length=..., max_length=...)` aplica a longitud de lista). Verificar que no rompa borradores/recotizar (esos no pasan por `OrdenVentaCreate` con 0 líneas).
