import pytest

from src.exceptions import ValidationError


@pytest.fixture
def usuario_creado(app):
    from src.modules.administrar.user.logic import crear_usuario

    crear_usuario(username="ana", password="clave-segura-123", role="Asesor")


def test_iniciar_sesion_con_credenciales_correctas(app, usuario_creado):
    from src.modules.administrar.user.logic import iniciar_sesion

    usuario = iniciar_sesion("ana", "clave-segura-123")

    assert usuario["username"] == "ana"


def test_iniciar_sesion_con_password_incorrecta_da_mensaje_generico(app, usuario_creado):
    from src.modules.administrar.user.logic import iniciar_sesion

    with pytest.raises(ValidationError, match="Usuario o contraseña incorrectos"):
        iniciar_sesion("ana", "password-incorrecta")


def test_iniciar_sesion_con_usuario_inexistente_da_el_mismo_mensaje_generico(app, usuario_creado):
    """No debe filtrar si falló el usuario o la contraseña (ver RODO.txt)."""
    from src.modules.administrar.user.logic import iniciar_sesion

    with pytest.raises(ValidationError, match="Usuario o contraseña incorrectos"):
        iniciar_sesion("no-existe", "cualquier-cosa")


def test_bloquea_la_cuenta_tras_max_intentos_fallidos(app, usuario_creado):
    from src.constants.settings import Settings
    from src.modules.administrar.user.logic import iniciar_sesion

    for _ in range(Settings.MAX_LOGIN_ATTEMPTS):
        with pytest.raises(ValidationError):
            iniciar_sesion("ana", "password-incorrecta")

    with pytest.raises(ValidationError, match="bloqueada temporalmente"):
        iniciar_sesion("ana", "clave-segura-123")


def test_usuario_borrado_no_puede_iniciar_sesion(app, usuario_creado):
    from src.modules.administrar.user.logic import borrar_usuario, iniciar_sesion, listar_usuarios

    id_usuario = listar_usuarios()[0]["id"]
    borrar_usuario(id_usuario)

    with pytest.raises(ValidationError, match="Usuario o contraseña incorrectos"):
        iniciar_sesion("ana", "clave-segura-123")


def test_login_http_exitoso_redirige_a_la_pantalla_principal(client, usuario_creado):
    from tests.conftest import extraer_csrf

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)

    resp = client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "ana", "password": "clave-segura-123"},
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_login_http_sin_csrf_token_devuelve_400(client, usuario_creado):
    resp = client.post("/usuarios/login", data={"username": "ana", "password": "clave-segura-123"})

    assert resp.status_code == 400


def test_sesion_de_un_dia_anterior_expira(client, usuario_creado):
    """login_required corta la sesión si login_date no es el día de hoy,
    aunque la cookie siga viva (corte por día calendario, no por inactividad)."""
    from tests.conftest import extraer_csrf

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "ana", "password": "clave-segura-123"},
    )

    with client.session_transaction() as sess:
        sess["login_date"] = "2000-01-01"

    resp = client.get("/", follow_redirects=True)

    assert b"Tu sesi\xc3\xb3n expir\xc3\xb3" in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_sesion_del_mismo_dia_sigue_activa(client, usuario_creado):
    from tests.conftest import extraer_csrf

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "ana", "password": "clave-segura-123"},
    )

    resp = client.get("/")

    assert resp.status_code == 200
