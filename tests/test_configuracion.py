def test_configuracion_accesible_para_cualquier_rol(asesor):
    resp = asesor.get("/configuracion/")

    assert resp.status_code == 200
    assert b"Configuraci\xc3\xb3n" in resp.data


def test_configuracion_requiere_login(client):
    resp = client.get("/configuracion/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"
