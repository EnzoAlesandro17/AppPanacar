import pytest

URLS_BORRADOS_ADMINISTRACION = [
    "/sucursales/borrados",
    "/empleados/borrados",
    "/marcas-vehiculos/borrados",
    "/companias-seguro/borrados",
    "/estados-siniestro/borrados",
]

URLS_BORRADOS_FUERA_ADMINISTRACION = [
    "/clientes/borrados",
    "/vehiculos/borrados",
    "/stock/borrados",
    "/links-utiles/borrados",
    # /usuarios/borrados no usa el before_request de blueprint (chequea
    # permiso vista por vista), así que el decorator de "ver eliminados"
    # responde primero, igual que en los módulos fuera de Administración.
    "/usuarios/borrados",
]

URLS_BORRADOS_TODAS = URLS_BORRADOS_ADMINISTRACION + URLS_BORRADOS_FUERA_ADMINISTRACION


@pytest.mark.parametrize("url", URLS_BORRADOS_TODAS)
def test_it_puede_ver_borrados_en_cualquier_modulo(admin, url):
    resp = admin.get(url)

    assert resp.status_code == 200


@pytest.mark.parametrize("url", URLS_BORRADOS_TODAS)
def test_backoffice_no_puede_ver_borrados(backoffice, url):
    resp = backoffice.get(url, follow_redirects=True)

    assert "No tenés permiso para ver eliminados.".encode() in resp.data


@pytest.mark.parametrize("url", URLS_BORRADOS_FUERA_ADMINISTRACION)
def test_asesor_no_puede_ver_borrados_fuera_de_administracion(asesor, url):
    resp = asesor.get(url, follow_redirects=True)

    assert "No tenés permiso para ver eliminados.".encode() in resp.data


@pytest.mark.parametrize("url", URLS_BORRADOS_ADMINISTRACION)
def test_asesor_no_puede_ver_borrados_de_administracion(asesor, url):
    """Bloqueado antes de llegar al chequeo de eliminados: toda Administración
    ya está vedada para Asesor."""
    resp = asesor.get(url, follow_redirects=True)

    assert "No tenés permiso para acceder a Administración.".encode() in resp.data


def test_link_ver_borrados_visible_para_it(admin):
    resp = admin.get("/clientes/")

    assert b"Ver borrados" in resp.data


def test_link_ver_borrados_oculto_para_backoffice(backoffice):
    resp = backoffice.get("/clientes/")

    assert b"Ver borrados" not in resp.data


def test_link_ver_borrados_oculto_para_asesor(asesor):
    resp = asesor.get("/clientes/")

    assert b"Ver borrados" not in resp.data
