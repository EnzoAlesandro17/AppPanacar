from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.user.logic import (
    actualizar_usuario,
    crear_usuario,
    obtener_sucursales_ids_usuario,
)
from tests.conftest import extraer_csrf


def test_crear_usuario_sin_sucursales_queda_sin_ninguna(app):
    id_usuario = crear_usuario(username="sin_sucursal", password="clave-segura-123")

    assert obtener_sucursales_ids_usuario(id_usuario) == []


def test_crear_usuario_con_varias_sucursales(app):
    sucursal_1 = crear_sucursal(name="Sucursal Uno")
    sucursal_2 = crear_sucursal(name="Sucursal Dos")

    id_usuario = crear_usuario(
        username="con_sucursales", password="clave-segura-123", branch_ids=[sucursal_1, sucursal_2]
    )

    assert set(obtener_sucursales_ids_usuario(id_usuario)) == {sucursal_1, sucursal_2}


def test_actualizar_usuario_branch_ids_none_no_toca_las_actuales(app):
    sucursal = crear_sucursal(name="Sucursal Persistente")
    id_usuario = crear_usuario(username="persistente", password="clave-segura-123", branch_ids=[sucursal])

    actualizar_usuario(id_usuario, username="persistente_2")

    assert obtener_sucursales_ids_usuario(id_usuario) == [sucursal]


def test_actualizar_usuario_branch_ids_vacia_desvincula_todas(app):
    sucursal = crear_sucursal(name="Sucursal A Vaciar")
    id_usuario = crear_usuario(username="a_vaciar", password="clave-segura-123", branch_ids=[sucursal])

    actualizar_usuario(id_usuario, branch_ids=[])

    assert obtener_sucursales_ids_usuario(id_usuario) == []


def test_login_guarda_branch_ids_en_sesion(client):
    sucursal = crear_sucursal(name="Sucursal Login")
    crear_usuario(username="login_sucursal", password="clave-segura-123", branch_ids=[sucursal])

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "login_sucursal", "password": "clave-segura-123"},
        follow_redirects=True,
    )

    with client.session_transaction() as sess:
        assert sess["branch_ids"] == [sucursal]


def test_crud_usuarios_por_http_con_sucursales(admin):
    sucursal_1 = crear_sucursal(name="Sucursal HTTP Uno")
    sucursal_2 = crear_sucursal(name="Sucursal HTTP Dos")

    resp = admin.get("/usuarios/nuevo")
    token = extraer_csrf(resp.data)

    resp = admin.post(
        "/usuarios/nuevo",
        data={
            "csrf_token": token, "username": "multi_sucursal", "password": "clave-segura-123",
            "role": "Asesor", "branch_ids": [str(sucursal_1), str(sucursal_2)],
        },
        follow_redirects=True,
    )
    assert b"Usuario creado" in resp.data
