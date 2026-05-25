# Cotizador UX Wave — Diseño

**Fecha:** 2026-05-25
**Estado:** Aprobado, listo para plan de implementación
**Alcance:** Frontend SPA, sub-features de cotizador. Backend solo se toca para exponer una variante del endpoint de fantasmas (si hace falta).

## Origen

Auditoría de la historia de uso del cotizador identificó 5 gaps. Este sub-proyecto los cierra en una sola wave.

## Sub-features

### F1 — Aviso "Selecciona cliente primero"

**Problema:** El usuario puede tocar la divisa, el TC o agregar productos antes de elegir cliente. Solo se da cuenta al guardar (el botón Guardar lista "selecciona cliente" en `reasons`).

**Solución (no invasiva):**
- Mostrar un banner ámbar en `HeaderCotizacion.tsx` arriba del grid cuando `cliente_id == null` y el cart tiene al menos una línea, o cuando el usuario tocó la moneda/TC sin cliente:
  - Texto: "Selecciona un cliente para que esta cotización pueda guardarse."
  - Ícono `AlertTriangle` ámbar; cierra automáticamente al elegir cliente
- No se deshabilita nada (decisión explícita: el usuario quiere flexibilidad para armar la cot incluso sin cliente y elegirlo al final)

### F2 — Buscador unificado: 3er tab "Fantasmas"

**Problema:** El cotizador busca productos del catálogo y servicios, pero no los fantasmas ya registrados. El usuario crea fantasmas duplicados cada vez. El backend ya tiene `GET /api/fantasmas/?q=...` (`app/routers/fantasmas.py:42`).

**Solución:**
- En `CatalogoFiltros.tsx`, agregar una 3ra pestaña "Fantasmas" junto a "Productos" / "Servicios"
- Crear hook `useFantasmasSearch.ts` que llame `/api/fantasmas/?q=<query>&estado=PENDIENTE` con `staleTime: 30s` y debounce 300ms (mismo patrón que `useProductosSearch`)
- En `ProductSearch.tsx`:
  - Cuando `tipo === 'fantasma'`, mostrar la lista de fantasmas matched con ícono `Ghost`, descripción, sku_libre, costo+moneda, badge `proveedor_sugerido_nombre` si existe
  - Click en una fantasma existente → `addLineaAdhoc({...})` con los campos del fantasma persistido. NO abre el modal de captura
  - Estado vacío de Fantasmas: "Sin coincidencias en fantasmas previos. ¿Capturar como nuevo?" → botón que abre `AgregarFantasmaModal` (flujo actual)
- El botón "+ Fantasma" (captura ad-hoc nueva) se mantiene visible siempre, a la derecha del input — para forzar captura nueva sin buscar
- El `Producto` que devuelve `/api/fantasmas/` y el shape esperado por `addLineaAdhoc` difieren: hay que adaptar campos (`descripcion` ← `descripcion_original`, `costo` ← `costo_referencia`, `moneda` ← `moneda_referencia`, `proveedor_sugerido_id`, `sku_libre`)

**No incluido (out of scope):** registrar uso del fantasma en `veces_solicitado` y `ultimo_visto_en`. Esos se actualizan al guardar la cot vía el flow existente del backend (suponiendo que ya lo hace; si no, se queda como follow-up).

### F3 — TotalsBar: Subtotal y Total grandes

**Problema:** Subtotal, IVA y Total están todos en `text-xs`. El subtotal — que es lo que más mira el comercial al armar la cot — se pierde visualmente.

**Solución:**
- `TotalsBar.tsx:177-203` rework tipográfico:
  - Subtotal: `text-2xl font-mono font-semibold text-slate-100`
  - IVA: `text-xs font-mono text-slate-400` (discreto, contextual)
  - Total: `text-2xl font-mono font-bold text-accent-glow`
  - Labels ("Subtotal", "IVA", "Total"): `text-[10px] uppercase tracking-wider text-slate-500`
- Layout: misma fila horizontal (no vertical), separación `gap-6` entre los 3 grupos, padding del container sube de `py-2` a `py-3` para acomodar el alto extra
- El chip "Util prom." se mantiene a la derecha; el chip de mix de monedas (por moneda nativa) se queda como está
- Mobile: el `flex-wrap` ya existente hace que en pantalla angosta los 3 importes salten a nueva línea

### F4 — Eliminar el modal "Pisar TC manualmente"

**Problema:** El input "TC" del header ya es editable directamente (línea `HeaderCotizacion.tsx:84-92`). El modal `ModalPisarTC` y el link admin "Pisar TC" en `TCMiniTable` son redundantes — duplican un input simple con UX adicional sin beneficio.

**Solución:**
- Eliminar `web/src/features/cotizador/components/ModalPisarTC.tsx`
- Quitar `<ModalPisarTC />` de `CotizadorPage.tsx:392`
- Quitar el botón admin "Pisar TC" de `TCMiniTable.tsx:88-97` (líneas con `esAdmin && (<button … cot:open-pisartc …>)`)
- Quitar la importación de `useIsAdmin` de `TCMiniTable.tsx` (ya no se usa)
- Quitar `ShieldAlert` de las importaciones de lucide-react en `TCMiniTable.tsx`
- El event `cot:open-pisartc` queda muerto; ningún dispatch ni listener lo referencia
- El usuario (cualquiera, no solo admin) ya puede editar el TC directamente en el input del header. La trazabilidad de quién lo cambió ya estaba ausente del modal también, así que no se pierde nada

