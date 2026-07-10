from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.products.logic import (
    actualizar_producto,
    crear_producto,
    listar_productos,
    obtener_sucursales_ids_producto,
    visible_para_sucursales,
)
from src.modules.administrar.user.logic import crear_usuario
from tests.conftest import extraer_csrf


def _producto(code, name, **overrides):
    datos = dict(
        code=code, name=name, category="Categoria", brand="MarcaX", description="Descripcion",
        stock=10, wholesale_price=100.0, retail_price=150.0,
    )
    datos.update(overrides)
    return crear_producto(**datos)


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


def test_producto_sin_sucursales_es_visible_para_cualquier_lista(app):
    sucursal = crear_sucursal(name="Sucursal Ajena Producto")
    id_producto = _producto("P001", "Producto Uno")

    assert obtener_sucursales_ids_producto(id_producto) == []
    assert visible_para_sucursales(id_producto, [sucursal])
    assert visible_para_sucursales(id_producto, [])


def test_producto_con_sucursal_solo_visible_si_comparte_alguna(app):
    sucursal_propia = crear_sucursal(name="Sucursal Propia Producto")
    sucursal_ajena = crear_sucursal(name="Sucursal Ajena Producto Dos")
    id_producto = _producto("P002", "Producto Dos", branch_ids=[sucursal_propia])

    assert visible_para_sucursales(id_producto, [sucursal_propia])
    assert not visible_para_sucursales(id_producto, [sucursal_ajena])


def test_actualizar_producto_branch_ids_none_no_toca_las_actuales(app):
    sucursal = crear_sucursal(name="Sucursal Persistente Producto")
    id_producto = _producto("P003", "Producto Tres", branch_ids=[sucursal])

    actualizar_producto(id_producto, supplier="Proveedor X")

    assert obtener_sucursales_ids_producto(id_producto) == [sucursal]


def test_actualizar_producto_branch_ids_vacia_desvincula_todas(app):
    sucursal = crear_sucursal(name="Sucursal A Vaciar Producto")
    id_producto = _producto("P004", "Producto Cuatro", branch_ids=[sucursal])

    actualizar_producto(id_producto, branch_ids=[])

    assert obtener_sucursales_ids_producto(id_producto) == []


def test_listar_productos_filtra_por_sucursal(app):
    sucursal_a = crear_sucursal(name="Sucursal Filtro Producto A")
    sucursal_b = crear_sucursal(name="Sucursal Filtro Producto B")
    _producto("P005", "Solo A", branch_ids=[sucursal_a])
    _producto("P006", "Solo B", branch_ids=[sucursal_b])
    _producto("P007", "Sin Sucursal")

    nombres = {p["name"] for p in listar_productos(branch_ids=[sucursal_a])}

    assert nombres == {"Solo A", "Sin Sucursal"}


def test_asesor_no_ve_por_http_producto_de_otra_sucursal(client):
    sucursal_a = crear_sucursal(name="Sucursal HTTP Producto A")
    sucursal_b = crear_sucursal(name="Sucursal HTTP Producto B")
    id_producto_b = _producto("P008", "ExclusivoDeB", branch_ids=[sucursal_b])

    asesor_a = _login(client, "asesor_producto_a", "Asesor", [sucursal_a])

    resp = asesor_a.get("/stock/")
    assert b"ExclusivoDeB" not in resp.data

    resp = asesor_a.get(f"/stock/{id_producto_b}/editar", follow_redirects=True)
    assert "No tenés acceso a ese producto.".encode() in resp.data
