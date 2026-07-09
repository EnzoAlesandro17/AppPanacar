def test_contabilidad_accesible_para_cualquier_rol(asesor):
    resp = asesor.get("/contabilidad/")

    assert resp.status_code == 200
    assert b"Contabilidad" in resp.data


def test_contabilidad_requiere_login(client):
    resp = client.get("/contabilidad/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"
