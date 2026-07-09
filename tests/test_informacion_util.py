import json

import pytest

from src.exceptions import ValidationError
from src.modules.administrar.informacion_util.logic import (
    actualizar_enlace,
    borrar_enlace,
    crear_enlace,
    listar_enlaces,
    obtener_por_id,
    reactivar_enlace,
    reordenar_enlaces,
)
from tests.conftest import extraer_csrf, extraer_csrf_meta


def test_crear_enlace_devuelve_id_y_queda_activo(app):
    id_enlace = crear_enlace(label="Manual Toyota", url="https://ejemplo.com/toyota")

    enlace = obtener_por_id(id_enlace)
    assert enlace["label"] == "Manual Toyota"
    assert enlace["url"] == "https://ejemplo.com/toyota"
    assert enlace["status"] == 1


@pytest.mark.parametrize("label,url", [("", "https://ejemplo.com"), ("Texto", "")])
def test_crear_enlace_exige_label_y_url(app, label, url):
    with pytest.raises(ValidationError):
        crear_enlace(label=label, url=url)


def test_listar_enlaces_excluye_borrados_por_defecto(app):
    activo = crear_enlace(label="Activo", url="https://ejemplo.com/a")
    borrado = crear_enlace(label="Borrado", url="https://ejemplo.com/b")
    borrar_enlace(borrado)

    ids = [e["id"] for e in listar_enlaces()]
    assert activo in ids
    assert borrado not in ids


def test_actualizar_enlace(app):
    id_enlace = crear_enlace(label="Original", url="https://ejemplo.com/original")

    actualizar_enlace(id_enlace, label="Nuevo", url="https://ejemplo.com/nuevo")

    enlace = obtener_por_id(id_enlace)
    assert enlace["label"] == "Nuevo"
    assert enlace["url"] == "https://ejemplo.com/nuevo"


def test_crear_y_actualizar_enlace_guardan_observaciones(app):
    id_enlace = crear_enlace(label="Con nota", url="https://ejemplo.com", observations="Usuario: admin")
    assert obtener_por_id(id_enlace)["observations"] == "Usuario: admin"

    actualizar_enlace(id_enlace, label="Con nota", url="https://ejemplo.com", observations="Actualizada")
    assert obtener_por_id(id_enlace)["observations"] == "Actualizada"


def test_observaciones_son_opcionales(app):
    id_enlace = crear_enlace(label="Sin nota", url="https://ejemplo.com")
    assert obtener_por_id(id_enlace)["observations"] is None


def test_borrar_y_reactivar_enlace(app):
    id_enlace = crear_enlace(label="Para borrar", url="https://ejemplo.com")

    borrar_enlace(id_enlace)
    assert obtener_por_id(id_enlace)["status"] == 0

    reactivar_enlace(id_enlace)
    assert obtener_por_id(id_enlace)["status"] == 1


def test_enlaces_nuevos_se_agregan_al_final(app):
    primero = crear_enlace(label="Primero", url="https://ejemplo.com/1")
    segundo = crear_enlace(label="Segundo", url="https://ejemplo.com/2")

    assert [e["id"] for e in listar_enlaces()] == [primero, segundo]


def test_reordenar_enlaces(app):
    primero = crear_enlace(label="Primero", url="https://ejemplo.com/1")
    segundo = crear_enlace(label="Segundo", url="https://ejemplo.com/2")

    reordenar_enlaces([segundo, primero])

    assert [e["id"] for e in listar_enlaces()] == [segundo, primero]


def test_tile_informacion_util_en_home(admin):
    resp = admin.get("/")

    assert b"tile-ancho" in resp.data
    assert "Links útiles".encode() in resp.data


def test_reordenar_por_http_exige_csrf(admin):
    resp = admin.get("/links-utiles/nuevo")
    token = extraer_csrf(resp.data)
    admin.post(
        "/links-utiles/nuevo",
        data={"csrf_token": token, "label": "A", "url": "https://a.com"},
        follow_redirects=True,
    )
    resp = admin.get("/links-utiles/nuevo")
    token = extraer_csrf(resp.data)
    admin.post(
        "/links-utiles/nuevo",
        data={"csrf_token": token, "label": "B", "url": "https://b.com"},
        follow_redirects=True,
    )

    ids = [e["id"] for e in listar_enlaces()]

    resp = admin.post(
        "/links-utiles/reordenar",
        data=json.dumps({"orden": list(reversed(ids))}),
    )
    assert resp.status_code == 400

    resp = admin.get("/links-utiles/")
    csrf_meta = extraer_csrf_meta(resp.data)
    resp = admin.post(
        "/links-utiles/reordenar",
        data=json.dumps({"orden": list(reversed(ids))}),
        content_type="application/json",
        headers={"X-CSRFToken": csrf_meta},
    )
    assert resp.status_code == 204
    assert [e["id"] for e in listar_enlaces()] == list(reversed(ids))


def test_listado_no_muestra_la_url_como_texto_pero_si_boton_abrir_y_observaciones(admin):
    """La URL sigue en el href del botón "Abrir" (tiene que funcionar), pero
    no debe aparecer como texto legible en ninguna celda de la tabla."""
    resp = admin.get("/links-utiles/nuevo")
    token = extraer_csrf(resp.data)
    admin.post(
        "/links-utiles/nuevo",
        data={
            "csrf_token": token, "label": "Manual Toyota", "url": "https://ejemplo.com/secreto-url",
            "observations": "Pedirle la clave a administración",
        },
        follow_redirects=True,
    )

    resp = admin.get("/links-utiles/")
    assert b">https://ejemplo.com/secreto-url<" not in resp.data
    assert b'href="https://ejemplo.com/secreto-url"' in resp.data
    assert b"Pedirle la clave a administraci\xc3\xb3n" in resp.data
    assert b">Abrir<" in resp.data
    assert b'target="_blank"' in resp.data
