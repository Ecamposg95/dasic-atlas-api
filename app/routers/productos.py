from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Union
import csv
import io
import models
import schemas
import database
from auth import get_current_user, allow_admin, allow_admin_asistente, allow_all_staff
from models import RolUsuario

router = APIRouter(prefix="/api/productos", tags=["Productos"])

# --- 1. OBTENER PRODUCTOS (LISTADO INTELIGENTE) ---
@router.get("/", response_model=Union[List[schemas.ProductoResponseAdmin], List[schemas.ProductoResponseVendedor]])
def listar_productos(
    skip: int = 0, 
    limit: int = 500, # Aumentamos el límite por defecto
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(allow_all_staff)
):
    """
    Lista productos. 
    - Admin/Asistente ven el Costo.
    - Vendedores solo ven Precios de Venta y Stock.
    """
    productos = db.query(models.Producto).offset(skip).limit(limit).all()

    # Lógica de "Camaleón": Decidimos qué schema usar según el rol
    if current_user.rol in [RolUsuario.ADMIN, RolUsuario.ASISTENTE]:
        return [schemas.ProductoResponseAdmin.model_validate(p) for p in productos]
    
    return [schemas.ProductoResponseVendedor.model_validate(p) for p in productos]

# --- 2. OBTENER UN SOLO PRODUCTO ---
@router.get("/{id}", response_model=Union[schemas.ProductoResponseAdmin, schemas.ProductoResponseVendedor])
def obtener_producto(
    id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(allow_all_staff)
):
    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if current_user.rol in [RolUsuario.ADMIN, RolUsuario.ASISTENTE]:
        return schemas.ProductoResponseAdmin.model_validate(producto)
    return schemas.ProductoResponseVendedor.model_validate(producto)

# --- 3. CREAR PRODUCTO (SOLO ADMIN/ASISTENTE) ---
@router.post("/", response_model=schemas.ProductoResponseAdmin, dependencies=[Depends(allow_admin_asistente)])
def crear_producto(
    producto: schemas.ProductoCreate, 
    db: Session = Depends(database.get_db)
):
    # Verificar si el SKU ya existe
    db_producto = db.query(models.Producto).filter(models.Producto.sku == producto.sku).first()
    if db_producto:
        raise HTTPException(status_code=400, detail=f"El SKU '{producto.sku}' ya existe.")

    nuevo_producto = models.Producto(**producto.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

# --- 4. ACTUALIZAR PRODUCTO ---
@router.put("/{id}", response_model=schemas.ProductoResponseAdmin, dependencies=[Depends(allow_admin_asistente)])
def actualizar_producto(
    id: int,
    producto_update: schemas.ProductoUpdate,
    db: Session = Depends(database.get_db)
):
    db_producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Actualizamos solo los campos enviados
    update_data = producto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_producto, key, value)

    db.commit()
    db.refresh(db_producto)
    return db_producto

# --- 5. ELIMINAR PRODUCTO (SOLO ADMIN) ---
@router.delete("/{id}", dependencies=[Depends(allow_admin)])
def eliminar_producto(id: int, db: Session = Depends(database.get_db)):
    db_producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(db_producto)
    db.commit()
    return {"mensaje": "Producto eliminado correctamente"}

# --- 6. CARGA MASIVA CSV (IMPORTAR) ---
@router.post("/upload-csv", dependencies=[Depends(allow_admin_asistente)])
async def cargar_inventario_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    """
    Importa productos desde CSV.
    Columnas esperadas: sku, nombre, precio_publico, costo, stock
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")

    # Leer el archivo en memoria
    content = await file.read()
    decoded_content = content.decode('utf-8-sig') # utf-8-sig maneja BOM de Excel
    csv_reader = csv.DictReader(io.StringIO(decoded_content))

    registros_nuevos = 0
    registros_actualizados = 0
    errores = []

    for row in csv_reader:
        try:
            # Normalizar claves del CSV (quitar espacios, minúsculas)
            row = {k.strip().lower(): v for k, v in row.items()}
            
            sku = row.get('sku')
            if not sku: continue # Saltar filas vacías
            
            # Buscar si existe para actualizar (Upsert)
            producto_existente = db.query(models.Producto).filter(models.Producto.sku == sku).first()
            
            if producto_existente:
                # Actualizar Stock y Precios si vienen en el CSV
                if 'stock' in row: producto_existente.stock_actual += int(row['stock'])
                if 'precio_publico' in row: producto_existente.precio_publico = float(row['precio_publico'])
                if 'costo' in row: producto_existente.costo_compra = float(row['costo'])
                registros_actualizados += 1
            else:
                # Crear nuevo
                nuevo_prod = models.Producto(
                    sku=sku.upper(),
                    nombre=row.get('nombre', 'Sin Nombre'),
                    descripcion=row.get('descripcion', ''),
                    precio_publico=float(row.get('precio_publico', 0)),
                    precio_mayorista=float(row.get('precio_mayorista', 0)),
                    precio_distribuidor=float(row.get('precio_distribuidor', 0)),
                    costo_compra=float(row.get('costo', 0)),
                    stock_actual=int(row.get('stock', 0)),
                    stock_minimo=int(row.get('stock_minimo', 5))
                )
                db.add(nuevo_prod)
                registros_nuevos += 1
                
        except Exception as e:
            errores.append(f"Error en SKU {row.get('sku', '?')}: {str(e)}")

    db.commit()
    return {
        "mensaje": "Proceso completado",
        "creados": registros_nuevos,
        "actualizados": registros_actualizados,
        "errores": errores
    }

# --- 7. EXPORTAR CSV (DESCARGAR) ---
@router.get("/exportar/csv", dependencies=[Depends(allow_admin_asistente)])
def exportar_productos_csv(db: Session = Depends(database.get_db)):
    """Genera y descarga un archivo CSV con todo el inventario"""
    productos = db.query(models.Producto).all()
    
    # Crear archivo en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'SKU', 'Nombre', 'Descripción', 'Stock Actual', 'Stock Mínimo', 
        'Costo', 'Precio Público', 'Precio Mayorista', 'Precio Distribuidor'
    ])
    
    # Datos
    for p in productos:
        writer.writerow([
            p.sku, p.nombre, p.descripcion, p.stock_actual, p.stock_minimo,
            p.costo_compra, p.precio_publico, p.precio_mayorista, p.precio_distribuidor
        ])
    
    output.seek(0)
    
    # StreamingResponse permite descargar el archivo al vuelo
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventario_dasic.csv"
    return response