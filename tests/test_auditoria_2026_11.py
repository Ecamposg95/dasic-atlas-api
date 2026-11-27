"""Regresiones de la auditoría de noviembre 2026.

Cada prueba fija un error encontrado al revisar el proyecto completo: el
comportamiento esperado va descrito en el nombre y el valor esperado está
derivado a mano en el comentario de al lado.
"""
from datetime import date
from decimal import Decimal

from app import models
from app.db.seeds import seed_default_pipeline
from app.models.crm import Deal, DealActividad, PipelineStage
from app.models.enums import TipoMovimiento


def _cliente(db, saldo="0"):
    c = models.Cliente(nombre_empresa="ACME", saldo_actual=Decimal(saldo))
    db.add(c)
    db.commit()
    return c


# ---------------------------------------------------------------------------
# Cobranza: el pago desde "Estado de cuenta" debe liquidar los cargos
# ---------------------------------------------------------------------------
def test_pago_distribuido_liquida_el_cargo_y_devuelve_el_saldo(db, client_as):
    cliente = _cliente(db, saldo="1000")
    cargo = models.TransaccionCliente(
        cliente_id=cliente.id,
        tipo=TipoMovimiento.CARGO,
        monto=Decimal("1000"),
        monto_pagado=Decimal("0"),
        estatus_pago="pendiente",
        descripcion="Venta",
    )
    db.add(cargo)
    db.commit()

    client = client_as("administrador")
    r = client.post(
        f"/api/clientes/{cliente.id}/pago-distribuido",
        json={"monto": 1000, "descripcion": "Abono a cuenta"},
    )
    assert r.status_code == 200, r.text
    # 1000 de deuda − 1000 de pago = 0
    assert Decimal(str(r.json()["nuevo_saldo"])) == Decimal("0")

    db.expire_all()
    cargo = db.get(models.TransaccionCliente, cargo.id)
    assert cargo.monto_pagado == Decimal("1000")
    assert cargo.estatus_pago == "pagado"


