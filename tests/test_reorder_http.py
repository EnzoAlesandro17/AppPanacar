import json

from tests.conftest import extraer_csrf, extraer_csrf_meta


def _crear_sucursal(admin, nombre):
    resp = admin.get("/branches/nuevo")
    token = extraer_csrf(resp.data)
    admin.post("/branches/nuevo", data={"csrf_token": token, "name": nombre}, follow_redirects=True)


def test_reordenar_por_http_aplica_el_nuevo_orden(admin):
    from src.modules.administrar.branches.logic import listar_sucursales

    _crear_sucursal(admin, "Primera")
    _crear_sucursal(admin, "Segunda")

    ids_originales = [s["id"] for s in listar_sucursales()]
    orden_invertido = list(reversed(ids_originales))

    resp = admin.get("/branches/")
    csrf_meta = extraer_csrf_meta(resp.data)

    resp = admin.post(
        "/branches/reordenar",
        data=json.dumps({"orden": orden_invertido}),
        content_type="application/json",
        headers={"X-CSRFToken": csrf_meta},
    )

    assert resp.status_code == 204
    assert [s["id"] for s in listar_sucursales()] == orden_invertido


def test_reordenar_por_http_sin_csrf_token_devuelve_400(admin):
    resp = admin.post(
        "/branches/reordenar",
        data=json.dumps({"orden": []}),
        content_type="application/json",
    )

    assert resp.status_code == 400


def test_reordenar_requiere_login(client):
    """Sin sesión, login_required debería redirigir aunque el CSRF sea válido
    (la <meta csrf-token> se renderiza igual, sin sesión, en cualquier página)."""
    resp = client.get("/user/login")
    csrf_meta = extraer_csrf_meta(resp.data)

    resp = client.post(
        "/branches/reordenar",
        data=json.dumps({"orden": []}),
        content_type="application/json",
        headers={"X-CSRFToken": csrf_meta},
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/user/login"
