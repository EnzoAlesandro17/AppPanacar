from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.user.logic import crear_usuario
from src.modules.administrar.validaciones.vehicle_brands.logic import crear_marca
from src.modules.administrar.vehicles.logic import (
    actualizar_vehiculo,
    crear_vehiculo,
    listar_vehiculos,
    obtener_sucursales_ids_vehiculo,
    visible_para_sucursales,
)
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


def test_vehiculo_sin_sucursales_es_visible_para_cualquier_lista(app):
    marca = crear_marca("MarcaTest1")
    sucursal = crear_sucursal(name="Sucursal Ajena Vehiculo")
    id_vehiculo = crear_vehiculo(brand_id=marca, model="Modelo", year=2020, license_plate="ABC123")

    assert obtener_sucursales_ids_vehiculo(id_vehiculo) == []
    assert visible_para_sucursales(id_vehiculo, [sucursal])
    assert visible_para_sucursales(id_vehiculo, [])


def test_vehiculo_con_sucursal_solo_visible_si_comparte_alguna(app):
    marca = crear_marca("MarcaTest2")
    sucursal_propia = crear_sucursal(name="Sucursal Propia Vehiculo")
    sucursal_ajena = crear_sucursal(name="Sucursal Ajena Vehiculo Dos")
    id_vehiculo = crear_vehiculo(
        brand_id=marca, model="Modelo", year=2020, license_plate="ABC124", branch_ids=[sucursal_propia]
    )

    assert visible_para_sucursales(id_vehiculo, [sucursal_propia])
    assert not visible_para_sucursales(id_vehiculo, [sucursal_ajena])


def test_actualizar_vehiculo_branch_ids_none_no_toca_las_actuales(app):
    marca = crear_marca("MarcaTest3")
    sucursal = crear_sucursal(name="Sucursal Persistente Vehiculo")
    id_vehiculo = crear_vehiculo(
        brand_id=marca, model="Modelo", year=2020, license_plate="ABC125", branch_ids=[sucursal]
    )

    actualizar_vehiculo(id_vehiculo, color="Rojo")

    assert obtener_sucursales_ids_vehiculo(id_vehiculo) == [sucursal]


def test_actualizar_vehiculo_branch_ids_vacia_desvincula_todas(app):
    marca = crear_marca("MarcaTest4")
    sucursal = crear_sucursal(name="Sucursal A Vaciar Vehiculo")
    id_vehiculo = crear_vehiculo(
        brand_id=marca, model="Modelo", year=2020, license_plate="ABC126", branch_ids=[sucursal]
    )

    actualizar_vehiculo(id_vehiculo, branch_ids=[])

    assert obtener_sucursales_ids_vehiculo(id_vehiculo) == []


def test_listar_vehiculos_filtra_por_sucursal(app):
    marca = crear_marca("MarcaTest5")
    sucursal_a = crear_sucursal(name="Sucursal Filtro Vehiculo A")
    sucursal_b = crear_sucursal(name="Sucursal Filtro Vehiculo B")
    crear_vehiculo(brand_id=marca, model="Solo A", year=2020, license_plate="ABC127", branch_ids=[sucursal_a])
    crear_vehiculo(brand_id=marca, model="Solo B", year=2020, license_plate="ABC128", branch_ids=[sucursal_b])
    crear_vehiculo(brand_id=marca, model="Sin Sucursal", year=2020, license_plate="ABC129")

    modelos = {v["model"] for v in listar_vehiculos(branch_ids=[sucursal_a])}

    assert modelos == {"Solo A", "Sin Sucursal"}


def test_asesor_no_ve_por_http_vehiculo_de_otra_sucursal(client):
    marca = crear_marca("MarcaTestHTTP1")
    sucursal_a = crear_sucursal(name="Sucursal HTTP Vehiculo A")
    sucursal_b = crear_sucursal(name="Sucursal HTTP Vehiculo B")
    id_vehiculo_b = crear_vehiculo(
        brand_id=marca, model="ExclusivoDeB", year=2020, license_plate="ABC130", branch_ids=[sucursal_b]
    )

    asesor_a = _login(client, "asesor_vehiculo_a", "Asesor", [sucursal_a])

    resp = asesor_a.get("/vehiculos/")
    assert b"ExclusivoDeB" not in resp.data

    resp = asesor_a.get(f"/vehiculos/{id_vehiculo_b}/editar", follow_redirects=True)
    assert "No tenés acceso a ese vehículo.".encode() in resp.data
