def test_contabilidad_accesible_para_admin(admin):
    resp = admin.get("/contabilidad/")

    assert resp.status_code == 200
    assert b"Contabilidad" in resp.data


def test_contabilidad_bloqueada_para_asesor(asesor):
    resp = asesor.get("/contabilidad/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_contabilidad_requiere_login(client):
    resp = client.get("/contabilidad/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"
