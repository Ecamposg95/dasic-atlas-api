# Sub-2 — Contacto en la cotización — Design

**Fecha:** 2026-06-02
**Contexto:** Tras el sub-1 (empresas + contactos), la cotización debe registrar opcionalmente QUÉ contacto (persona) de la empresa hizo el pedido, mostrarlo en el picker del cotizador (empresa→contacto) y en el PDF/Word ("Atención: <contacto>"). Cambio **aditivo** extremo a extremo (`contacto_id` nullable en `OrdenVenta`).

## Decisiones de producto (acordadas)

1. Capturar el contacto en la orden (`OrdenVenta.contacto_id` nullable).
2. En el picker: al elegir una empresa, el contacto se **autollena con el principal** (`es_principal`) de esa empresa; editable o vaciable; se resetea al cambiar de empresa.
3. No crear contactos desde el cotizador (se gestionan en el área de Empresas del sub-1).

## Arquitectura

### 1. Backend

- `app/models/sales.py::OrdenVenta`: `contacto_id = Column(Integer, ForeignKey("contactos.id"), nullable=True)` + `contacto = relationship("Contacto", foreign_keys=[contacto_id])`.
- Migración `migrations/versions/20260601_06_orden_contacto.py` (down_revision `20260601_05`): `ALTER TABLE ordenes_venta ADD COLUMN contacto_id INTEGER REFERENCES contactos(id)`. Espejo en `_BACKFILL_DDL` (`ADD COLUMN IF NOT EXISTS contacto_id INTEGER REFERENCES contactos(id)`).
- `app/schemas/sales.py::OrdenVentaCreate`: `contacto_id: Optional[int] = None` (después de `cliente_id`).
- `app/routers/ventas.py`: agregar `contacto_id` en los 3 constructores/asignaciones de cabecera — POST crear (`contacto_id=orden_data.contacto_id`), PUT actualizar (`orden.contacto_id = orden_update.contacto_id`), recotizar/clone (`contacto_id=origen.contacto_id`). En `/detalle-json` agregar `"contacto_id": orden.contacto_id`.
- **PDF** (`PDF_TEMPLATE_VENTA`, bloque cliente): tras el bloque del cliente, `{% if orden.contacto %}<div class="row"><span class="lbl">Atención:</span> {{ orden.contacto.nombre }}</div>{% endif %}`.
- **Word** (`app/services/word_service.py::build_cotizacion_docx`, bloque cliente): tras los extras del cliente, `if orden.contacto:` → párrafo "Atención: <orden.contacto.nombre>".

### 2. Frontend (cotizador)

- `types.ts`: `OrdenVentaCreate` += `contacto_id: number | null`; el header de `OrdenVentaDetail` += `contacto_id: number | null`. Nuevo tipo `ContactoLite = { id: number; nombre: string; cargo: string | null; es_principal: boolean }`.
- `store.ts`: estado `contacto_id: number | null` (initial null), setter `setContacto`, e hidratación (`contacto_id: orden.contacto_id ?? null`) en `hydrateFromOrden`.
- `lib/serialize.ts`: `CotizadorSnapshot` += `contacto_id`; `buildSavePayload` manda `contacto_id: s.contacto_id`.
- `components/ClientPicker.tsx`: bajo la empresa seleccionada, un `<select>` "Atiende a:" poblado con los contactos de la empresa (`GET /api/clientes/{cliente_id}/contactos`, vía un useQuery local con `enabled` cuando hay `cliente_id`). Bind a `contacto_id`/`setContacto`. Al **seleccionar una empresa** desde la búsqueda: `setCliente(c.id)` + `setContacto(null)`. Un `useEffect`: cuando llegan los contactos y `contacto_id` es null, autollenar con el `es_principal` (o el primero). El guard "solo si null" evita pisar el contacto de una orden ya cargada en edición.
- La página del cotizador que provee el snapshot a `buildSavePayload` debe incluir `contacto_id` del store (donde arma el `CotizadorSnapshot`).

### 3. Cobertura

| Requisito | Cómo |
|-----------|------|
| Orden guarda el contacto | `OrdenVenta.contacto_id` persistido en POST/PUT/recotizar. |
| Picker empresa→contacto | Sub-selector en ClientPicker con autollenado del principal. |
| "Atención" en documentos | PDF y Word renderizan el contacto de la orden. |
| Round-trip en edición | `/detalle-json` expone `contacto_id`; hidratación lo restaura. |

## Fuera de alcance

- Crear/editar contactos desde el cotizador (sub-1 ya tiene esa UI en Empresas).
- Dedup de empresas (sub-3).
- Cambiar la línea "Nombre:" existente del PDF (es el contacto principal denormalizado del cliente; "Atención:" es el contacto específico de la orden — pueden coexistir).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`.
- **Migración aditiva** (columna nullable + FK) → bajo riesgo; espejo en `_BACKFILL_DDL`; la FK referencia `contactos` (creada en `20260601_05`).
- **Hidratación:** el autollenado del principal solo aplica cuando `contacto_id` es null → no pisa órdenes ya guardadas con contacto.
