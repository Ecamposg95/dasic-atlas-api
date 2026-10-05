"""GET /api/superadmin/audit — fuentes sistema y stock."""
from app import models
from app.services import audit_service
from app.services.stock_service import aplicar_movimiento
from app.models.enums import TipoMovimientoStock


def _sembrar(db, usuario):
    u = usuario(rol="superadmin", email="root@test.local")
    audit_service.registrar(
        db, usuario=u, accion="eliminar", entidad="cliente",
        entidad_id=9, resumen="Eliminó cliente ACME",
    )
    p = models.Producto(sku="SKU-9", nombre="Válvula", stock_actual=10)
    db.add(p)
    db.commit()
    aplicar_movimiento(
        db, producto=p, tipo=TipoMovimientoStock.AJUSTE.value,
        cantidad=-3, motivo="merma", usuario=u,
    )
    db.commit()
    return u


def test_fuente_sistema_y_stock_aparecen(db, client_as, usuario):
    _sembrar(db, usuario)
    root = client_as("superadmin", email="root2@test.local")
    r = root.get("/api/superadmin/audit")
    assert r.status_code == 200
    fuentes = {e["fuente"] for e in r.json()["items"]}
    assert {"sistema", "stock"} <= fuentes


def test_filtro_fuente_stock(db, client_as, usuario):
    _sembrar(db, usuario)
    root = client_as("superadmin", email="root2@test.local")
    r = root.get("/api/superadmin/audit?fuente=stock")
    items = r.json()["items"]
    assert items and all(e["fuente"] == "stock" for e in items)
    assert any("merma" in e["detalle"] for e in items)


def test_filtro_usuario_aplica_a_fuentes_nuevas(db, client_as, usuario):
    u = _sembrar(db, usuario)
    root = client_as("superadmin", email="root2@test.local")
    r = root.get(f"/api/superadmin/audit?usuario_id={u.id}")
    items = r.json()["items"]
    assert items and all(e["usuario_id"] == u.id for e in items)
