"""Interruptor de acceso: suspender y reactivar la plataforma.

Estas pruebas se autentican DE VERDAD (cookie emitida por el login), sin el
override de `get_current_user` que usa `client_as`: el corte vive justo en esa
dependencia, así que overridearla lo saltaría y las pruebas pasarían en falso.
"""
import pytest
from starlette.testclient import TestClient

from app import models
from app.db import get_db
from app.main import app
from app.models.enums import RolUsuario
from app.services import UserService, acceso_service

CONTRASENA = "Contrasena#123"
RUTA_PROTEGIDA = "/api/auth/me"


@pytest.fixture()
def nuevo_cliente(db):
    """Factory de TestClient: cada uno con su propio tarro de cookies."""
    app.dependency_overrides[get_db] = lambda: db
    yield lambda: TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def crear_usuario(db):
    def _make(rol, email):
        u = models.Usuario(
            nombre=f"Test {email}",
            email=email,
            password_hash=UserService.get_password_hash(CONTRASENA),
            rol=rol,
            activo=True,
        )
        db.add(u)
        db.commit()
        return u
    return _make


def _login(client, email):
    return client.post("/api/auth/login", data={"username": email, "password": CONTRASENA})


@pytest.fixture()
def escenario(nuevo_cliente, crear_usuario):
    """Un superadmin y un administrador del cliente, ambos con sesión abierta."""
    crear_usuario(RolUsuario.SUPERADMIN, "dev@atlas.test")
    crear_usuario(RolUsuario.ADMINISTRADOR, "admin@dasic.test")
    sa, cliente = nuevo_cliente(), nuevo_cliente()
    assert _login(sa, "dev@atlas.test").status_code == 200
    assert _login(cliente, "admin@dasic.test").status_code == 200
    return sa, cliente


def _suspender(sa, **extra):
    return sa.put("/api/superadmin/acceso", json={"suspendida": True, **extra})


def _reactivar(sa):
    return sa.put("/api/superadmin/acceso", json={"suspendida": False})


def test_por_defecto_la_plataforma_esta_activa(escenario):
    sa, cliente = escenario
    assert cliente.get(RUTA_PROTEGIDA).status_code == 200
    estado = sa.get("/api/superadmin/acceso").json()
    assert estado["suspendida"] is False
    assert estado["usuarios_afectados"] == 1  # el superadmin no cuenta


def test_suspender_corta_la_sesion_ya_abierta(escenario):
    sa, cliente = escenario
    assert _suspender(sa).status_code == 200

    r = cliente.get(RUTA_PROTEGIDA)
    assert r.status_code == 423
    assert r.headers[acceso_service.HEADER_SUSPENDIDA] == "1"
    assert r.json()["detail"] == acceso_service.MENSAJE_DEFAULT
    # No es solo /me: cualquier endpoint autenticado queda cerrado.
    assert cliente.get("/api/dashboard/kpis").status_code == 423


def test_suspendida_no_deja_iniciar_sesion_ni_emite_cookie(escenario, nuevo_cliente):
    sa, _ = escenario
    _suspender(sa)

    otro = nuevo_cliente()
    r = _login(otro, "admin@dasic.test")
    assert r.status_code == 423
    assert "set-cookie" not in r.headers


def test_suspendida_no_revela_el_estado_con_credenciales_malas(escenario, nuevo_cliente):
    sa, _ = escenario
    _suspender(sa)

    r = nuevo_cliente().post(
        "/api/auth/login", data={"username": "admin@dasic.test", "password": "mala"}
    )
    assert r.status_code == 401


def test_el_superadmin_nunca_queda_fuera(escenario, nuevo_cliente):
    sa, _ = escenario
    _suspender(sa)

    assert sa.get(RUTA_PROTEGIDA).status_code == 200
    assert _login(nuevo_cliente(), "dev@atlas.test").status_code == 200
    assert sa.get("/api/superadmin/acceso").json()["suspendida"] is True


def test_reactivar_devuelve_el_acceso_sin_volver_a_entrar(escenario):
    sa, cliente = escenario
    _suspender(sa)
    assert cliente.get(RUTA_PROTEGIDA).status_code == 423

    assert _reactivar(sa).status_code == 200
    assert cliente.get(RUTA_PROTEGIDA).status_code == 200


def test_mensaje_personalizado_llega_al_usuario_y_se_puede_restaurar(escenario):
    sa, cliente = escenario
    _suspender(sa, mensaje="  Servicio suspendido por falta de pago.  ")
    assert cliente.get(RUTA_PROTEGIDA).json()["detail"] == "Servicio suspendido por falta de pago."

    # mensaje omitido = no tocar el que ya estaba
    _suspender(sa)
    assert cliente.get(RUTA_PROTEGIDA).json()["detail"] == "Servicio suspendido por falta de pago."

    # mensaje vacío = volver al default
    _suspender(sa, mensaje="")
    assert cliente.get(RUTA_PROTEGIDA).json()["detail"] == acceso_service.MENSAJE_DEFAULT


def test_mensaje_demasiado_largo_se_rechaza(escenario):
    sa, _ = escenario
    r = _suspender(sa, mensaje="x" * (acceso_service.MENSAJE_MAX + 1))
    assert r.status_code == 400
    assert sa.get("/api/superadmin/acceso").json()["suspendida"] is False


@pytest.mark.parametrize("rol", [RolUsuario.ADMINISTRADOR, RolUsuario.GERENTE_COMERCIAL, RolUsuario.VENTAS])
def test_solo_el_superadmin_mueve_el_interruptor(nuevo_cliente, crear_usuario, rol):
    crear_usuario(rol, "alguien@dasic.test")
    c = nuevo_cliente()
    assert _login(c, "alguien@dasic.test").status_code == 200
    assert c.get("/api/superadmin/acceso").status_code == 403
    assert c.put("/api/superadmin/acceso", json={"suspendida": False}).status_code == 403


def test_sin_sesion_el_interruptor_responde_401(nuevo_cliente):
    c = nuevo_cliente()
    assert c.get("/api/superadmin/acceso").status_code == 401
    assert c.put("/api/superadmin/acceso", json={"suspendida": True}).status_code == 401


def test_cada_cambio_queda_en_la_bitacora_y_los_repetidos_no(escenario, db):
    sa, _ = escenario
    _suspender(sa)
    _suspender(sa)  # sin cambio de estado: no debe duplicar el evento
    _reactivar(sa)

    eventos = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.entidad == "plataforma")
        .order_by(models.AuditLog.id)
        .all()
    )
    assert [e.accion for e in eventos] == ["suspender", "reactivar"]
