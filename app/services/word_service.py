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