**Riesgo cero:** este cambio simplemente elimina código muerto. El backend `/api/fx/override` (admin-only, pisa el TC del DÍA en la tabla `tipos_cambio_dia`) NO se toca — ese es para casos de outage de Banxico y sigue accesible desde otro lugar futuro (no del cotizador).

### F5 — Tabs encimados: corregir UI

**Problema:** Hay dos sets de tabs muy parecidos visualmente — `TabsCotizador.tsx` (Cotizador/Historial) y `CatalogoFiltros.tsx` (Productos/Servicios). Ambos usan `border-b border-slate-800` + `text-accent-glow border-accent-glow` para el activo. El espacio entre ellos es pequeño, dando sensación de "tabs anidados encimados".

**Solución:**
- `TabsCotizador.tsx`: subir contraste y peso visual — tabs del nivel superior con `py-2.5` (más altos), texto `text-sm font-semibold`, borde inferior del contenedor `border-b-2` (no `border-b`), fondo `bg-slate-900/40` para diferenciarlo del fondo de la página
- `CatalogoFiltros.tsx`: bajar contraste — tabs del sub-nivel con texto `text-[11px]` (más chico), padding `px-2.5 py-1`, sin borde inferior del contenedor (eliminar la `<div className="flex gap-1 border-b border-slate-800">`), usar fondo `bg-slate-950/40` con bordes redondeados para parecer "chips" en vez de tabs (clarifica que es sub-control del buscador, no navegación de página)
- Resultado: jerarquía visual clara — tabs primarios (página) altos, tabs secundarios (filtro de búsqueda) bajos como chips
- Margen entre `HeaderCotizacion` y la sección "Productos" se incrementa de `mt-2` a `mt-4`

## Archivos a tocar

**Crear:**
- `web/src/features/cotizador/hooks/useFantasmasSearch.ts` (~50 líneas)

**Modificar:**
- `web/src/features/cotizador/components/HeaderCotizacion.tsx` — agregar banner ámbar (F1)
- `web/src/features/cotizador/components/CatalogoFiltros.tsx` — agregar tab Fantasmas + chip style (F2 + F5)
- `web/src/features/cotizador/components/ProductSearch.tsx` — soportar `tipo === 'fantasma'`, render de resultados, click handler (F2)
- `web/src/features/cotizador/components/TotalsBar.tsx` — tipografía (F3)
- `web/src/features/cotizador/components/TCMiniTable.tsx` — quitar link admin "Pisar TC" + imports (F4)
- `web/src/features/cotizador/components/TabsCotizador.tsx` — contraste y peso (F5)
- `web/src/features/cotizador/pages/CotizadorPage.tsx` — quitar `<ModalPisarTC />` (F4)

**Eliminar:**
- `web/src/features/cotizador/components/ModalPisarTC.tsx` (F4)

**Sin cambios:**
- Backend (`/api/fantasmas/?q=` ya existe), `store.ts`, `calc.ts`, `serialize.ts`, `CartRow.tsx`, `RowExpanded.tsx`

## Riesgos y consideraciones

- **F2 (Fantasmas tab):** el endpoint devuelve hasta `page_size=100` items. Si una cuenta tiene más de 100 fantasmas activos, la búsqueda inicial sin query mostrará los más recientes. Aceptable — el usuario buscará por texto.
- **F2 (shape mismatch):** el `proveedor_sugerido_id` del fantasma puede apuntar a un proveedor que ya no existe (FK no aplicado en DB legacy). El backend ya tiene `_serialize_fantasma_row` que protege con try/except, así que llega `proveedor_sugerido_nombre: null` — manejarlo en el render.
- **F4 (modal eliminado):** si en el futuro Dasic pide UX adicional al "pisar TC" (auditoría, motivo, etc.), se reintroduce. Por ahora YAGNI.
- **F5 (tabs):** el cambio de jerarquía visual cambia un componente compartido (`TabsCotizador`). Verificar que no se use en otra ruta — un grep antes de tocarlo.

## Verificación manual

Después del build:

1. **F1:** abrir `/cotizador/nueva` sin elegir cliente, agregar un producto del catálogo. Aparece banner ámbar arriba del header. Elegir cliente → banner desaparece.
2. **F2:** crear y guardar una cotización con una fantasma "Sensor X". Abrir nueva cot, ir al tab "Fantasmas", escribir "sensor" → debería aparecer "Sensor X" en resultados. Click → entra al cart como fantasma.
3. **F3:** verificar que el subtotal y total en el TotalsBar son visualmente más grandes que el IVA. Resize ventana → en pantalla angosta los 3 importes saltan a líneas separadas.
4. **F4:** confirmar que `ModalPisarTC.tsx` no existe, que el link "Pisar TC" no aparece en el `TCMiniTable` para usuarios admin. Editar el TC del header directamente funciona como siempre.
5. **F5:** los tabs Cotizador/Historial se ven más altos y prominentes; los Productos/Servicios/Fantasmas se ven como chips compactos, claramente subordinados al buscador.
