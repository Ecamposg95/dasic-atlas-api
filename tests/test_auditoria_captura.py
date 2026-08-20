"""La captura de auditoría en los routers: deletes y ediciones sensibles."""
from decimal import Decimal

from app import models


def _cliente(db, nombre="ACME Industrial"):
    c = models.Cliente(nombre_empresa=nombre, rfc_tax_id="AAA010101AAA")
    db.add(c)
    db.commit()
    return c


def test_eliminar_cliente_registra_auditoria(db, client_as):
    c = _cliente(db)
    admin = client_as("administrador")
    r = admin.delete(f"/api/clientes/{c.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad, ev.entidad_id) == ("eliminar", "cliente", c.id)
    assert "ACME Industrial" in ev.resumen
    assert ev.usuario_id == admin.user.id


def test_eliminar_cliente_bloqueado_no_registra(db, client_as):
    c = _cliente(db)
    db.add(models.OrdenVenta(folio="C-X-1", cliente_id=c.id))
    db.commit()
    admin = client_as("administrador")
    r = admin.delete(f"/api/clientes/{c.id}")
    assert r.status_code == 409
    assert db.query(models.AuditLog).count() == 0


def test_eliminar_contacto_registra_auditoria(db, client_as):
    c = _cliente(db)
    contacto = models.Contacto(cliente_id=c.id, nombre="Juan Pérez", cargo="Compras")
    db.add(contacto)
    db.commit()
    admin = client_as("administrador")
    r = admin.delete(f"/api/clientes/{c.id}/contactos/{contacto.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad) == ("eliminar", "contacto")
    assert "Juan Pérez" in ev.resumen


def _producto(db, **kw):
    defaults = dict(sku="SKU-1", nombre="Bomba X", costo_compra=Decimal("100.00"),
                    moneda_compra="MXN", precio_publico=Decimal("150.00"))
    defaults.update(kw)
    p = models.Producto(**defaults)
    db.add(p)
    db.commit()
    return p


def test_cambio_de_costo_registra_diff(db, client_as):
    p = _producto(db)
    admin = client_as("administrador")
    r = admin.put(f"/api/productos/{p.id}", json={"costo_compra": 120.5})
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad, ev.entidad_id) == ("cambio_precio", "producto", p.id)
    assert '"antes": "100.00"' in ev.datos and '"despues": "120.5' in ev.datos


def test_update_sin_cambio_de_precio_no_registra(db, client_as):
    p = _producto(db)
    admin = client_as("administrador")
    r = admin.put(f"/api/productos/{p.id}", json={"nombre": "Bomba X v2", "costo_compra": 100.0})
    assert r.status_code == 200
    assert db.query(models.AuditLog).count() == 0


def test_eliminar_producto_registra_auditoria(db, client_as):
    p = _producto(db)
    admin = client_as("administrador")
    r = admin.delete(f"/api/productos/{p.id}")
    assert r.status_code == 200
    ev = db.query(models.AuditLog).one()
    assert (ev.accion, ev.entidad) == ("eliminar", "producto")
    assert "SKU-1" in ev.resumen
