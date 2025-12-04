from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from .. import database, models, schemas, auth, services

router = APIRouter()

@router.post("/cotizar")
def crear_cotizacion(
    datos: schemas.CotizacionCreate, 
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Lógica simplificada para probar
    if datos.cliente_id:
        cliente = db.query(models.Cliente).filter(models.Cliente.id == datos.cliente_id).first()
    else:
        cliente = models.Cliente(nombre=datos.nuevo_cliente_nombre, compania="S/C", email="N/A")
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

    total_doc = 0.0
    # Aquí iría tu bucle de items, cálculo de precios y guardado
    # Por ahora solo devolvemos un dummy
    
    folio_str = f"C-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Simulación de generación de PDF
    pdf_path = services.generar_pdf_cotizacion(folio_str, str(datetime.now()), cliente, [], 0.0, datos.moneda_salida)

    return {"folio": folio_str, "pdf_url": pdf_path, "mensaje": "Cotización creada (Simulada)"}