# Bugs funcionales — agosto 2026

> Cada hallazgo tiene ruta de reproducción verificada leyendo el código. Contexto de caché: `web/src/lib/queryClient.ts` fija `staleTime: 30_000` y `refetchOnWindowFocus: false` — una query que no se invalida **no se refresca sola**.

## Top 15 por severidad

| # | Sev | Dónde | Qué pasa |
|---|---|---|---|
| ~~1~~ | ~~CRÍTICO~~ | `remisiones/hooks/useRemisiones.ts` | ✅ **Corregido** (Ola 1). Las mutaciones no invalidaban `['remision-borrador']` → el editor precargaba pendientes pre-emisión → sobre-entrega o 400 |
| ~~2~~ | ~~CRÍTICO~~ | ídem | ✅ **Corregido** (Ola 1). Tampoco invalidaban `['ventas','avance-entrega']` → el avance de la venta nunca se refrescaba tras emitir |
| ~~3~~ | ~~ALTO~~ | `cotizador/hooks/useSugerirOC.ts` | ✅ **Corregido** (Ola 1). Invalidaba `['compras']`, key inexistente; la real es `['ordenesCompra']` → las OC generadas no aparecían |
| ~~4~~ | ~~ALTO~~ | `compras/hooks/useRecibirParcial.ts` | ✅ **Corregido** (Ola 1). Recibir OC mueve stock y no invalidaba `['productos']`/`['cardex']` |
| ~~5~~ | ~~ALTO~~ | `fx/pages/FxPage.tsx` | ✅ **Corregido** (Ola 1). Override/refresh de TC no invalidaba `['fx','usd-mxn']` → el cotizador sembraba el TC viejo |
| ~~6~~ | ~~ALTO~~ | `components/layout/Sidebar.tsx` | ✅ **Corregido** (Ola 1). `modulos_visibles` se ignoraba → menús que el backend rechaza con 403. Los ítems sin clasificar en la matriz siguen visibles a propósito: cubre 11 de 21 módulos |
| 7 | **PARCIAL** | `cotizador/pages/CotizadorPage.tsx:210-212` | ✅ Ya no colapsa las filas expandidas al guardar (`store.ts` conserva `expandedUids` al re-hidratar la misma orden). ⚠️ **Sigue abierto**: un refetch que aterrice mientras se teclea pisa la edición en vuelo. Requiere marcar el estado como sucio y decidir qué gana — el servidor o lo que el usuario está escribiendo—, que es decisión de producto |
| ~~8~~ | ~~ALTO~~ | `clientes/hooks/useEmpresaDetalle.ts` | ✅ **Corregido** (Ola 1). Registrar pago no invalidaba `['empresa',id,'resumen']` → saldo viejo en la pestaña contigua |
| ~~9~~ | ~~ALTO~~ | `cxc/hooks/usePagoDistribuido.ts` | ✅ **Corregido** (Ola 1). Espejo del anterior. Ambos usan ahora el helper compartido `lib/cobranza-cache.ts`, porque el bug era la enumeración duplicada de claves |
| ~~10~~ | ~~ALTO~~ | `remisiones/pages/RemisionesPage.tsx` | ✅ **Corregido** (Ola 1). Recibir/Cancelar/Crear cotización eran visibles para roles que el backend rechaza. Ahora leen los flags `can_*` que `/api/auth/me` ya entregaba |
| ~~11~~ | ~~ALTO~~ | `servicios/pages/ServiciosPage.tsx` | ✅ **Corregido** (Ola 1). Comparaciones de rol a mano sin `'superadmin'`. Sustituidas por los helpers centrales, espejo de las guardas del router |
| ~~12~~ | ~~ALTO~~ | `borradores/pages/BorradoresPage.tsx` | ✅ **Corregido** (Ola 1). Dos query keys para el mismo endpoint → descartar en una pantalla dejaba fantasmas en la otra. Se invalidan ambas; unificar los dos hooks queda pendiente |
| ~~13~~ | ~~MEDIO~~ | `cotizador/store.ts` + `routers/ventas.py` | ✅ **Corregido** (Ola 1). `max: 0` al re-hidratar → toda cotización guardada mostraba "Sin stock · OC". La causa estaba en el backend: `/detalle-json` no exponía `stock_actual` |
| ~~14~~ | ~~MEDIO~~ | `components/document/DocumentRow.tsx` | ✅ **Corregido** (Ola 1). El input de cantidad se autocorregía en cada tecla y no se podía vaciar para reteclear. Lógica extraída a `useQtyDraft` (compartida por tabla y tarjeta, donde estaba duplicada) con 12 pruebas |
| ~~15~~ | ~~MEDIO~~ | `cotizador/components/HeaderCotizacion.tsx`, `fx/pages/FxPage.tsx` | ✅ **Corregido** (Ola 1). `toISOString()` usaba UTC: tras las 18:00 CDMX los documentos nacían fechados un día adelante. Helper `lib/fechas.ts` con 9 pruebas; la suite fija `TZ=America/Mexico_City` para que sean falsificables en CI |

