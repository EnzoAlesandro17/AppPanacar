from tests.conftest import extraer_csrf


def test_configuracion_accesible_para_cualquier_rol(asesor):
    resp = asesor.get("/configuracion/")

    assert resp.status_code == 200
    assert b"Configuraci\xc3\xb3n" in resp.data


def test_configuracion_requiere_login(client):
    resp = client.get("/configuracion/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"


def test_tema_por_defecto_es_claro(asesor):
    resp = asesor.get("/")

    assert b'data-theme="light"' in resp.data


def test_configuracion_cambia_el_tema_a_oscuro(asesor):
    resp = asesor.get("/configuracion/")
    token = extraer_csrf(resp.data)

    resp = asesor.post(
        "/configuracion/", data={"csrf_token": token, "theme": "dark"}, follow_redirects=True,
    )

    assert b"Tema actualizado" in resp.data

    resp = asesor.get("/")
    assert b'data-theme="dark"' in resp.data


def test_configuracion_rechaza_tema_invalido(asesor):
    resp = asesor.get("/configuracion/")
    token = extraer_csrf(resp.data)

    resp = asesor.post(
        "/configuracion/", data={"csrf_token": token, "theme": "neon"}, follow_redirects=True,
    )

    assert b"debe ser uno de" in resp.data
    resp = asesor.get("/")
    assert b'data-theme="light"' in resp.data


def test_configuracion_post_requiere_login(client):
    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)

    resp = client.post(
        "/configuracion/", data={"csrf_token": token, "theme": "dark"}, follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"
