# Cotización en Word editable — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generar la cotización como `.docx` editable (python-docx), descargable desde el historial, sin tocar el PDF.

**Architecture:** Un servicio puro `word_service.build_cotizacion_docx(...)` construye el `.docx` en memoria a partir de datos ya resueltos. Un endpoint `GET /api/ventas/{id}/word` reutiliza el mismo cálculo de totales que `/pdf` y devuelve el binario con headers de descarga. El frontend agrega un enlace "Word" junto al de "PDF".

**Tech Stack:** FastAPI + SQLAlchemy (Postgres) + **python-docx** (nuevo); React 18 + Vite + TS.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend `python3 -m py_compile <archivos>` (valida sintaxis; `python-docx` no está instalado localmente, el import real se valida en deploy); frontend `cd web && npm run build`. Sin migración.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-cotizacion-word-editable-design.md`.

---

## Fase 1 — Backend

### Task 1: Dependencia + servicio `word_service`

**Files:**
- Modify: `requirements.txt`
- Create: `app/services/word_service.py`

- [ ] **Step 1: Agregar la dependencia**

En `requirements.txt`, agregar una línea (junto a `fpdf2`/`openpyxl`):

```
python-docx
```

- [ ] **Step 2: Crear el servicio**

Crear `app/services/word_service.py` con:

```python
"""Genera la cotización como .docx editable (python-docx).

Servicio puro: recibe datos ya resueltos (sin DB ni request) y retorna los
bytes del .docx. Solo modo desglose (una fila por línea)."""
import io
from decimal import Decimal

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _fmt(simbolo: str, valor) -> str:
    return f"{simbolo} {Decimal(valor or 0):,.2f}"


def build_cotizacion_docx(
    *,
    orden,
    iva,
    total,
    simbolo: str,
    tipo_doc: str,
    fecha_str: str,
    vigencia_dias: int,
) -> bytes:
    doc = Document()

    # Encabezado
    h = doc.add_paragraph()
    r = h.add_run("DASIC Industrial")
    r.bold = True
    r.font.size = Pt(18)

    sub = doc.add_paragraph()
    sr = sub.add_run(f"{tipo_doc} · {orden.folio or ''}")
    sr.bold = True
    sr.font.size = Pt(12)

    meta = doc.add_paragraph(f"Fecha: {fecha_str}    Vigencia: {vigencia_dias} días")
    meta.runs[0].font.size = Pt(9)

    # Vendedor
    vend = orden.vendedor
    p = doc.add_paragraph()
    p.add_run("Atiende: ").bold = True
    p.add_run(vend.nombre if vend else "Equipo DASIC")
    if vend and getattr(vend, "email", None):
        p.add_run(f"  ·  {vend.email}")

    # Cliente
    cli = orden.cliente
    pc = doc.add_paragraph()
    pc.add_run("Cliente: ").bold = True
    pc.add_run(cli.nombre_empresa if cli else "—")
    extras = []
    if cli and getattr(cli, "rfc_tax_id", None):
        extras.append(f"RFC: {cli.rfc_tax_id}")
    if cli and getattr(cli, "contacto_nombre", None):
        extras.append(f"Contacto: {cli.contacto_nombre}")
    if cli and getattr(cli, "email", None):
        extras.append(cli.email)
    if cli and getattr(cli, "telefono", None):
        extras.append(cli.telefono)
    if extras:
        doc.add_paragraph("   ".join(extras)).runs[0].font.size = Pt(9)

    doc.add_paragraph("")

    # Tabla de líneas
    tabla = doc.add_table(rows=1, cols=6)
    tabla.style = "Table Grid"
    hdr = tabla.rows[0].cells
    for i, t in enumerate(["#", "SKU", "Descripción", "Cant.", "P. Unit", "Subtotal"]):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(t)
        run.bold = True
        run.font.size = Pt(9)

    for idx, d in enumerate(orden.detalles, start=1):
        prod = d.producto
        sku = d.sku_libre or ((prod.sku_comercial or prod.sku) if prod else None) or "—"
        desc = d.descripcion_libre or (prod.nombre if prod else None) or "Producto"
        row = tabla.add_row().cells
        row[0].text = str(idx)
        row[1].text = str(sku)

        dcell = row[2]
        dcell.text = ""
        dcell.paragraphs[0].add_run(desc).font.size = Pt(9)
        if d.mostrar_marca and d.marca:
            mr = dcell.add_paragraph().add_run(f"Marca: {d.marca}")
            mr.font.size = Pt(8)
        if d.clave_prod_serv or d.clave_unidad_sat:
            sr2 = dcell.add_paragraph().add_run(
                f"SAT: {d.clave_prod_serv or '—'} · Unidad: {d.clave_unidad_sat or '—'}"
            )
            sr2.font.size = Pt(8)
        if d.observaciones_linea:
            orun = dcell.add_paragraph().add_run(d.observaciones_linea)
            orun.italic = True
            orun.font.size = Pt(8)

        row[3].text = str(d.cantidad)
        row[4].text = _fmt(simbolo, d.precio_unitario)
        row[5].text = _fmt(simbolo, d.subtotal)

    # Totales
    doc.add_paragraph("")
    for etiqueta, val in (("Subtotal", orden.total), ("IVA", iva), ("Total", total)):
        pt = doc.add_paragraph()
        pt.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = pt.add_run(f"{etiqueta}: {_fmt(simbolo, val)}")
        if etiqueta == "Total":
            run.bold = True
            run.font.size = Pt(12)

    # Observaciones
    if orden.observaciones:
        doc.add_paragraph("")
        doc.add_paragraph().add_run("Observaciones:").bold = True
        doc.add_paragraph(orden.observaciones).runs[0].font.size = Pt(9)

    # Términos y condiciones
    if orden.terminos_condiciones:
        doc.add_paragraph("")
        doc.add_paragraph().add_run("Términos y condiciones:").bold = True
        doc.add_paragraph(orden.terminos_condiciones).runs[0].font.size = Pt(9)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/services/word_service.py`
Expected: sin salida (OK). (El import de `docx` no se ejecuta en py_compile; valida solo sintaxis.)

- [ ] **Step 4: Commit**

```bash
git add requirements.txt app/services/word_service.py
git commit -m "feat(word): servicio build_cotizacion_docx + dependencia python-docx (US-017)"
```

### Task 2: Endpoint `GET /api/ventas/{id}/word`

**Files:**
- Modify: `app/routers/ventas.py`

- [ ] **Step 1: Imports**

En `app/routers/ventas.py`, cambiar la línea:
```python
from fastapi import APIRouter, Depends, HTTPException, status
```
por:
```python
from fastapi import APIRouter, Depends, HTTPException, Response, status
```

Y agregar el import del servicio junto a los otros `from app.services...`:
```python
from app.services.word_service import build_cotizacion_docx
```

- [ ] **Step 2: Agregar el endpoint**

Inmediatamente después de la función `generar_pdf` (el endpoint `@router.get("/{id}/pdf", ...)`), agregar:

```python
@router.get("/{id}/word", dependencies=[Depends(allow_all_staff)])
def generar_word(id: int, db: Session = Depends(get_db)):
    """Genera la cotización como .docx editable (descarga). Reutiliza el mismo
    cálculo de totales que /pdf. No muta pdf_generado_at (eso es del PDF)."""
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == id).first()
    if not orden:
        raise HTTPException(404)

    iva = (orden.total * _iva_rate()).quantize(Decimal("0.01"))
    total = (orden.total + iva).quantize(Decimal("0.01"))
    es_cotizacion = orden.estatus == models.EstatusOrden.COTIZACION
    tipo_doc = "COTIZACION" if es_cotizacion else "NOTA DE VENTA"
    simbolo = _currency_symbol(orden.moneda)

    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    if orden.fecha_creacion:
        f = orden.fecha_creacion
        fecha_str = f"{f.day} de {meses_es[f.month - 1]} de {f.year}"
    else:
        fecha_str = ""
    vigencia_dias = (
        max((orden.fecha_vencimiento.date() - orden.fecha_creacion.date()).days, 0)
        if orden.fecha_vencimiento and orden.fecha_creacion
        else _quote_validity_days()
    )

    data = build_cotizacion_docx(
        orden=orden,
        iva=iva,
        total=total,
        simbolo=simbolo,
        tipo_doc=tipo_doc,
        fecha_str=fecha_str,
        vigencia_dias=vigencia_dias,
    )
    filename = f"cotizacion_{orden.folio or orden.id}.docx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

