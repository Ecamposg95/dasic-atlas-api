from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import database, models, schemas
import csv
import codecs
import io

router = APIRouter()

# --- READ: Listar Productos (Con Búsqueda Opcional) ---
@router.get("/", response_model=List[schemas.ProductoCreate]) 
def listar_productos(
    q: Optional[str] = Query(None, description="Búsqueda por catálogo, descripción o marca"),
    skip: int = 0, 
    limit: int = 1000, 
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Producto)
    
    if q:
        search = f"%{q}%"
        query = query.filter(
            (models.Producto.numero_catalogo.ilike(search)) |
            (models.Producto.descripcion.ilike(search)) |
            (models.Producto.marca.ilike(search))
        )
    
    return query.offset(skip).limit(limit).all()

# --- READ: Obtener un solo producto ---
@router.get("/{id}", response_model=schemas.ProductoCreate)
def obtener_producto(id: int, db: Session = Depends(database.get_db)):
    prod = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod

# --- CREATE: Crear Producto Manual ---
@router.post("/")
def crear_producto(prod: schemas.ProductoCreate, db: Session = Depends(database.get_db)):
    # 1. Validar duplicados por catálogo
    if db.query(models.Producto).filter(models.Producto.numero_catalogo == prod.numero_catalogo).first():
        raise HTTPException(status_code=400, detail=f"El catálogo '{prod.numero_catalogo}' ya existe.")

    # 2. Crear instancia
    nuevo = models.Producto(
        numero_catalogo=prod.numero_catalogo,
        descripcion=prod.descripcion,
        marca=prod.marca,
        costo_proveedor=prod.costo_proveedor,
        moneda_compra=prod.moneda_compra,
        tiempo_entrega=prod.tiempo_entrega,
        stock_actual=prod.stock_actual,
        imagen_url=prod.imagen_url
    )
    
    # 3. Guardar
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# --- UPDATE: Editar Producto ---
@router.put("/{id}")
def actualizar_producto(id: int, prod: schemas.ProductoCreate, db: Session = Depends(database.get_db)):
    existente = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not existente:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Actualizar campos
    existente.numero_catalogo = prod.numero_catalogo
    existente.descripcion = prod.descripcion
    existente.marca = prod.marca
    existente.costo_proveedor = prod.costo_proveedor
    existente.moneda_compra = prod.moneda_compra
    existente.tiempo_entrega = prod.tiempo_entrega
    existente.stock_actual = prod.stock_actual
    existente.imagen_url = prod.imagen_url
    
    db.commit()
    db.refresh(existente)
    return {"msg": "Producto actualizado correctamente", "producto": existente}

# --- DELETE: Eliminar Producto ---
@router.delete("/{id}")
def eliminar_producto(id: int, db: Session = Depends(database.get_db)):
    prod = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Validar si está en cotizaciones (Integridad Referencial)
    # Si tienes activado cascade delete en SQL esto no es necesario, pero es buena práctica
    if db.query(models.CotizacionDetalle).filter(models.CotizacionDetalle.producto_id == id).first():
        raise HTTPException(status_code=400, detail="No se puede eliminar: El producto está en cotizaciones activas.")

    db.delete(prod)
    db.commit()
    return {"msg": "Producto eliminado"}

# --- EXTRAS: CARGA MASIVA INTELIGENTE ---
@router.post("/upload-csv")
async def cargar_inventario_csv(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    """
    Procesa archivos CSV de Inventario.
    Soporta columnas: 'Catalog #', 'Nombre Catalogo', 'Description', 'Unit Price Prov', etc.
    """
    
    # Leer contenido y decodificar
    content = await file.read()
    decoded = content.decode('utf-8-sig') # utf-8-sig maneja el BOM de Excel
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    nuevos = 0
    actualizados = 0
    errores = 0

    for row in csv_reader:
        try:
            # 1. Normalizar Keys (Quitar espacios extra y BOMs raros)
            row = {k.strip(): v for k, v in row.items() if k}
            
            # 2. Mapeo Flexible de Columnas (Para soportar tus varios formatos de Excel)
            catalogo = row.get('Catalog #') or row.get('Nombre Catalogo') or row.get('Numero de Parte')
            if not catalogo: continue # Saltar fila vacía

            descripcion = row.get('Description') or row.get('Descripción') or "Sin descripción"
            marca = row.get('MARCA') or row.get('Marca') or "Genérico"
            
            # Precio (Limpiar símbolos $ y ,)
            precio_raw = row.get('Unit Price Prov') or row.get('Precio') or row.get('Costo') or "0"
            try:
                costo = float(str(precio_raw).replace('$', '').replace(',', '').strip())
            except: 
                costo = 0.0

            # Moneda
            moneda_raw = row.get('Divisa Proveedor') or row.get('Moneda') or 'MXN'
            moneda = 'MXN' if 'MN' in moneda_raw or 'Peso' in moneda_raw else 'USD'

            # Stock
            try:
                stock = int(float(row.get('Inventario') or row.get('Stock') or 0))
            except:
                stock = 0

            tiempo = row.get('T. Entrega') or row.get('Tiempo Entrega') or '1-2 Semanas'
            proveedor_nombre = row.get('Proveedor1') or row.get('Proveedor')

            # 3. Lógica de Proveedor (Crear si no existe)
            prov_id = None
            if proveedor_nombre:
                prov = db.query(models.Proveedor).filter(models.Proveedor.nombre == proveedor_nombre).first()
                if not prov:
                    prov = models.Proveedor(nombre=proveedor_nombre)
                    db.add(prov)
                    db.commit()
                    db.refresh(prov)
                prov_id = prov.id

            # 4. Upsert Producto (Actualizar o Insertar)
            producto = db.query(models.Producto).filter(models.Producto.numero_catalogo == catalogo).first()

            if producto:
                # Actualizar
                producto.descripcion = descripcion
                producto.marca = marca
                producto.costo_proveedor = costo
                producto.moneda_compra = moneda
                producto.stock_actual = stock
                producto.tiempo_entrega = tiempo
                if prov_id: producto.proveedor_id = prov_id
                actualizados += 1
            else:
                # Insertar
                nuevo_prod = models.Producto(
                    numero_catalogo=catalogo,
                    descripcion=descripcion,
                    marca=marca,
                    costo_proveedor=costo,
                    moneda_compra=moneda,
                    stock_actual=stock,
                    tiempo_entrega=tiempo,
                    proveedor_id=prov_id
                )
                db.add(nuevo_prod)
                nuevos += 1
                
        except Exception as e:
            print(f"Error en fila {row}: {e}")
            errores += 1
            continue

    db.commit()
    
    return {
        "mensaje": "Proceso finalizado",
        "nuevos": nuevos,
        "actualizados": actualizados,
        "errores": errores
    }