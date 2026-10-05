"""Widget "última cotización de este cliente" del cotizador.

Devolvió 500 en producción desde que `fecha_creacion` pasó a `DATE`: el
endpoint le pedía `.tzinfo` a un `date` y luego lo restaba de `utcnow()`.
Fue el más golpeado de los cinco (332 de 859 errores en cuatro semanas),
porque se consulta cada vez que alguien elige un cliente en el cotizador.

Además del 500, `DATE` trajo un empate que antes no existía: dos cotizaciones
del mismo cliente el mismo día tienen la misma fecha, así que "la última"
necesita desempatar por id.
"""
from datetime import timedelta

from app import models
from app.core.fechas import hoy_negocio


def _cliente(db, nombre="ACME"):
    c = models.Cliente(nombre_empresa=nombre)
    db.add(c)
    db.commit()
    return c


def _cotizacion(client, db, cliente_id, *, creada_hace=0):
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
    data = r.json()
    orden = db.get(models.OrdenVenta, data["id"])
    orden.fecha_creacion = hoy_negocio() - timedelta(days=creada_hace)
    db.commit()
    return data


def test_cliente_sin_cotizaciones_devuelve_null(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    assert r.json() is None


def test_cotizacion_de_hoy_tiene_cero_dias(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    cot = _cotizacion(c, db, cli.id)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == cot["id"]
    assert data["folio"] == cot["folio"]
    assert data["fecha"] == hoy_negocio().isoformat()
    assert data["dias_atras"] == 0
    assert data["moneda"] == "MXN"


def test_dias_atras_cuenta_dias_de_calendario(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id, creada_hace=3)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    assert r.json()["dias_atras"] == 3


def test_dos_cotizaciones_el_mismo_dia_gana_la_mas_reciente(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    segunda = _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=4)

    r = c.get(f"/api/ventas/ultima-cotizacion-cliente/{cli.id}")

    assert r.status_code == 200, r.text
    assert r.json()["id"] == segunda["id"]
