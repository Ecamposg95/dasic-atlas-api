from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Union
import csv
import io
from app import models
from app import schemas
from app.db import get_db
from app.security import allow_admin, allow_admin_asistente, allow_all_staff

router = APIRouter(prefix="/api/productos", tags=["Productos"])

DEFAULT_PURCHASE_CURRENCY = "MXN"
IMPORT_COLUMN_ALIASES = {
    "sku": ("sku", "codigo", "codigo_interno"),
    "sku_comercial": ("sku_comercial", "sku comercial", "commercial_sku"),
    "nombre": ("nombre", "producto"),
    "descripcion": ("descripcion", "descripción"),
    "stock_actual": ("stock", "stock_actual", "existencia"),
    "stock_minimo": ("stock_minimo", "stock mínimo", "minimo"),
    "costo_compra": ("costo", "costo_compra", "purchase_cost"),
    "precio_publico": ("precio_publico", "precio público", "precio_lista"),
    "precio_mayorista": ("precio_mayorista",),
    "precio_distribuidor": ("precio_distribuidor",),
    "moneda_compra": ("moneda_compra", "moneda", "currency"),
}
IMPORT_TEMPLATE_COLUMNS = [
    "sku",
    "sku_comercial",
    "nombre",
    "descripcion",
    "stock",
    "stock_minimo",
    "costo",
    "moneda_compra",
    "precio_publico",
    "precio_mayorista",
    "precio_distribuidor",
]


def _normalize_sku(value: str) -> str:
    return value.strip().upper()


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_currency(value: Optional[str]) -> str:
    normalized = (value or DEFAULT_PURCHASE_CURRENCY).strip().upper()
    return normalized or DEFAULT_PURCHASE_CURRENCY


def _resolve_public_price(raw_price: Optional[Decimal], costo_compra: Decimal) -> Decimal:
    return costo_compra if raw_price is None else raw_price


def _read_decimal(row: dict, field_name: str) -> Optional[Decimal]:
    for alias in IMPORT_COLUMN_ALIASES[field_name]:
        raw_value = row.get(alias)
        if raw_value is None:
            continue
        cleaned = str(raw_value).strip().replace(",", "")
        if cleaned == "":
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} inválido: {raw_value}") from exc
    return None


def _read_int(row: dict, field_name: str, default: int = 0) -> int:
    for alias in IMPORT_COLUMN_ALIASES[field_name]:
        raw_value = row.get(alias)
        if raw_value is None:
            continue
        cleaned = str(raw_value).strip()
        if cleaned == "":
            return default
        try:
            return int(Decimal(cleaned))
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} inválido: {raw_value}") from exc
    return default


def _read_text(row: dict, field_name: str, default: Optional[str] = None) -> Optional[str]:
    for alias in IMPORT_COLUMN_ALIASES[field_name]:
        raw_value = row.get(alias)
        if raw_value is None:
            continue
        normalized = _normalize_optional_text(str(raw_value))
        if normalized is not None:
            return normalized
    return default


def _normalize_csv_row(row: dict) -> dict:
    return {
        (str(key).strip().lower() if key is not None else ""): (value.strip() if isinstance(value, str) else value)
        for key, value in row.items()
        if key is not None
    }

# --- 1. OBTENER PRODUCTOS (LISTADO INTELIGENTE) ---
@router.get("/", response_model=Union[List[schemas.ProductoResponseAdmin], List[schemas.ProductoResponseVendedor]])
def listar_productos(
    skip: int = 0, 
    limit: int = 500, # Aumentamos el límite por defecto
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(allow_all_staff)
):
    """
    Lista productos. 
    - Admin/Asistente ven el Costo.
    - Vendedores solo ven Precios de Venta y Stock.
    """
    productos = db.query(models.Producto).offset(skip).limit(limit).all()

    # Lógica de "Camaleón": Decidimos qué schema usar según el rol
    if current_user.rol in [models.RolUsuario.ADMIN, models.RolUsuario.ASISTENTE]:
        return [schemas.ProductoResponseAdmin.model_validate(p) for p in productos]
    
    return [schemas.ProductoResponseVendedor.model_validate(p) for p in productos]

# --- 2. OBTENER UN SOLO PRODUCTO ---
@router.get("/{id}", response_model=Union[schemas.ProductoResponseAdmin, schemas.ProductoResponseVendedor])
def obtener_producto(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(allow_all_staff)
):
    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if current_user.rol in [models.RolUsuario.ADMIN, models.RolUsuario.ASISTENTE]:
        return schemas.ProductoResponseAdmin.model_validate(producto)
    return schemas.ProductoResponseVendedor.model_validate(producto)

# --- 3. CREAR PRODUCTO (SOLO ADMIN/ASISTENTE) ---
@router.post("/", response_model=schemas.ProductoResponseAdmin, dependencies=[Depends(allow_admin_asistente)])
def crear_producto(
    producto: schemas.ProductoCreate, 
    db: Session = Depends(get_db)
):
    sku = _normalize_sku(producto.sku)

    # Verificar si el SKU ya existe
    db_producto = db.query(models.Producto).filter(models.Producto.sku == sku).first()
    if db_producto:
        raise HTTPException(status_code=400, detail=f"El SKU '{sku}' ya existe.")

    payload = producto.model_dump()
    payload["sku"] = sku
    payload["sku_comercial"] = _normalize_optional_text(producto.sku_comercial)
    payload["moneda_compra"] = _normalize_currency(producto.moneda_compra)
    payload["precio_publico"] = _resolve_public_price(producto.precio_publico, producto.costo_compra)

    nuevo_producto = models.Producto(**payload)
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

