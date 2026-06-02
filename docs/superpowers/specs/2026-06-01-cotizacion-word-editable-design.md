# US-017 — Cotización en Word editable — Design

**Fecha:** 2026-06-01
**Alcance:** US-017 (generar la cotización como `.docx` editable, además del PDF). US-018 (mantener el PDF) ya está cumplido — no se toca el endpoint `/pdf`.

## Contexto actual (auditado)

- El "PDF" de cotización es `GET /api/ventas/{id}/pdf` (ventas.py:1548) → **HTMLResponse** imprimible (template `PDF_TEMPLATE_VENTA`). No es binario.
- El endpoint `/pdf` ya ensambla todo: `iva = orden.total * _iva_rate()`, `gran_total`, `tipo_doc` (COTIZACION/NOTA DE VENTA), `simbolo_moneda = _currency_symbol(orden.moneda)`, `fecha_str` (día de mes de año, en español), `vigencia_dias`. El vendedor sale de `orden.vendedor` (nombre + email); el cliente de `orden.cliente`.
- `DetalleOrden` por línea: `sku_libre`/`producto.sku`, `descripcion_libre`/`producto.nombre`, `cantidad`, `precio_unitario`, `subtotal`, `marca`, `mostrar_marca`, `clave_prod_serv`, `clave_unidad_sat`, `observaciones_linea`.
- `requirements.txt` tiene `fpdf2` y `openpyxl`, **no** `python-docx`.
- El frontend enlaza al PDF en `HistorialTab.tsx:263` (`<a href="/api/ventas/{id}/pdf" target="_blank">PDF</a>`).

## Decisión de producto (acordada)

**`.docx` real con `python-docx`** (no HTML-como-.doc): abre limpio en Word/Google Docs/LibreOffice sin advertencias de formato. python-docx es pura-Python e instala bien en Railway (nixpacks).

## Arquitectura

### 1. Dependencia

Agregar `python-docx` a `requirements.txt`. Import en el servicio como `from docx import Document`.

### 2. Servicio `app/services/word_service.py`

Función única `build_cotizacion_docx(*, orden, iva, total, simbolo, tipo_doc, fecha_str, vigencia_dias) -> bytes`:
- Crea `Document()`, arma el contenido y lo guarda a un `io.BytesIO()`, retorna `buf.getvalue()`.
- **Encabezado:** título "DASIC Industrial" + `tipo_doc`; línea con folio, fecha (`fecha_str`), y "Vigencia: N días".
- **Vendedor:** "Atiende: {orden.vendedor.nombre}" + email si existe (fallback "Equipo DASIC").
- **Cliente:** "Cliente: {cliente.nombre_empresa}", y si existen: RFC (`rfc_tax_id`), contacto (`contacto_nombre`), email/teléfono.
- **Tabla de líneas** (encabezados: `#`, `SKU`, `Descripción`, `Cant.`, `P. Unit`, `Subtotal`): una fila por `DetalleOrden`. La celda Descripción incluye:
  - la descripción (`descripcion_libre` or `producto.nombre`),
  - si `mostrar_marca` y hay marca → línea "Marca: {marca}",
  - si hay SAT → línea "SAT: {clave_prod_serv} · Unidad: {clave_unidad_sat}",
  - si hay `observaciones_linea` → esa nota.
  - Precios formateados `{simbolo} {valor:,.2f}`.
- **Totales** (alineados a la derecha): Subtotal (`orden.total`), IVA (`iva`), **Total** (`total`) con `simbolo` y etiqueta de moneda.
- **Observaciones generales:** `orden.observaciones` si existe.
- **Términos y condiciones:** `orden.terminos_condiciones` si existe.
- Solo modo **desglose** (no "concepto unificado").
- El servicio es puro (sin DB ni request): recibe datos ya resueltos → testeable y aislado.

### 3. Endpoint `GET /api/ventas/{id}/word`

En `app/routers/ventas.py` (junto a `/pdf`, `dependencies=[Depends(allow_all_staff)]`):
- Carga `orden` (404 si no existe).
- Reusa el cálculo de `/pdf`: `iva = (orden.total * _iva_rate()).quantize(...)`, `total = orden.total + iva`, `tipo_doc`, `simbolo_moneda`, `fecha_str`, `vigencia_dias` (misma lógica que `generar_pdf`).
- `data = build_cotizacion_docx(...)`.
- Retorna `Response(content=data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="cotizacion_{orden.folio or orden.id}.docx"'})`.
- No muta `pdf_generado_at` (eso es del PDF).

### 4. Frontend

- En `HistorialTab.tsx`, junto al enlace "PDF" (línea ~263), agregar un enlace análogo "Word":
  `<a href={`/api/ventas/${o.id}/word`} target="_blank" rel="noreferrer" title="Descargar Word">Word</a>` (mismo estilo que el de PDF, con un ícono apropiado). Es descarga directa (Content-Disposition: attachment) — sin hook ni estado.

### 5. Cobertura de US-017

| Criterio | Cómo se cubre |
|----------|---------------|
| Botón "Generar Word" | Enlace en HistorialTab. |
| Cliente, productos, cantidades, precios, observaciones, condiciones | Todo en el `.docx` (encabezado, cliente, tabla, totales, observaciones, T&C). |
| Documento editable | `.docx` nativo. |
| No sustituye al PDF | El `/pdf` queda intacto (US-018). |

## Fuera de alcance (YAGNI)

- Logo/imágenes embebidas (texto y tabla limpios).
- Modo "concepto unificado" en el Word (solo desglose).
- Plantillas Word personalizables por usuario.
- Word para remisión u OC (esto es solo cotización).
- QR (es del PDF).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`. `python-docx` no está instalado en el entorno local (sin venv) → `py_compile` valida sintaxis; el import real se valida en deploy. El servicio se diseña puro para poder probarse manualmente si se levanta un venv.
- **Nueva dependencia:** `python-docx` es pura-Python, sin libs de sistema → bajo riesgo de build en Railway.
- **Sin migración** ni cambios de esquema.
- **Reúso de cálculo:** los totales se computan igual que en `/pdf` para que Word y PDF coincidan.
