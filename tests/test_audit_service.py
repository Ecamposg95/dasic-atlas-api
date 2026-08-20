"""Bitácora global de mutaciones (audit_log) — modelo y servicio."""
from app import models


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
