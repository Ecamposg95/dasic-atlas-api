"""El dashboard opera en días de calendario, no en instantes.

`ordenes_venta.fecha_creacion` y `fecha_vencimiento` son `DATE` desde
2026-08-06. El dashboard siguió tratándolas como `datetime` (`.tzinfo`,
`.date()`, resta contra `utcnow()`) y cinco endpoints devolvieron 500 en
producción durante semanas sin que ninguna prueba lo notara: no había ni una
sola prueba que tocara este router.

El barrido de abajo es el guardián de esa clase de fallo: recorre **todas** las
rutas GET del dashboard con datos reales en la base. Las pruebas siguientes
fijan la regla de negocio que el arreglo introduce: los días se cuentan contra
`hoy_negocio()`, así que una cotización que vence hoy está por vencer, no
vencida.
"""
from datetime import timedelta

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


def _rutas_get_dashboard():
    return sorted(
        path for metodo, path in _rutas_api()
        if metodo == "GET" and path.startswith("/api/dashboard/") and "{" not in path
    )


def test_el_barrido_ve_las_rutas_del_dashboard():
    """Guarda del guardián: si el filtro deja de encontrar rutas, el barrido
    de abajo pasaría vacío y en silencio."""
    rutas = _rutas_get_dashboard()
    assert len(rutas) >= 7, rutas
    assert "/api/dashboard/pipeline" in rutas
    assert "/api/dashboard/heatmap" in rutas


def test_ningun_endpoint_del_dashboard_revienta_con_datos(db, client_as):
    """Con cotizaciones nuevas, en seguimiento, por vencer, vencidas y sin
    vencimiento en la base, todos los GET del dashboard responden 200."""
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=5)
    _cotizacion(c, db, cli.id, creada_hace=3, vence_en=2)
    _cotizacion(c, db, cli.id, creada_hace=20, vence_en=-1)
    _cotizacion(c, db, cli.id, creada_hace=2, vence_en=None)

    fallos = []
    for ruta in _rutas_get_dashboard():
        try:
            r = c.get(ruta)
        except Exception as exc:  # noqa: BLE001 — se reporta cuál ruta y por qué
            fallos.append(f"{ruta} → {type(exc).__name__}: {exc}")
            continue
        if r.status_code != 200:
            fallos.append(f"{ruta} → {r.status_code}")
    assert not fallos, "\n".join(fallos)


def test_pipeline_clasifica_por_dias_de_calendario(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    nueva = _cotizacion(c, db, cli.id)
    seguimiento = _cotizacion(c, db, cli.id, creada_hace=5)
    vence_hoy = _cotizacion(c, db, cli.id, creada_hace=3, vence_en=0)
    vencida = _cotizacion(c, db, cli.id, creada_hace=20, vence_en=-1)
    sin_vencimiento = _cotizacion(c, db, cli.id, creada_hace=2, vence_en=None)

    r = c.get("/api/dashboard/pipeline")
    assert r.status_code == 200, r.text
    p = r.json()

    def ids(columna):
        return {i["id"] for i in p[columna]["items"]}

    def item(columna, oid):
        return next(i for i in p[columna]["items"] if i["id"] == oid)

    assert ids("nueva") == {nueva}
    assert ids("seguimiento") == {seguimiento, sin_vencimiento}
    assert ids("por_vencer") == {vence_hoy}
    assert ids("vencida") == {vencida}

    assert item("nueva", nueva)["edad_dias"] == 0
    assert item("nueva", nueva)["fecha"] == hoy_negocio().isoformat()
    assert item("por_vencer", vence_hoy)["dias_restantes"] == 0
    assert item("por_vencer", vence_hoy)["edad_dias"] == 3
    assert item("vencida", vencida)["dias_restantes"] == -1
    assert item("vencida", vencida)["edad_dias"] == 20
    assert item("seguimiento", sin_vencimiento)["dias_restantes"] is None


def test_alertas_por_vencer_abarca_de_hoy_a_tres_dias(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    hoy = _cotizacion(c, db, cli.id, vence_en=0)
    en_dos = _cotizacion(c, db, cli.id, vence_en=2)
    en_tres = _cotizacion(c, db, cli.id, vence_en=3)
    _cotizacion(c, db, cli.id, vence_en=4)
    _cotizacion(c, db, cli.id, vence_en=-1)

    r = c.get("/api/dashboard/alertas")
    assert r.status_code == 200, r.text
    dias = {i["id"]: i["dias_restantes"] for i in r.json()["por_vencer_3d"]}

    assert dias == {hoy: 0, en_dos: 2, en_tres: 3}


def test_heatmap_cuenta_por_dia_de_negocio(db, client_as):
    c = client_as("administrador")
    cli = _cliente(db)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id)
    _cotizacion(c, db, cli.id, creada_hace=3)
    _cotizacion(c, db, cli.id, creada_hace=10)  # fuera de la ventana de 7 días

    r = c.get("/api/dashboard/heatmap?dias=7")
    assert r.status_code == 200, r.text
    h = r.json()
    hoy = hoy_negocio()
    por_dia = {x["d"]: x["v"] for x in h["days"]}

    assert len(h["days"]) == 7
    assert h["days"][0]["d"] == (hoy - timedelta(days=6)).isoformat()
    assert h["days"][-1] == {"d": hoy.isoformat(), "v": 2}
    assert por_dia[(hoy - timedelta(days=3)).isoformat()] == 1
    assert h["total"] == 3
    assert h["max"] == 2


def test_el_vendedor_solo_ve_sus_cotizaciones_en_el_pipeline(db, client_as):
    admin = client_as("administrador")
    vendedor = client_as("ventas")
    cli = _cliente(db)
    _cotizacion(admin, db, cli.id)
    propia = _cotizacion(vendedor, db, cli.id)

    r = vendedor.get("/api/dashboard/pipeline")
    assert r.status_code == 200, r.text
    p = r.json()
    vistos = {i["id"] for columna in p.values() for i in columna["items"]}

    assert vistos == {propia}