~~**Bonus trivial:** `seguimiento/types.ts:28` — el toast de convertir a venta imprime `undefined`.~~ ✅ **Corregido** (Ola 1): el tipo declaraba `{id, folio_venta}` y el backend devuelve `{mensaje, nuevo_folio}`.

## Invalidación de caché — mapa completo

Además de los del top: ~~`useCrearCotizacionDesde` crea una orden y solo invalida remisiones~~ (✅ corregido junto con #1 y #2, igual que las invalidaciones de `['productos']`/`['cardex']` al emitir y cancelar, que sí mueven inventario); ✅ **Corregidos** (P3), con dos precisiones sobre el reporte. De los tres flujos de `SeguimientoPage` **solo dos** tienen efectos: `convertir` consume las reservas a SALIDA y crea el cargo de cobranza, y `cancelar` libera reservas — **`recotizar` no toca ni stock ni cobranza**, así que su invalidación ya era correcta. Los ajustes de inventario y la importación masiva ya invalidan `['cardex']`. Pendiente: las mutaciones de CRM y `['empresa',id,'deals']`.

✅ **Corregido, y el diagnóstico era otro.** Es cierto que nadie invalida `['dashboard']`, pero con `refetchOnMount` por defecto el dashboard **sí** se refresca al navegar a él: el máximo desfase al entrar era su `staleTime`. El fallo real estaba en el otro lado — es la pantalla que la gente **deja abierta**, y el default global apaga `refetchOnWindowFocus` (correcto en pantallas de edición, donde un refetch pisaría lo que se captura, pero aquí no hay nada que pisar). Sus 6 consultas lo activan ahora. Se prefirió eso a salpicar invalidaciones en 20 sitios, que es justo el patrón que se desincroniza.

## Manejo de errores

~~Sin `onError` ni feedback~~ ✅ **Corregido, y de los cuatro reportados solo dos eran reales.** Eliminar contacto y borrar nota no tenían `onError`: ya lo tienen, y el borrado de nota ahora **confirma** (era el único borrado del sistema que no preguntaba, frente a 43 sitios que sí). **Activo y planta ya estaban resueltos:** su `onError` con toast vive en el hook `useInstalaciones.ts`, no en el componente que revisó la auditoría — el 409 "la planta tiene activos" nunca se perdió.

~~**`Layout.tsx:35-40`**~~ ✅ **Corregido.** Cualquier fallo de `/api/auth/me` expulsaba al login, no solo el 401. Ahora solo 401 y 403 sacan al usuario; lo transitorio se reintenta 3 veces con espera creciente y, si no cede, se muestra una pantalla con "Reintentar" en vez de echarlo. **Matiz sobre el reporte original:** el efecto solo corre con `user === null` —al recargar o entrar por enlace directo—, así que no había pérdida de trabajo en curso; el daño real era aterrizar en el login en vez de en la ruta pedida.

~~`ReportesPage.tsx:292-294`~~ ✅ **Corregido.** Hacía `window.location.href` **durante el render** (efecto secundario en fase de render, que React puede ejecutar dos veces) y recargaba la SPA entera; ahora usa `<Navigate>`.

✅ **Hallazgo adicional, no auditado:** los **47** sitios que redirigen a `/spa/login` resolvían a una ruta **hija de `/spa`**, cuyo elemento es el `Layout` protegido: el login se dibujaba **dentro del shell autenticado** —sidebar, header y footer alrededor del formulario— y disparaba la verificación de sesión del propio Layout, que al recibir otro 401 navegaba a `/`. Se movió al nivel superior, donde se dibuja limpio y sin rebote, y se retiró la hija para no dejar dos rutas compitiendo por el mismo path.

🔵 **En curso — estado de error por página.** Se creó `components/ui/query-error.tsx`: dos formas (bloque suelto y `<tr>` con `asRow`, porque los listados renderizan dentro de un `<tbody>` donde no cabe un `<div>`), y trata el **403 aparte** —lo presenta como falta de acceso y sin botón de reintentar, porque no es un fallo sino una respuesta—. La rama de error va siempre antes que la de vacío: confundir "roto" con "vacío" es el defecto que corrige.

**Medición corregida.** El conteo que se venía citando ("14 de 35") salía de buscar `isError`, y por eso no veía las páginas con manejo propio. El reparto real hoy es: **13 con la primitiva**, **6 con banner propio** (login, salud, reportes, detalle de deal, seguimiento y usuarios de plataforma — funcionan, solo no están unificadas) y **16 sin nada**, una de ellas código muerto (`CrearRemisionPage`, sin ruta en el router).

## Estado obsoleto y carreras

El caso grave es el cotizador (#7 del top). Menores: efectos con `[]` que no reaccionan a cambios de query param en `CotizadorPage.tsx:230-241` (navegar de `?cliente=5` a `?cliente=9` no re-precarga) y `RemisionesPage.tsx:466-478` (un segundo `?ver=` no abre el detalle). El import de JSON del cotizador (`CotizadorPage.tsx:100-163`) sigue agregando líneas al store aunque navegues fuera.

Bien resueltos: `useMoveDeal` (cancelQueries + snapshot + rollback) y la guarda contra doble POST de `useGuardarCotizacion`.

## Validación cliente vs servidor

`GastoFormModal.tsx:34-42` no limita la categoría a 80 caracteres (el backend sí) → 422 con mensaje crudo de Pydantic. `AjusteStockModal.tsx:61-64` valida motivo no vacío donde el backend puede exigir 3 caracteres, y su mensaje de 403 menciona un rol equivocado.

## Navegación

✅ **Corregido.** `SeguimientoPage` ya siembra su búsqueda desde `?folio=` y `?orden=`, así que el enlace de `DealCard` y el "Guardar e ir a Seguimiento" del cotizador abren filtrados en vez del historial completo. `TotalsBar` navega del lado del cliente a la ruta canónica `/spa/seguimiento` —sus tres salidas recargaban la SPA entera— y la ruta legacy `/seguimiento` pasó a usar `RedirectConQuery`, el helper que ya existía en el router, para no descartar el query string. ✅ El "Cancelar" ya confirma también al editar una cotización existente — antes salía sin preguntar y los cambios sin guardar se perdían en silencio. Usa el mismo criterio que el aviso de recarga del navegador: hay algo que perder si el carrito tiene líneas.

## Permisos: UI vs matriz del backend

Falsos positivos (se muestra y el backend rechaza): menú completo para Ventas y Operativo (#6), acciones de remisión (#10).

~~Falsos negativos~~ ✅ **Corregidos** (Ola 1). Servicios (#11) e Inventario. En inventario el hallazgo real difería del reportado: la columna de costo desalineaba **en ambos sentidos** —el backend excluía a `SUPERADMIN` de ver costos, porque `RolUsuario.ADMIN` es alias de `ADMINISTRADOR` y no un tier que lo incluya, mientras la UI se la escondía a gerencia— y el botón de **ajustar stock no tenía gateo alguno**, así que ventas y operativo lo veían y recibían 403. Corregidos los tres puntos, backend incluido.

**Contradicción de la propia matriz:** `permissions.py:249-257` declara el módulo `compras` visible para Ventas y Operativo, pero los 11 endpoints de compras exigen admin o gerencia. O se alinea la matriz, o se alinean los endpoints.

## Lo que se verificó y está limpio

`lib/calc.ts` (defensivo en conversiones, banda de plausibilidad del TC, redondeo por línea antes de sumar) · protección contra doble submit en todos los formularios · todos los literales `/spa/...` del código existen en el router · los decimales llegan como número, no como string.

## Auditoría de noviembre 2026

Revisión completa de backend y frontend el 2026-11-24. Regresiones en `tests/test_auditoria_2026_11.py` y `web/src/features/cotizador/lib/calc.test.ts`.

### Corregido

| Dónde | Qué pasaba |
|---|---|
| `routers/ventas.py::_generar_folio` | Convertir una cotización liberaba su número: la siguiente cotización repetía folio y su conversión respondía 500. El consecutivo del mes ahora es uno para `C-` y `V-` |
| `services/auto_oc_service.py` | "Sugerir OC" y "Generar OC" respondían 500 siempre que había algo que pedir (`Decimal × float`) |
| `security/jwt.py`, `routers/auth.py` | Un usuario desactivado seguía usando la API y podía iniciar sesión; solo `/api/auth/me` lo rechazaba |
| `routers/clientes.py` (`registrar-pago`), `clientes/hooks/useEmpresaDetalle.ts` | El pago desde "Estado de cuenta" bajaba el saldo pero dejaba los cargos como pendientes en CxC, antigüedad y vencimientos. Ahora reparte FIFO como `pago-distribuido` |
| `routers/ventas.py::crear_orden` | `?tipo_orden=pagada` o `cancelada` sacaba stock sin generar cargo. Solo se acepta `cotizacion` o `pendiente` |
| `routers/ventas.py::crear_orden` | Las fechas capturadas en una cotización nueva se ignoraban en el primer guardado |
| `routers/crm.py` (`PATCH /deals/{id}`) | Cambiar la etapa desde el formulario no cerraba el deal ni dejaba rastro; solo `/move` lo hacía |
| `routers/compras.py` (recepción) | Sin bloqueo sobre la OC: dos recepciones simultáneas podían dar entrada dos veces |
| `routers/fantasmas.py` | Vaciar proveedor, marca, claves SAT o notas decía "Actualizado" y no cambiaba nada |
| `db/seeds.py::seed_super_admin` | La contraseña inicial de `admin@dasic.mx` estaba escrita en el código. Ahora sale de `INITIAL_ADMIN_PASSWORD` o se genera y se registra una vez en el log. **La anterior sigue en el historial de git: hay que cambiarla en toda instancia donde no se haya cambiado** |
| `cotizador/components/EditLineModal.tsx` | "Guardar y actualizar catálogo" pisaba el SKU interno del producto con el SKU comercial. "Reemplazar producto" conservaba el proveedor y la marca del producto anterior |
| `inventario/components/ProductoFormModal.tsx` | Editar un producto reimponía el stock que el modal vio al abrir, revirtiendo movimientos ocurridos mientras tanto |
| `cotizador/lib/calc.ts` | El preview podía quedar un centavo abajo del total guardado en empates de medio centavo |
| `lib/api.ts`, `LoginPage.tsx`, `lib/queryClient.ts` | El 409 de cotización ya enviada mostraba JSON crudo; la pantalla de suspensión se quedaba pegada tras un login correcto; las consultas reintentaban ante 423 |
| `contactos/pages/ContactosPage.tsx`, `crm/pages/DealDetallePage.tsx` | "Nuevo contacto" reabría con los datos del anterior; registrar una actividad borraba lo escrito sin guardar en el resumen del deal |
| `routers/superadmin.py` | El enlace a productos de la auditoría apuntaba a una ruta inexistente |

### Abierto — requiere decisión

| Sev | Dónde | Qué pasa |
|---|---|---|
| ALTO | `routers/ventas.py::convertir_cotizacion` | El stock se descuenta desde las reservas, no desde las líneas. Una recotización (V2) no tiene reservas: al convertirla se genera el cargo y **no sale stock**, y la original conserva su reserva. Falta decidir si recotizar traslada la reserva o cancela el origen |
| ALTO | `routers/ventas.py` (detalle-json, pdf, word, versiones, eventos, recotizar, enviar-correo, whatsapp-log, ia-resumen, sugerir-oc, generar-oc) | Solo exigen ser staff: Ventas ve y recotiza cotizaciones ajenas, Operativo lee costos y márgenes, y ambos pueden generar OC. La lectura compartida entre vendedores está documentada como deliberada; lo demás no |
| ALTO | `services/cuentas_por_cobrar.py`, `models/finance.py` | Las ventas en USD suman al saldo, a la antigüedad y al resumen como si fueran pesos (la transacción no guarda moneda). Igual en el saldo de proveedores |
| MEDIO | `routers/compras.py:698` | Crear una OC recibida desde cotización (`afecta_stock`) escribe en el catálogo un costo ya convertido a la moneda de la cotización sin cambiar `moneda_compra`. Hoy solo alcanzable por API |
| MEDIO | `domains/remisiones/service.py:245` | El control de sobre-entrega compara línea por línea: dos líneas del mismo renglón de la orden lo rebasan |
| MEDIO | `services/auto_oc_service.py::generar_ocs` | Suma las líneas fantasma al total de la OC sin crearles detalle, mezcla MXN y USD en un total, y `detalles_compra.cantidad` es entero (trunca cantidades fraccionarias) |
| MEDIO | `domains/remisiones/service.py:375` | La cotización creada desde una remisión usa la serie `C-` sola y puede repetir el número de una cotización ya convertida |
| MEDIO | `crm/pages/CrmKanbanPage.tsx`, `DealFormModal.tsx` | La lista de responsables sale de `/api/usuarios/`, que es solo para administradores: el resto de los roles ve "Sin asignar" |
| MEDIO | `remisiones/pages/RemisionEditorPage.tsx` | Volver a "Remisiones" desde un borrador conserva ese borrador en el editor (sin verificar en navegador) |
| BAJO | varios | Enlaces a PDF/Word/CSV muestran JSON crudo bajo suspensión; "Hasta" en remisiones excluye el día elegido; etiqueta de IVA en la OC impresa ignora el override; montos negativos aceptados en `compras/registrar-entrada` y `registrar-pago`; claves de caché sin invalidar (`clientes-count`, `precios-comparar-q`, `marcas`, `compras-proveedores`); no hay ESLint configurado; ninguna ruta de la SPA tiene guarda por rol (el backend sí rechaza) |
