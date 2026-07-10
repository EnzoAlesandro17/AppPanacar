from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.clients.logic import (
    actualizar_cliente,
    crear_cliente,
    listar_clientes,
    obtener_sucursales_ids_cliente,
    visible_para_sucursales,
)
from src.modules.administrar.user.logic import crear_usuario
from tests.conftest import extraer_csrf


def _login(client, username, role, branch_ids):
    crear_usuario(username=username, password="clave-segura-123", role=role, branch_ids=branch_ids)
    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": username, "password": "clave-segura-123"},
        follow_redirects=True,
    )
    return client


def test_cliente_sin_sucursales_es_visible_para_cualquier_lista(app):
    sucursal = crear_sucursal(name="Sucursal Ajena")
    id_cliente = crear_cliente(name="Juan", last_name="Perez", dni_cuit="30111401")

    assert obtener_sucursales_ids_cliente(id_cliente) == []
    assert visible_para_sucursales(id_cliente, [sucursal])
    assert visible_para_sucursales(id_cliente, [])


def test_cliente_con_sucursal_solo_visible_si_comparte_alguna(app):
    sucursal_propia = crear_sucursal(name="Sucursal Propia")
    sucursal_ajena = crear_sucursal(name="Sucursal Ajena Dos")
    id_cliente = crear_cliente(
        name="Ana", last_name="Gomez", dni_cuit="30111402", branch_ids=[sucursal_propia]
    )

    assert visible_para_sucursales(id_cliente, [sucursal_propia])
    assert not visible_para_sucursales(id_cliente, [sucursal_ajena])


def test_actualizar_cliente_branch_ids_none_no_toca_las_actuales(app):
    sucursal = crear_sucursal(name="Sucursal Persistente Cliente")
    id_cliente = crear_cliente(
        name="Rita", last_name="Diaz", dni_cuit="30111403", branch_ids=[sucursal]
    )

    actualizar_cliente(id_cliente, phone="1122334455")

    assert obtener_sucursales_ids_cliente(id_cliente) == [sucursal]


def test_actualizar_cliente_branch_ids_vacia_desvincula_todas(app):
    sucursal = crear_sucursal(name="Sucursal A Vaciar Cliente")
    id_cliente = crear_cliente(
        name="Tito", last_name="Ruiz", dni_cuit="30111404", branch_ids=[sucursal]
    )

    actualizar_cliente(id_cliente, branch_ids=[])

    assert obtener_sucursales_ids_cliente(id_cliente) == []


def test_listar_clientes_filtra_por_sucursal(app):
    sucursal_a = crear_sucursal(name="Sucursal Filtro A")
    sucursal_b = crear_sucursal(name="Sucursal Filtro B")
    crear_cliente(name="Solo A", last_name="Cliente", dni_cuit="30111405", branch_ids=[sucursal_a])
    crear_cliente(name="Solo B", last_name="Cliente", dni_cuit="30111406", branch_ids=[sucursal_b])
    crear_cliente(name="Sin Sucursal", last_name="Cliente", dni_cuit="30111407")

    nombres = {c["name"] for c in listar_clientes(branch_ids=[sucursal_a])}

    assert nombres == {"Solo A", "Sin Sucursal"}


def test_asesor_no_ve_por_http_cliente_de_otra_sucursal(client):
    sucursal_a = crear_sucursal(name="Sucursal HTTP A")
    sucursal_b = crear_sucursal(name="Sucursal HTTP B")
    id_cliente_b = crear_cliente(
        name="Exclusivo", last_name="DeB", dni_cuit="30111408", branch_ids=[sucursal_b]
    )

    asesor_a = _login(client, "asesor_sucursal_a", "Asesor", [sucursal_a])

    resp = asesor_a.get("/clientes/")
    assert b"Exclusivo" not in resp.data

    resp = asesor_a.get(f"/clientes/{id_cliente_b}/editar", follow_redirects=True)
    assert "No tenés acceso a ese cliente.".encode() in resp.data


def test_asesor_ve_por_http_cliente_de_su_propia_sucursal(client):
    sucursal_a = crear_sucursal(name="Sucursal HTTP C")
    id_cliente_a = crear_cliente(
        name="Compartido", last_name="DeA", dni_cuit="30111409", branch_ids=[sucursal_a]
    )

    asesor_a = _login(client, "asesor_sucursal_c", "Asesor", [sucursal_a])

    resp = asesor_a.get("/clientes/")
    assert b"Compartido" in resp.data

    resp = asesor_a.get(f"/clientes/{id_cliente_a}/editar")
    assert resp.status_code == 200
