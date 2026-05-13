"""
Database seeding.

Single-tenant: solo crea el usuario administrador inicial si la tabla está vacía.

También aplica DDL idempotente para columnas/tablas nuevas, como puente
entre instancias en producción que arrancan sin correr `alembic upgrade head`
(el Procfile sólo levanta uvicorn). Las migraciones siguen siendo la
fuente de verdad para entornos limpios.
"""

import json
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.schemas import UsuarioCreate
from app.services import UserService

logger = logging.getLogger(__name__)

MARCA_TAXONOMY_FILE = Path(__file__).resolve().parent.parent / "data" / "marca_abreviaturas.json"


# DDL idempotente: cada sentencia debe ser segura de re-ejecutar.
# Solo agregar entradas para cambios que YA viven en migrations/versions/.
_BACKFILL_DDL = [
    # 20260430_01: cotizador robusto
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS proveedor_principal_id INTEGER REFERENCES proveedores(id)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS proveedor_alterno_id INTEGER REFERENCES proveedores(id)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS tiempo_entrega_dias INTEGER NOT NULL DEFAULT 7",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS es_servicio BOOLEAN NOT NULL DEFAULT false",
    "CREATE INDEX IF NOT EXISTS ix_productos_proveedor_principal_id ON productos (proveedor_principal_id)",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS tipo_linea VARCHAR(20) NOT NULL DEFAULT 'producto_catalogo'",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS proveedor_sugerido_id INTEGER REFERENCES proveedores(id)",
    # 20260429_02: marca + unidad
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS marca VARCHAR(80)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS unidad VARCHAR(20) DEFAULT 'PZA'",
    "CREATE INDEX IF NOT EXISTS ix_productos_marca ON productos (marca)",
    # 20260430_02: RBAC owner scoping para clientes
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS creado_por_id INTEGER REFERENCES usuarios(id)",
    "CREATE INDEX IF NOT EXISTS ix_clientes_creado_por_id ON clientes (creado_por_id)",
    # 20260430_03 (no migration formal): gastos.moneda
    "ALTER TABLE IF EXISTS gastos ADD COLUMN IF NOT EXISTS moneda VARCHAR(3) NOT NULL DEFAULT 'MXN'",
    # plantillas_cotizacion (create_all la genera; este DDL es seguro idempotente)
    """CREATE TABLE IF NOT EXISTS plantillas_cotizacion (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(120) NOT NULL,
        descripcion TEXT,
        usuario_id INTEGER REFERENCES usuarios(id),
        lineas TEXT NOT NULL DEFAULT '[]',
        creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS ix_plantillas_cotizacion_usuario_id ON plantillas_cotizacion (usuario_id)",
    # 20260510_01: tabla de marcas (taxonomía DASIC + SKU prefix)
    """CREATE TABLE IF NOT EXISTS marcas (
        id SERIAL PRIMARY KEY,
        abreviatura VARCHAR(20) NOT NULL UNIQUE,
        nombre VARCHAR(150) NOT NULL,
        categoria VARCHAR(150),
        creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_marcas_abreviatura ON marcas (abreviatura)",
    # 20260512_03: FK Producto.marca_id → marcas.id (SET NULL en delete)
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS marca_id INTEGER REFERENCES marcas(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_productos_marca_id ON productos (marca_id)",
    # 20260513_01: tiempos de entrega por línea (sin CHECK aquí; CHECK solo en migración formal)
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS entrega_min INTEGER",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS entrega_max INTEGER",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS entrega_unidad VARCHAR(10)",
    # 20260513_02: términos y condiciones editables por cotización
    "ALTER TABLE IF EXISTS ordenes_venta ADD COLUMN IF NOT EXISTS terminos_condiciones TEXT",
    # 20260515_01: nota libre por línea (productos similares manuales)
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS observaciones_linea TEXT",

    # ====================================================================
    # Fase 1 — Catálogos SAT chicos (10 tablas; las masivas viven aparte).
    # Producción: create_all() ya las crea desde el metadata. Estas líneas
    # son redundantes pero garantizan idempotencia si create_all falla.
    # ====================================================================
    """CREATE TABLE IF NOT EXISTS sat_forma_pago (
        codigo VARCHAR(3) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        activo BOOLEAN NOT NULL DEFAULT true,
        vigencia_desde DATE,
        vigencia_hasta DATE,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_metodo_pago (
        codigo VARCHAR(3) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        activo BOOLEAN NOT NULL DEFAULT true,
        vigencia_desde DATE,
        vigencia_hasta DATE,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_uso_cfdi (
        codigo VARCHAR(5) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        activo BOOLEAN NOT NULL DEFAULT true,
        vigencia_desde DATE,
        vigencia_hasta DATE,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_regimen_fiscal (
        codigo VARCHAR(3) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        aplica_persona_fisica BOOLEAN NOT NULL DEFAULT false,
        aplica_persona_moral BOOLEAN NOT NULL DEFAULT false,
        activo BOOLEAN NOT NULL DEFAULT true,
        vigencia_desde DATE,
        vigencia_hasta DATE,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_objeto_imp (
        codigo VARCHAR(2) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_impuesto (
        codigo VARCHAR(3) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        aplica_traslado BOOLEAN NOT NULL DEFAULT false,
        aplica_retencion BOOLEAN NOT NULL DEFAULT false,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_tipo_factor (
        codigo VARCHAR(10) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_tasa_o_cuota (
        id_local VARCHAR(30) PRIMARY KEY,
        impuesto VARCHAR(3) NOT NULL,
        tipo_factor VARCHAR(10) NOT NULL,
        valor NUMERIC(7,6) NOT NULL,
        descripcion TEXT NOT NULL,
        es_retencion BOOLEAN NOT NULL DEFAULT false,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_moneda (
        codigo VARCHAR(3) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        decimales VARCHAR(2) NOT NULL DEFAULT '2',
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_tipo_comprobante (
        codigo VARCHAR(2) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_clave_prodserv (
        codigo VARCHAR(8) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        palabras_clave TEXT,
        incluir_iva_basico BOOLEAN NOT NULL DEFAULT true,
        vigencia_desde DATE,
        vigencia_hasta DATE,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sat_clave_unidad (
        codigo VARCHAR(3) PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        descripcion TEXT,
        simbolo VARCHAR(20),
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_en TIMESTAMPTZ DEFAULT now()
    )""",

    # ====================================================================
    # Fase 2 — Producto: campos SAT + clasificación interna
    # `abreviatura` y `catalogo_fabricante` fueron eliminados en
    # 20260517_01 (duplicaban `sku` y `sku_comercial`). Los drops están
    # más abajo en este array para que Railway los aplique.
    # ====================================================================
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS clave_prod_serv VARCHAR(8)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS clave_unidad_sat VARCHAR(10)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS objeto_imp VARCHAR(2)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS descripcion_fiscal TEXT",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS categoria VARCHAR(80)",
    "CREATE INDEX IF NOT EXISTS ix_productos_categoria ON productos (categoria)",
    "CREATE INDEX IF NOT EXISTS ix_productos_clave_prod_serv ON productos (clave_prod_serv)",

    # ====================================================================
    # Fase 3 — Servicios (catálogo)
    # create_all() debería crear la tabla; este DDL la garantiza.
    # ====================================================================
    """CREATE TABLE IF NOT EXISTS servicios (
        id SERIAL PRIMARY KEY,
        organization_id VARCHAR(36),
        codigo VARCHAR(30) NOT NULL,
        nombre VARCHAR(150) NOT NULL,
        descripcion TEXT,
        categoria_servicio VARCHAR(40),
        costo NUMERIC(12,2) NOT NULL DEFAULT 0,
        moneda VARCHAR(3) NOT NULL DEFAULT 'MXN',
        tiempo_estimado NUMERIC(8,2),
        unidad_tiempo VARCHAR(10),
        clave_prod_serv VARCHAR(8) NOT NULL DEFAULT '81111500',
        clave_unidad_sat VARCHAR(10) NOT NULL DEFAULT 'E48',
        objeto_imp VARCHAR(2) DEFAULT '02',
        descripcion_fiscal TEXT,
        activo BOOLEAN NOT NULL DEFAULT true,
        creado_por_id INTEGER REFERENCES usuarios(id),
        creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_servicios_org_codigo ON servicios (organization_id, codigo)",
    "CREATE INDEX IF NOT EXISTS ix_servicios_activo ON servicios (activo)",
    "CREATE INDEX IF NOT EXISTS ix_servicios_categoria ON servicios (categoria_servicio)",
    "CREATE INDEX IF NOT EXISTS ix_servicios_nombre ON servicios (nombre)",

    # ====================================================================
    # Fase 4 — DetalleOrden.servicio_id FK
    # ====================================================================
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS servicio_id INTEGER REFERENCES servicios(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_detalles_orden_servicio_id ON detalles_orden (servicio_id)",

    # ====================================================================
    # Fase 5 — DetalleCompra: producto_id nullable + fantasma + moneda
    # ====================================================================
    "ALTER TABLE IF EXISTS detalles_compra ALTER COLUMN producto_id DROP NOT NULL",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS sku_libre VARCHAR(80)",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS descripcion_libre VARCHAR(255)",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS moneda_origen_linea VARCHAR(3)",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS costo_base_linea NUMERIC(12,2)",

    # ====================================================================
    # Fase 6 — CRM: créditos en Cliente + CxC formal en TransaccionCliente
    # ====================================================================
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS limite_credito NUMERIC(12,2) NOT NULL DEFAULT 0",
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS dias_credito INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS dia_corte INTEGER",
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS moneda_credito VARCHAR(3) NOT NULL DEFAULT 'MXN'",
    "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS orden_venta_id INTEGER REFERENCES ordenes_venta(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_tx_cli_orden_venta ON transacciones_clientes (orden_venta_id)",
    "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS fecha_vencimiento DATE",
    "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS estatus_pago VARCHAR(20) NOT NULL DEFAULT 'pendiente'",
    "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS monto_pagado NUMERIC(12,2) NOT NULL DEFAULT 0",
    "CREATE INDEX IF NOT EXISTS ix_tx_cli_estatus_pago ON transacciones_clientes (estatus_pago)",

    # ====================================================================
    # 20260517_01 — drop columnas redundantes (abreviatura, catalogo_fabricante)
    # Idempotente: si ya no existen, no-op. Si existen con datos, primero
    # copiamos a sku_comercial cuando aplica para no perder info del usuario.
    # ====================================================================
    """UPDATE productos
          SET sku_comercial = catalogo_fabricante
        WHERE catalogo_fabricante IS NOT NULL
          AND catalogo_fabricante <> ''
          AND (sku_comercial IS NULL OR sku_comercial = '')""",
    "DROP INDEX IF EXISTS ix_productos_abreviatura",
    "DROP INDEX IF EXISTS ix_productos_catalogo_fabricante",
    "ALTER TABLE IF EXISTS productos DROP COLUMN IF EXISTS abreviatura",
    "ALTER TABLE IF EXISTS productos DROP COLUMN IF EXISTS catalogo_fabricante",
]


def run_backfill_ddl(db: Session) -> None:
    """Ejecuta DDL idempotente para columnas nuevas. Tolera errores individuales."""
    for stmt in _BACKFILL_DDL:
        try:
            db.execute(text(stmt))
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Backfill DDL skip (%s): %s", stmt[:80], exc)


def seed_super_admin(db: Session) -> None:
    """Crea el usuario administrador inicial si no existe ningún usuario."""
    if db.query(models.Usuario).first():
        logger.info("DASIC ERP online")
        return

    logger.info("Inicializando sistema DASIC ERP — creando administrador...")
    admin = UsuarioCreate(
        nombre="Administrador Principal",
        email="admin@dasic.mx",
        password="784512",
        rol=models.RolUsuario.ADMIN,
        activo=True,
    )
    UserService.create_user(db, admin)
    logger.info("Admin creado: admin@dasic.mx")


def seed_marcas(db: Session) -> None:
    """Carga marca_abreviaturas.json en la tabla `marcas` si está vacía.

    Idempotente: solo inserta lo que no existe (por `abreviatura`). En
    re-arranques no toca filas existentes, así el CRUD desde la UI no se
    pierde aunque el JSON cambie.
    """
    if not MARCA_TAXONOMY_FILE.exists():
        return
    try:
        data = json.loads(MARCA_TAXONOMY_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("No se pudo leer marca_abreviaturas.json: %s", exc)
        return

    existentes = {m.abreviatura for m in db.query(models.Marca).all()}
    nuevas = 0
    for it in data.get("items", []):
        abrev = (it.get("abreviatura") or "").strip().upper()
        nombre = (it.get("marca") or "").strip()
        if not abrev or not nombre or abrev in existentes:
            continue
        db.add(models.Marca(
            abreviatura=abrev,
            nombre=nombre,
            categoria=(it.get("categoria") or "").strip() or None,
        ))
        existentes.add(abrev)
        nuevas += 1
    if nuevas:
        db.commit()
        logger.info("Sembradas %d marcas desde taxonomía DASIC.", nuevas)


def seed_sat_catalogos_pequenos(db: Session) -> None:
    """Siembra los 10 catálogos SAT chicos desde `app/data/sat/*`.

    Idempotente: usa `ON CONFLICT DO NOTHING` por código. Si el SAT actualiza
    una descripción, re-correr no la sobreescribe (preserva ediciones manuales
    si las hubiera). Para forzar refresh, vaciar la tabla antes del seed.
    """
    try:
        from app.data.sat import (
            FORMAS_PAGO, METODOS_PAGO, USOS_CFDI, REGIMENES_FISCALES,
            OBJETOS_IMP, IMPUESTOS, TIPOS_FACTOR, TASAS_O_CUOTAS,
            MONEDAS, TIPOS_COMPROBANTE,
        )
    except Exception as exc:
        logger.warning("No se pudo importar datos SAT (%s); skip seed SAT.", exc)
        return

    plan: list[tuple[str, str, list[tuple]]] = [
        (
            "sat_forma_pago",
            "INSERT INTO sat_forma_pago (codigo, descripcion) VALUES (:codigo, :descripcion) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d} for (c, d) in FORMAS_PAGO],
        ),
        (
            "sat_metodo_pago",
            "INSERT INTO sat_metodo_pago (codigo, descripcion) VALUES (:codigo, :descripcion) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d} for (c, d) in METODOS_PAGO],
        ),
        (
            "sat_uso_cfdi",
            "INSERT INTO sat_uso_cfdi (codigo, descripcion) VALUES (:codigo, :descripcion) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d} for (c, d) in USOS_CFDI],
        ),
        (
            "sat_regimen_fiscal",
            "INSERT INTO sat_regimen_fiscal (codigo, descripcion, aplica_persona_fisica, aplica_persona_moral) "
            "VALUES (:codigo, :descripcion, :pf, :pm) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d, "pf": pf, "pm": pm} for (c, d, pf, pm) in REGIMENES_FISCALES],
        ),
        (
            "sat_objeto_imp",
            "INSERT INTO sat_objeto_imp (codigo, descripcion) VALUES (:codigo, :descripcion) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d} for (c, d) in OBJETOS_IMP],
        ),
        (
            "sat_impuesto",
            "INSERT INTO sat_impuesto (codigo, descripcion, aplica_traslado, aplica_retencion) "
            "VALUES (:codigo, :descripcion, :tr, :re) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d, "tr": tr, "re": re} for (c, d, tr, re) in IMPUESTOS],
        ),
        (
            "sat_tipo_factor",
            "INSERT INTO sat_tipo_factor (codigo, descripcion) VALUES (:codigo, :descripcion) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d} for (c, d) in TIPOS_FACTOR],
        ),
        (
            "sat_tasa_o_cuota",
            "INSERT INTO sat_tasa_o_cuota (id_local, impuesto, tipo_factor, valor, descripcion, es_retencion) "
            "VALUES (:id_local, :imp, :tf, :val, :desc, :ret) ON CONFLICT (id_local) DO NOTHING",
            [
                {"id_local": idl, "imp": imp, "tf": tf, "val": val, "desc": desc, "ret": ret}
                for (idl, imp, tf, val, desc, ret) in TASAS_O_CUOTAS
            ],
        ),
        (
            "sat_moneda",
            "INSERT INTO sat_moneda (codigo, descripcion, decimales) VALUES (:codigo, :descripcion, :dec) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d, "dec": str(dec)} for (c, d, dec) in MONEDAS],
        ),
        (
            "sat_tipo_comprobante",
            "INSERT INTO sat_tipo_comprobante (codigo, descripcion) VALUES (:codigo, :descripcion) ON CONFLICT (codigo) DO NOTHING",
            [{"codigo": c, "descripcion": d} for (c, d) in TIPOS_COMPROBANTE],
        ),
    ]

    total = 0
    for table_name, stmt, rows in plan:
        try:
            res = db.execute(text(stmt), rows)
            inserted = res.rowcount if res.rowcount and res.rowcount > 0 else 0
            db.commit()
            total += inserted
            if inserted:
                logger.info("SAT %s: %d filas insertadas.", table_name, inserted)
        except Exception as exc:
            db.rollback()
            logger.warning("SAT seed skip %s: %s", table_name, exc)

    if total == 0:
        logger.info("SAT catálogos chicos ya estaban completos.")


def run_all_seeds(db: Session) -> None:
    """Punto de entrada único para tareas de startup."""
    run_backfill_ddl(db)
    seed_super_admin(db)
    seed_marcas(db)
    seed_sat_catalogos_pequenos(db)
    logger.info("Startup completado correctamente.")