# --- 4. ACTUALIZAR PRODUCTO ---
@router.put("/{id}", response_model=schemas.ProductoResponseAdmin, dependencies=[Depends(allow_admin_asistente)])
def actualizar_producto(
    id: int,
    producto_update: schemas.ProductoUpdate,
    db: Session = Depends(get_db)
):
    db_producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Actualizamos solo los campos enviados
    update_data = producto_update.model_dump(exclude_unset=True)
    if "sku_comercial" in update_data:
        update_data["sku_comercial"] = _normalize_optional_text(update_data["sku_comercial"])
    if "moneda_compra" in update_data:
        update_data["moneda_compra"] = _normalize_currency(update_data["moneda_compra"])
    if "precio_publico" in update_data and update_data["precio_publico"] is None:
        costo_base = update_data.get("costo_compra", db_producto.costo_compra)
        update_data["precio_publico"] = _resolve_public_price(None, costo_base)
    elif "costo_compra" in update_data and "precio_publico" not in update_data and db_producto.precio_publico == db_producto.costo_compra:
        update_data["precio_publico"] = update_data["costo_compra"]
    for key, value in update_data.items():
        setattr(db_producto, key, value)

    db.commit()
    db.refresh(db_producto)
    return db_producto

# --- 5. ELIMINAR PRODUCTO (SOLO ADMIN) ---
@router.delete("/{id}", dependencies=[Depends(allow_admin)])
def eliminar_producto(id: int, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """
    Importa productos desde CSV.
    Columnas base: sku, nombre, costo, stock.
    Columnas opcionales: sku_comercial, moneda_compra, precio_publico, precio_mayorista, precio_distribuidor, descripcion, stock_minimo.
    """
    filename = (file.filename or "").lower()
    if filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "La importación directa de Excel aún no está habilitada.",
                "usa_csv_mientras_tanto": True,
                "columnas_compatibles": IMPORT_TEMPLATE_COLUMNS,
            },
        )
    if not filename.endswith(".csv"):
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
            row = _normalize_csv_row(row)

            sku = _read_text(row, "sku")
            if not sku:
                continue # Saltar filas vacías
            sku = _normalize_sku(sku)

            sku_comercial = _read_text(row, "sku_comercial")
            nombre = _read_text(row, "nombre", "Sin Nombre") or "Sin Nombre"
            descripcion = _read_text(row, "descripcion", "") or ""
            moneda_compra = _normalize_currency(_read_text(row, "moneda_compra", DEFAULT_PURCHASE_CURRENCY))
            costo_compra = _read_decimal(row, "costo_compra") or Decimal("0")
            precio_publico = _resolve_public_price(_read_decimal(row, "precio_publico"), costo_compra)
            precio_mayorista = _read_decimal(row, "precio_mayorista") or Decimal("0")
            precio_distribuidor = _read_decimal(row, "precio_distribuidor") or Decimal("0")
            stock_actual = _read_int(row, "stock_actual", 0)
            stock_minimo = _read_int(row, "stock_minimo", 5)

            # Buscar si existe para actualizar (Upsert)
            producto_existente = db.query(models.Producto).filter(models.Producto.sku == sku).first()

            if producto_existente:
                # Actualizar Stock y Precios si vienen en el CSV
                producto_existente.stock_actual += stock_actual
                producto_existente.sku_comercial = sku_comercial or producto_existente.sku_comercial
                producto_existente.nombre = nombre or producto_existente.nombre
                producto_existente.descripcion = descripcion or producto_existente.descripcion
                producto_existente.stock_minimo = stock_minimo
                producto_existente.moneda_compra = moneda_compra
                producto_existente.costo_compra = costo_compra
                producto_existente.precio_publico = precio_publico
                producto_existente.precio_mayorista = precio_mayorista
                producto_existente.precio_distribuidor = precio_distribuidor
                registros_actualizados += 1
            else:
                # Crear nuevo
                nuevo_prod = models.Producto(
                    sku=sku,
                    sku_comercial=sku_comercial,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio_publico=precio_publico,
                    precio_mayorista=precio_mayorista,
                    precio_distribuidor=precio_distribuidor,
                    costo_compra=costo_compra,
                    moneda_compra=moneda_compra,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
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
def exportar_productos_csv(db: Session = Depends(get_db)):
    """Genera y descarga un archivo CSV con todo el inventario"""
    productos = db.query(models.Producto).all()
    
    # Crear archivo en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'SKU', 'SKU Comercial', 'Nombre', 'Descripción', 'Stock Actual', 'Stock Mínimo',
        'Costo', 'Moneda Compra', 'Precio Público', 'Precio Mayorista', 'Precio Distribuidor'
    ])
    
    # Datos
    for p in productos:
        writer.writerow([
            p.sku, p.sku_comercial, p.nombre, p.descripcion, p.stock_actual, p.stock_minimo,
            p.costo_compra, p.moneda_compra, p.precio_publico, p.precio_mayorista, p.precio_distribuidor
        ])
    
    output.seek(0)
    
    # StreamingResponse permite descargar el archivo al vuelo
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventario_dasic.csv"
    return response