> Los helpers `_iva_rate`, `_currency_symbol`, `_quote_validity_days` ya existen en `ventas.py` (los usa `generar_pdf`).

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/routers/ventas.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/routers/ventas.py
git commit -m "feat(api): GET /api/ventas/{id}/word — descarga .docx de la cotización (US-017)"
```

---

## Fase 2 — Frontend

### Task 3: Enlace "Word" en `HistorialTab`

**Files:**
- Modify: `web/src/features/cotizador/components/HistorialTab.tsx`

- [ ] **Step 1: Agregar el enlace junto al de PDF**

En `HistorialTab.tsx`, localizar el `<a ... href={`/api/ventas/${o.id}/pdf`} ...>` (con `<FileText className="h-3 w-3" /> PDF`). Inmediatamente DESPUÉS de ese `</a>`, agregar:

```tsx
                    <a
                      href={`/api/ventas/${o.id}/word`} target="_blank" rel="noreferrer"
                      className="text-[11px] px-1.5 py-0.5 rounded border border-slate-700 hover:border-accent-glow text-slate-300 flex items-center gap-1"
                      title="Descargar Word"
                    ><FileText className="h-3 w-3" /> Word</a>
```

(Reusa el ícono `FileText` ya importado — no agregar imports.)

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/cotizador/components/HistorialTab.tsx
git commit -m "feat(cotizador): enlace Word junto a PDF en el historial (US-017)"
```

---

## Fase 3 — Build final + push

### Task 4: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — US-017 Word editable"
git push origin main
```

> Tras el deploy, Railway instala `python-docx` (nixpacks lee requirements.txt). Si el deploy falla por la dependencia, revisar el log de build de Railway.

---

## Notas de verificación manual (post-deploy, recomendado)

- En el cotizador → tab Historial → en una cotización, click "Word" → descarga `cotizacion_{folio}.docx`.
- Abrir el .docx en Word/Google Docs/LibreOffice → confirmar que es editable y contiene: encabezado con folio/fecha/vigencia, vendedor + correo, cliente (RFC/contacto), tabla de líneas con cantidades y precios (+ marca/SAT/observación donde aplique), Subtotal/IVA/Total, observaciones y términos.
- Confirmar que el botón "PDF" sigue funcionando igual (US-018).
- Probar una cotización en USD → el símbolo de moneda y los montos coinciden con el PDF.
