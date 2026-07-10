from src.modules.administrar.bitacora.logic import listar_eventos, registrar_evento
from src.modules.administrar.user.logic import crear_usuario
from tests.conftest import extraer_csrf


def _login(client, username, password="clave-segura-123"):
    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    return client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": username, "password": password},
        follow_redirects=True,
    )


def test_registrar_y_listar_eventos(app):
    registrar_evento(
        user_id=None, username="ana", ip_address="127.0.0.1", method="POST",
        path="/clientes/nuevo", category="success", message="Cliente creado.",
    )
    registrar_evento(
        user_id=None, username="ana", ip_address="127.0.0.1", method="POST",
        path="/clientes/nuevo", category="success", message="Otro cliente creado.",
    )

    eventos = listar_eventos()

    assert len(eventos) == 2
    assert eventos[0]["message"] == "Otro cliente creado."


def test_login_exitoso_queda_registrado(app, client):
    crear_usuario(username="pedro", password="clave-segura-123", role="IT")

    _login(client, "pedro")

    eventos = listar_eventos()
    assert any(
        e["username"] == "pedro" and e["category"] == "success" and "Inicio de sesión" in e["message"]
        for e in eventos
    )


def test_login_fallido_queda_registrado_sin_user_id(app, client):
    crear_usuario(username="pedro", password="clave-segura-123", role="IT")

    _login(client, "pedro", password="incorrecta")

    eventos = listar_eventos()
    evento = next(e for e in eventos if e["category"] == "error")
    assert evento["user_id"] is None
    assert evento["username"] == "pedro"


def test_logout_queda_registrado(client):
    crear_usuario(username="pedro", password="clave-segura-123", role="IT")
    _login(client, "pedro")

    client.get("/usuarios/logout")

    eventos = listar_eventos()
    assert any(e["message"] == "Cierre de sesión." for e in eventos)


def test_crear_cliente_exitoso_queda_registrado(admin):
    resp = admin.get("/clientes/nuevo")
    token = extraer_csrf(resp.data)
    admin.post(
        "/clientes/nuevo",
        data={"csrf_token": token, "name": "Ana", "last_name": "Gomez", "dni_cuit": "30111470"},
        follow_redirects=True,
    )

    eventos = listar_eventos()
    assert any(e["message"] == "Cliente creado." and e["category"] == "success" for e in eventos)


def test_intento_sin_permiso_queda_registrado(asesor):
    asesor.get("/sucursales/", follow_redirects=True)

    eventos = listar_eventos()
    assert any("No tenés permiso para acceder a Administración" in (e["message"] or "") for e in eventos)


def test_it_puede_ver_bitacora(admin):
    resp = admin.get("/bitacora/")

    assert resp.status_code == 200


def test_backoffice_no_puede_ver_bitacora(backoffice):
    resp = backoffice.get("/bitacora/", follow_redirects=True)

    assert "No tenés permiso para ver la bitácora.".encode() in resp.data


def test_asesor_no_puede_ver_bitacora(asesor):
    """Asesor ni siquiera llega a la vista: antes lo frena restringir_a_administracion
    (antes de request), que ya bloquea toda Administración."""
    resp = asesor.get("/bitacora/", follow_redirects=True)

    assert "No tenés permiso para acceder a Administración.".encode() in resp.data


def test_tile_bitacora_solo_para_it(app):
    """admin/backoffice comparten el mismo test client si se piden juntos como
    fixtures (el segundo login pisa la sesión del primero); acá se usan dos
    clients independientes a propósito."""
    cliente_it = app.test_client()
    crear_usuario(username="it_tile", password="clave-segura-123", role="IT")
    _login(cliente_it, "it_tile")

    cliente_backoffice = app.test_client()
    crear_usuario(username="backoffice_tile", password="clave-segura-123", role="BackOffice")
    _login(cliente_backoffice, "backoffice_tile")

    resp = cliente_it.get("/administracion/")
    assert b"Bit\xc3\xa1cora" in resp.data

    resp = cliente_backoffice.get("/administracion/")
    assert b"Bit\xc3\xa1cora" not in resp.data