# ---------------------------------------------------------------------------
# CRM: cambiar la etapa desde el formulario cierra (o reabre) el deal
# ---------------------------------------------------------------------------
def _deal(db, client):
    seed_default_pipeline(db)
    db.commit()
    stages = db.query(PipelineStage).order_by(PipelineStage.orden).all()
    abierta = next(s for s in stages if not s.es_ganado and not s.es_perdido)
    ganada = next(s for s in stages if s.es_ganado)
    r = client.post(
        "/api/crm/deals",
        json={"pipeline_id": abierta.pipeline_id, "titulo": "Bomba", "stage_id": abierta.id},
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"], abierta, ganada


def test_patch_a_etapa_ganada_cierra_el_deal_y_deja_rastro(db, client_as):
    client = client_as("ventas")
    deal_id, _abierta, ganada = _deal(db, client)

    r = client.patch(f"/api/crm/deals/{deal_id}", json={"titulo": "Bomba 2", "stage_id": ganada.id})
    assert r.status_code == 200, r.text

    db.expire_all()
    deal = db.get(Deal, deal_id)
    assert deal.titulo == "Bomba 2"
    assert deal.stage_id == ganada.id
    assert deal.cerrado_en is not None
    movimientos = (
        db.query(DealActividad)
        .filter(DealActividad.deal_id == deal_id, DealActividad.tipo == "sistema")
        .filter(DealActividad.descripcion == f"Movido a {ganada.nombre}")
        .count()
    )
    assert movimientos == 1


def test_patch_de_vuelta_a_etapa_abierta_reabre_el_deal(db, client_as):
    client = client_as("ventas")
    deal_id, abierta, ganada = _deal(db, client)
    client.patch(f"/api/crm/deals/{deal_id}", json={"stage_id": ganada.id})

    r = client.patch(f"/api/crm/deals/{deal_id}", json={"stage_id": abierta.id})
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(Deal, deal_id).cerrado_en is None


def test_patch_sin_cambio_de_etapa_no_toca_el_cierre(db, client_as):
    client = client_as("ventas")
    deal_id, abierta, _ganada = _deal(db, client)

    r = client.patch(f"/api/crm/deals/{deal_id}", json={"titulo": "Otro", "stage_id": abierta.id})
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(Deal, deal_id).cerrado_en is None
    assert db.query(DealActividad).filter(
        DealActividad.deal_id == deal_id, DealActividad.descripcion.like("Movido a%")
    ).count() == 0


def test_patch_a_etapa_inexistente_responde_404(db, client_as):
    client = client_as("ventas")
    deal_id, _abierta, _ganada = _deal(db, client)
    r = client.patch(f"/api/crm/deals/{deal_id}", json={"stage_id": 999999})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Cotizador: las fechas capturadas se respetan desde el primer guardado
# ---------------------------------------------------------------------------
def _cotizacion(cliente_id, **extra):
    base = {
        "cliente_id": cliente_id,
        "moneda": "MXN",
        "detalles": [
            {
                "cantidad": "1",
                "utilidad": "0",
                "descuento": "0",
                "costo_unitario": "100",
                "descripcion_libre": "Línea de prueba",
                "tipo_linea": "producto_fantasma",
            }
        ],
    }
    base.update(extra)
    return base


def test_crear_cotizacion_respeta_las_fechas_enviadas(db, client_as):
    cliente = _cliente(db)
    client = client_as("ventas")
    r = client.post(
        "/api/ventas/",
        json=_cotizacion(cliente.id, fecha_creacion="2026-10-01", fecha_vencimiento="2026-12-31"),
    )
    assert r.status_code in (200, 201), r.text
    db.expire_all()
    orden = db.get(models.OrdenVenta, r.json()["id"])
    assert orden.fecha_creacion == date(2026, 10, 1)
    assert orden.fecha_vencimiento == date(2026, 12, 31)


def test_crear_cotizacion_sin_fechas_usa_hoy_y_la_vigencia(db, client_as):
    from app.core.fechas import hoy_negocio

    cliente = _cliente(db)
    client = client_as("ventas")
    r = client.post("/api/ventas/", json=_cotizacion(cliente.id))
    assert r.status_code in (200, 201), r.text
    db.expire_all()
    orden = db.get(models.OrdenVenta, r.json()["id"])
    assert orden.fecha_creacion == hoy_negocio()
    assert orden.fecha_vencimiento > hoy_negocio()


# ---------------------------------------------------------------------------
# Fantasmas: vaciar un campo opcional lo vacía de verdad
# ---------------------------------------------------------------------------
def test_editar_fantasma_permite_vaciar_campos_opcionales(db, client_as):
    prov = models.Proveedor(nombre_empresa="Proveedor X")
    db.add(prov)
    db.flush()
    f = models.ProductoFantasma(
        descripcion_original="Válvula",
        descripcion_normalizada="válvula",
        costo_referencia=Decimal("10"),
        moneda_referencia="MXN",
        proveedor_sugerido_id=prov.id,
        observaciones="nota vieja",
        estado="PENDIENTE",
    )
    db.add(f)
    db.commit()

    client = client_as("administrador")
    r = client.patch(
        f"/api/fantasmas/{f.id}",
        json={"proveedor_sugerido_id": None, "observaciones": None},
    )
    assert r.status_code == 200, r.text
    db.expire_all()
    f = db.get(models.ProductoFantasma, f.id)
    assert f.proveedor_sugerido_id is None
    assert f.observaciones is None
    # Lo que no se envió no cambia.
    assert f.descripcion_original == "Válvula"


def test_registrar_pago_simple_tambien_liquida_el_cargo(db, client_as):
    cliente = _cliente(db, saldo="116")
    cargo = models.TransaccionCliente(
        cliente_id=cliente.id,
        tipo=TipoMovimiento.CARGO,
        monto=Decimal("116"),
        monto_pagado=Decimal("0"),
        estatus_pago="pendiente",
        descripcion="Venta",
    )
    db.add(cargo)
    db.commit()

    client = client_as("administrador")
    r = client.post(f"/api/clientes/{cliente.id}/registrar-pago?monto=116&descripcion=Abono")
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(models.TransaccionCliente, cargo.id).estatus_pago == "pagado"
    assert db.get(models.Cliente, cliente.id).saldo_actual == Decimal("0")  # 116 − 116


def test_pago_distribuido_con_monto_no_numerico_responde_400(db, client_as):
    cliente = _cliente(db)
    client = client_as("administrador")
    for malo in ("abc", "NaN"):
        r = client.post(f"/api/clientes/{cliente.id}/pago-distribuido", json={"monto": malo})
        assert r.status_code == 400, (malo, r.text)


# ---------------------------------------------------------------------------
# Folios: una cotización convertida no libera su número
# ---------------------------------------------------------------------------
def test_convertir_no_provoca_folio_repetido(db, client_as):
    cliente = _cliente(db)
    client = client_as("administrador")

    primera = client.post("/api/ventas/", json=_cotizacion(cliente.id)).json()
    r = client.post(f"/api/ventas/{primera['id']}/convertir")
    assert r.status_code == 200, r.text

    # La primera ya es V-…001: la siguiente cotización debe ser …002, no …001.
    segunda = client.post("/api/ventas/", json=_cotizacion(cliente.id)).json()
    assert segunda["folio"][-3:] == "002"
    r = client.post(f"/api/ventas/{segunda['id']}/convertir")
    assert r.status_code == 200, r.text

    folios = [o.folio for o in db.query(models.OrdenVenta).all()]
    assert len(folios) == len(set(folios)) == 2


def test_no_se_puede_crear_una_orden_ya_pagada_o_cancelada(db, client_as):
    cliente = _cliente(db)
    client = client_as("administrador")
    for estatus in ("pagada", "cancelada"):
        r = client.post(f"/api/ventas/?tipo_orden={estatus}", json=_cotizacion(cliente.id))
        assert r.status_code == 400, (estatus, r.text)
    assert db.query(models.OrdenVenta).count() == 0


# ---------------------------------------------------------------------------
# Auto-OC: sugerir y generar no truenan con cantidades Decimal
# ---------------------------------------------------------------------------
def test_sugerir_y_generar_oc_con_faltante(db, client_as):
    cliente = _cliente(db)
    prov = models.Proveedor(nombre_empresa="Proveedor X")
    db.add(prov)
    db.flush()
    prod = models.Producto(
        sku="P-1", sku_comercial="P-1", nombre="Bomba", costo_compra=Decimal("100"),
        moneda_compra="MXN", stock_actual=0, proveedor_principal_id=prov.id,
    )
    db.add(prod)
    db.commit()

    client = client_as("administrador")
    cot = client.post("/api/ventas/", json={
        "cliente_id": cliente.id,
        "moneda": "MXN",
        "detalles": [{
            "producto_id": prod.id, "cantidad": "2", "utilidad": "10", "descuento": "0",
            "tipo_linea": "producto_catalogo",
        }],
    })
    assert cot.status_code in (200, 201), cot.text
    cot_id = cot.json()["id"]

    r = client.post(f"/api/ventas/{cot_id}/sugerir-oc")
    assert r.status_code == 200, r.text
    grupo = r.json()["por_proveedor"][0]
    assert grupo["subtotal"] == 200.0  # faltan 2 × 100

    r = client.post(f"/api/ventas/{cot_id}/generar-oc")
    assert r.status_code == 200, r.text
    oc = db.query(models.OrdenCompra).one()
    assert oc.total == Decimal("200")


# ---------------------------------------------------------------------------
# Usuarios desactivados: ni sesión nueva ni uso de la que ya tenían
# ---------------------------------------------------------------------------
def test_usuario_desactivado_pierde_el_acceso(db):
    from starlette.testclient import TestClient

    from app.db import get_db
    from app.main import app
    from app.models.enums import RolUsuario
    from app.services import UserService

    u = models.Usuario(
        nombre="Ex empleado",
        email="ex@dasic.test",
        password_hash=UserService.get_password_hash("Contrasena#123"),
        rol=RolUsuario.ADMINISTRADOR,
        activo=True,
    )
    db.add(u)
    db.commit()

    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        credenciales = {"username": "ex@dasic.test", "password": "Contrasena#123"}
        assert client.post("/api/auth/login", data=credenciales).status_code == 200
        assert client.get("/api/clientes/").status_code == 200

        u.activo = False
        db.commit()

        # La sesión abierta deja de servir en cualquier endpoint, no solo en /me.
        assert client.get("/api/clientes/").status_code == 403
        # Y no puede abrir otra.
        nuevo = TestClient(app)
        assert nuevo.post("/api/auth/login", data=credenciales).status_code == 403
    finally:
        app.dependency_overrides.clear()
