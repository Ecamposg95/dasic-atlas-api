# seed.py
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
from app.auth import get_password_hash

# Datos de prueba
PRODUCTOS_DEMO = [
    {
        "numero_catalogo": "BES-M12MI",
        "descripcion": "Sensor Inductivo Balluff M12, Alcance 4mm, PNP, NA",
        "marca": "Balluff",
        "costo_proveedor": 450.00,
        "moneda_compra": "MXN",
        "tiempo_entrega": "Inmediato",
        "stock_actual": 10,
        "imagen_url": "https://assets.balluff.com/WebBinary1/0000000000018596-Medium.jpg"
    },
    {
        "numero_catalogo": "VUVG-L10-B52",
        "descripcion": "Válvula Solenoide Festo VUVG, 5/2 Vías, 24VDC",
        "marca": "Festo",
        "costo_proveedor": 35.00,
        "moneda_compra": "USD",
        "tiempo_entrega": "1 Semana",
        "stock_actual": 5,
        "imagen_url": "https://www.festo.com/rep/en-gb_gb/assets/im/1024/298822066.jpg"
    },
    {
        "numero_catalogo": "6ES7214-1AG40",
        "descripcion": "PLC Siemens S7-1200 CPU 1214C, DC/DC/DC",
        "marca": "Siemens",
        "costo_proveedor": 280.00,
        "moneda_compra": "USD",
        "tiempo_entrega": "3-4 Semanas",
        "stock_actual": 2,
        "imagen_url": "https://media.automation24.com/images/1024/101784_0_01.jpg"
    },
    {
        "numero_catalogo": "MARTOR-9870",
        "descripcion": "Hoja de gancho Martor No. 98, color plateado",
        "marca": "Martor",
        "costo_proveedor": 1275.87,
        "moneda_compra": "MXN",
        "tiempo_entrega": "2 Días",
        "stock_actual": 50,
        "imagen_url": "https://www.martor.com/fileadmin/_processed_/d/f/csm_98_b0a67d515a.jpg"
    },
    {
        "numero_catalogo": "MUDDER-HOOK",
        "descripcion": "Cuchillas Con Gancho Utilitario, Acero Inoxidable",
        "marca": "Mudder",
        "costo_proveedor": 1524.26,
        "moneda_compra": "MXN",
        "tiempo_entrega": "1 Día Hábil",
        "stock_actual": 20,
        "imagen_url": "https://m.media-amazon.com/images/I/61+7wN-dOAL._AC_SL1500_.jpg"
    }
]

def init_db():
    # Asegurar que las tablas existan antes de insertar
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("🌱 Iniciando sembrado de datos...")

        # 1. CREAR ADMIN
        if not db.query(models.Usuario).filter(models.Usuario.username == "admin").first():
            hashed = get_password_hash("admin123")
            user = models.Usuario(username="admin", hashed_password=hashed, rol="admin")
            db.add(user)
            print("✅ Usuario ADMIN creado (admin / admin123)")
        else:
            print("ℹ️ El usuario Admin ya existe.")

        # 2. CREAR CLIENTE DEMO
        if not db.query(models.Cliente).filter(models.Cliente.nombre == "Ing. Erick Campos").first():
            cliente = models.Cliente(
                nombre="Ing. Erick Campos",
                compania="Durakon Industries México SA de CV",
                email="erick.campos@durakon.com",
                telefono="55 1234 5678",
                rfc="DIM123456XYZ",
                direccion="Ave. Industrial 123, Parque Industrial Querétaro",
                dias_credito=30,
                saldo_actual=0.0
            )
            db.add(cliente)
            print("✅ Cliente DEMO creado (Durakon Industries)")
        else:
            print("ℹ️ El cliente Demo ya existe.")

        # 3. CREAR PRODUCTOS
        count = 0
        for p_data in PRODUCTOS_DEMO:
            if not db.query(models.Producto).filter(models.Producto.numero_catalogo == p_data["numero_catalogo"]).first():
                prod = models.Producto(**p_data)
                db.add(prod)
                count += 1
        
        if count > 0:
            print(f"✅ {count} Productos insertados.")
        else:
            print("ℹ️ Los productos ya existían.")

        db.commit()
        print("✨ ¡Base de datos inicializada correctamente!")

    except Exception as e:
        print(f"❌ Error al inicializar DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()