import pytest

URLS_ADMINISTRACION = [
    "/administracion/",
    "/sucursales/",
    "/empleados/",
    "/usuarios/",
    "/validaciones/",
    "/marcas-vehiculos/",
    "/companias-seguro/",
    "/estados-siniestro/",
    "/contabilidad/",
    "/preguntas-frecuentes/",
]


@pytest.mark.parametrize("url", URLS_ADMINISTRACION)
def test_asesor_no_puede_acceder_a_administracion(asesor, url):
    resp = asesor.get(url, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


@pytest.mark.parametrize("url", URLS_ADMINISTRACION)
def test_admin_puede_acceder_a_administracion(admin, url):
    resp = admin.get(url)

    assert resp.status_code == 200


@pytest.mark.parametrize("url", URLS_ADMINISTRACION)
def test_backoffice_puede_acceder_a_administracion(backoffice, url):
    resp = backoffice.get(url)

    assert resp.status_code == 200


def test_asesor_ve_mensaje_de_permiso_denegado(asesor):
    resp = asesor.get("/sucursales/", follow_redirects=True)

    assert "No tenés permiso para acceder a Administración.".encode() in resp.data


def test_tile_administracion_oculto_para_asesor(asesor):
    resp = asesor.get("/")

    assert b"Administraci\xc3\xb3n</a>" not in resp.data


def test_tile_administracion_visible_para_admin(admin):
    resp = admin.get("/")

    assert b"Administraci\xc3\xb3n</a>" in resp.data


def test_asesor_sigue_pudiendo_entrar_a_mi_cuenta(asesor):
    resp = asesor.get("/usuarios/perfil")

    assert resp.status_code == 200


def test_asesor_sigue_pudiendo_entrar_a_configuracion(asesor):
    resp = asesor.get("/configuracion/")

    assert resp.status_code == 200
