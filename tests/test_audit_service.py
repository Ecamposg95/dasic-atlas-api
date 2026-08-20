"""Bitácora global de mutaciones (audit_log) — modelo y servicio."""
from app import models
from app.services import audit_service


def test_modelo_audit_log_persiste_con_defaults(db, usuario):
    u = usuario()
    db.add(models.AuditLog(
        usuario_id=u.id,
        accion="eliminar",
        entidad="cliente",
        entidad_id=123,
        resumen="Eliminó cliente ACME",
    ))
    db.commit()
    row = db.query(models.AuditLog).one()
    assert row.fecha is not None           # server_default
    assert row.datos is None
    assert (row.accion, row.entidad, row.entidad_id) == ("eliminar", "cliente", 123)


def test_registrar_participa_en_la_transaccion_del_caller(db, usuario):
    u = usuario()
    audit_service.registrar(
        db, usuario=u, accion="eliminar", entidad="cliente",
        entidad_id=1, resumen="x",
    )
    db.rollback()  # la mutación "falló": el evento debe irse con ella
    assert db.query(models.AuditLog).count() == 0

    audit_service.registrar(
        db, usuario=u, accion="eliminar", entidad="cliente",
        entidad_id=1, resumen="x",
    )
    db.commit()
    assert db.query(models.AuditLog).count() == 1


def test_registrar_serializa_datos_y_tolera_usuario_none(db):
    audit_service.registrar(
        db, usuario=None, accion="cambio_precio", entidad="producto",
        entidad_id=5, resumen="r" * 500,  # se trunca a 400
        datos={"costo_compra": {"antes": "10.00", "despues": "12.50"}},
    )
    db.commit()
    row = db.query(models.AuditLog).one()
    assert row.usuario_id is None
    assert len(row.resumen) == 400
    assert '"antes": "10.00"' in row.datos
