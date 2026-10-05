"""Los reportes operan en días de calendario, no en instantes.

`ordenes_venta.fecha_creacion` y `fecha_vencimiento` son `DATE` desde
2026-08-06. Tres endpoints de reportes siguieron tratándolas como `datetime`
(`vencimientos-proximos`, `conversion-cotizaciones` y
`ordenes-pendientes-entrega`) y devolvían 500 en cuanto había datos; ninguna
prueba tocaba este router. Mismo enfoque que `test_dashboard_fechas.py`: un
barrido de todos los GET con datos reales y pruebas de la regla de negocio.
"""
from datetime import datetime, time, timedelta, timezone

from app import models
from app.core.fechas import hoy_negocio
from tests.test_endpoints_autenticacion import _rutas_api


def _cliente(db, nombre="ACME"):
    c = models.Cliente(nombre_empresa=nombre)
    db.add(c)
    db.commit()
    return c


def _cotizacion(client, db, cliente_id, *, creada_hace=0, vence_en=15):
    """Crea una cotización por la API y le fija sus dos fechas de calendario.

    `creada_hace`: días atrás respecto a hoy. `vence_en`: días hacia adelante
    (negativo = ya venció; `None` = sin fecha de vencimiento). Devuelve el id.
    """
    r = client.post("/api/ventas/", json={
        "cliente_id": cliente_id,
        "moneda": "MXN",
        "detalles": [{
            "cantidad": "1", "utilidad": "0", "descuento": "0",
            "costo_unitario": "100", "descripcion_libre": "Línea",
            "tipo_linea": "producto_fantasma",
        }],
    })
    assert r.status_code in (200, 201), r.text
    oid = r.json()["id"]
    hoy = hoy_negocio()
    orden = db.get(models.OrdenVenta, oid)
    orden.fecha_creacion = hoy - timedelta(days=creada_hace)
    orden.fecha_vencimiento = None if vence_en is None else hoy + timedelta(days=vence_en)
    db.commit()
    return oid


def _orden_convertida(client, db, cliente_id, *, creada_hace=6):
    """Cotización convertida: estatus PENDIENTE, creada hace N días y
    actualizada a mediodía (CDMX) de hoy. 18:00 UTC es mediodía en CDMX todo
    el año, así que el día de negocio no depende de la hora en que corra."""
    oid = _cotizacion(client, db, cliente_id, creada_hace=creada_hace)
    orden = db.get(models.OrdenVenta, oid)
    orden.estatus = models.EstatusOrden.PENDIENTE
    orden.actualizado_en = datetime.combine(hoy_negocio(), time(18, 0), tzinfo=timezone.utc)
    db.commit()
    return oid


def _rutas_get_reportes():
    return sorted(
        path for metodo, path in _rutas_api()
        if metodo == "GET" and path.startswith("/api/reportes/") and "{" not in path
    )


def test_el_barrido_ve_las_rutas_de_reportes():
    """Guarda del guardián: si el filtro deja de encontrar rutas, el barrido
    de abajo pasaría vacío y en silencio."""
    rutas = _rutas_get_reportes()
    assert len(rutas) >= 8, rutas
    assert "/api/reportes/vencimientos-proximos" in rutas
    assert "/api/reportes/conversion-cotizaciones" in rutas
    assert "/api/reportes/ordenes-pendientes-entrega" in rutas


def test_ningun_endpoint_de_reportes_revienta_con_datos(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=5)
    _cotizacion(c, db, cli.id, creada_hace=3, vence_en=2)
    _cotizacion(c, db, cli.id, creada_hace=20, vence_en=-1)
    _cotizacion(c, db, cli.id, creada_hace=2, vence_en=None)
    _orden_convertida(c, db, cli.id)

    fallos = []
    for ruta in _rutas_get_reportes():
        try:
            r = c.get(ruta)
        except Exception as exc:  # noqa: BLE001 — se reporta cuál ruta y por qué
            fallos.append(f"{ruta} → {type(exc).__name__}: {exc}")
            continue
        if r.status_code != 200:
            fallos.append(f"{ruta} → {r.status_code}")
    assert not fallos, "\n".join(fallos)


def test_vencimientos_proximos_cuenta_dias_de_calendario(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    hoy = _cotizacion(c, db, cli.id, vence_en=0)
    en_dos = _cotizacion(c, db, cli.id, vence_en=2)
    en_14 = _cotizacion(c, db, cli.id, vence_en=14)
    _cotizacion(c, db, cli.id, vence_en=15)
    _cotizacion(c, db, cli.id, vence_en=-1)

    r = c.get("/api/reportes/vencimientos-proximos")
    assert r.status_code == 200, r.text
    dias = {i["id"]: i["dias_restantes"] for i in r.json()["items"]}

    assert dias == {hoy: 0, en_dos: 2, en_14: 14}


def test_ordenes_pendientes_entrega_cuenta_dias_desde_la_creacion(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    oid = _orden_convertida(c, db, cli.id, creada_hace=6)

    r = c.get("/api/reportes/ordenes-pendientes-entrega")
    assert r.status_code == 200, r.text
    items = r.json()["items"]

    assert [i["id"] for i in items] == [oid]
    assert items[0]["dias_desde_venta"] == 6
    assert items[0]["fecha_creacion"] == (hoy_negocio() - timedelta(days=6)).isoformat()


def test_conversion_cotizaciones_mide_el_tiempo_en_dias(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _orden_convertida(c, db, cli.id, creada_hace=6)

    r = c.get("/api/reportes/conversion-cotizaciones")
    assert r.status_code == 200, r.text

    assert r.json()["tiempo_medio_conversion_dias"] == 6.0
