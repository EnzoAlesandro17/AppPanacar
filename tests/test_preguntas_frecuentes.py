def test_preguntas_frecuentes_accesible_para_cualquier_rol(asesor):
    resp = asesor.get("/preguntas-frecuentes/")

    assert resp.status_code == 200
    assert b"Preguntas frecuentes" in resp.data


def test_preguntas_frecuentes_requiere_login(client):
    resp = client.get("/preguntas-frecuentes/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"
