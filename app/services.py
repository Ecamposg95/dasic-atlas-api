from fpdf import FPDF
from datetime import datetime
import os

# Colores Corporativos (Aproximados de tu imagen)
COLOR_AZUL_OSCURO = (31, 78, 121) # Header Azul
COLOR_GRIS_TABLA = (240, 240, 240) # Filas pares
COLOR_AZUL_TABLA = (23, 55, 94) # Header Tabla

class PDFDasic(FPDF):
    def header(self):
        # Logo (Asegurate de tener logo.png en static/img/)
        if os.path.exists("static/img/logo.png"):
            self.image("static/img/logo.png", 10, 8, 33)
        
        # Título Empresa
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, "Development of Automation Systems and Industrial Control SA de CV", 0, 1, 'R')
        
        # Dirección
        self.set_font('Arial', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Ave Iztaccíhuatl MZ 39 LT 1, Col. Adolfo Ruiz Cortines, Del. Coyoacan, CP. 04630", 0, 1, 'R')
        
        # Línea Azul separadora
        self.set_draw_color(*COLOR_AZUL_OSCURO)
        self.set_line_width(1)
        self.line(10, 25, 200, 25)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_cotizacion(folio, fecha, cliente, items, total, moneda, tc_usado=1.0):
    output_dir = "generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    pdf = PDFDasic()
    pdf.add_page()
    
    # --- BLOQUE DE INFORMACIÓN (Fecha y Folio) ---
    pdf.set_y(30)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*COLOR_AZUL_OSCURO)
    pdf.cell(15, 6, "Fecha:", 0, 0)
    pdf.set_text_color(0)
    pdf.set_font("Arial", "U", 10) # Subrayado
    pdf.cell(40, 6, fecha, 0, 0)
    
    pdf.set_x(130)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(*COLOR_AZUL_OSCURO)
    pdf.cell(40, 6, "COTIZACION:", 0, 0, 'R')
    pdf.set_text_color(0)
    pdf.cell(30, 6, folio, 0, 1, 'R')
    
    pdf.ln(5)
    
    # --- DATOS DEL CLIENTE ---
    pdf.set_x(100) # Alinear a la derecha visualmente
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 5, "Nombre:", 0, 0, 'R')
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 5, cliente.nombre, 0, 1, 'R')
    
    pdf.set_x(100)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 5, "Compañía:", 0, 0, 'R')
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 5, cliente.compania, 0, 1, 'R')
    
    pdf.set_x(100)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 5, "E-mail:", 0, 0, 'R')
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 5, cliente.email, 0, 1, 'R')

    pdf.ln(10)

    # --- TABLA DE PRODUCTOS ---
    # Encabezados
    pdf.set_fill_color(*COLOR_AZUL_OSCURO)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 8)
    
    cols = [10, 30, 85, 15, 25, 25] # Anchos de columnas
    headers = ["Item", "Catalog #", "Description", "Qty", "Unit Price", "SubTotal"]
    
    for i, h in enumerate(headers):
        align = 'C' if i != 2 else 'L' # Descripción a la izquierda
        pdf.cell(cols[i], 8, h, 1, 0, align, True)
    pdf.ln()

    # Filas
    pdf.set_text_color(0)
    pdf.set_font("Arial", "", 8)
    fill = False
    
    total_neto = 0
    
    for idx, item in enumerate(items):
        # Fondo alternado gris
        pdf.set_fill_color(*COLOR_GRIS_TABLA)
        
        # Altura dinámica basada en la descripción
        # Calculamos cuántas líneas ocupará la descripción
        pdf.set_font("Arial", "", 8)
        num_lines = len(pdf.multi_cell(cols[2], 5, item['desc'], split_only=True))
        h = max(10, num_lines * 5)
        
        # Verificar salto de página
        if pdf.get_y() + h > 260:
            pdf.add_page()
        
        # Dibujar celdas
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        pdf.cell(cols[0], h, str(idx + 1), 1, 0, 'C', fill)
        pdf.cell(cols[1], h, item['catalogo'], 1, 0, 'C', fill)
        
        # Descripción Multi-linea
        x_desc = pdf.get_x()
        y_desc = pdf.get_y()
        pdf.multi_cell(cols[2], 5, item['desc'] + f"\n(T.E: {item['entrega']})", 1, 'L', fill)
        pdf.set_xy(x_desc + cols[2], y_desc) # Regresar cursor
        
        pdf.cell(cols[3], h, str(item['cant']), 1, 0, 'C', fill)
        pdf.cell(cols[4], h, f"${item['precio']:,.2f}", 1, 0, 'R', fill)
        pdf.cell(cols[5], h, f"${item['sub']:,.2f}", 1, 1, 'R', fill)
        
        # --- IMAGEN DEL PRODUCTO (SI EXISTE) ---
        # Si el usuario mandó URL, intentamos dibujarla abajo de la descripción
        if item.get('imagen_url') and item['imagen_url'].startswith('http'):
            try:
                # Insertar imagen pequeña debajo de la descripción o en una nueva línea
                # Por ahora, para replicar tu imagen, la pondremos debajo si hay espacio
                # Ojo: FPDF2 necesita descargarla primero o usar un path local. 
                # Para MVP asumimos que 'imagen_url' es accesible.
                pdf.image(item['imagen_url'], x=x_start + 15, y=y_start + h + 2, w=30)
                pdf.ln(35) # Espacio extra para la imagen
            except:
                pass # Si falla la imagen, no rompemos el PDF
        
        total_neto += item['sub']

    # --- TOTALES ---
    pdf.ln(2)
    pdf.set_x(140)
    pdf.set_fill_color(*COLOR_AZUL_OSCURO)
    pdf.set_text_color(255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, f"SUBTOTAL {moneda}", 1, 0, 'R', True)
    
    pdf.set_text_color(0)
    pdf.cell(25, 8, f"${total_neto:,.2f}", 1, 1, 'R')

    # --- CONDICIONES COMERCIALES (Texto fijo basado en tu imagen) ---
    pdf.ln(10)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, "CONDICIONES COMERCIALES:", 0, 1)
    
    pdf.set_font("Arial", "", 7)
    condiciones = [
        "Agregar el IVA Correspondiente.",
        "Precios expresados en MONEDA NACIONAL." if moneda == 'MXN' else "Precios expresados en DOLARES AMERICANOS.",
        "Tiempo de entrega S.P.V (Salvo Previa Venta).",
        "En caso de cancelación se cobrará el 25% del monto total.",
        "Vigencia de esta cotización: 5 DÍAS A PARTIR DE LA FECHA DE EMISIÓN."
    ]
    
    for cond in condiciones:
        pdf.cell(5, 4, "-", 0, 0)
        pdf.cell(0, 4, cond, 0, 1)

    filename = f"{output_dir}/COT-{folio}.pdf"
    pdf.output(filename)
    return filename