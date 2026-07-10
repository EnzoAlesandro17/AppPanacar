"""BackOffice/Asesor no ven listas de eliminados (ver test_ver_eliminados.py);
en su lugar, si intentan crear un registro que choca con uno ya borrado
(mismo DNI/CUIT, dominio, code, etc.), el sistema les ofrece reactivar ese
registro en vez de rechazarlo por duplicado. Estos tests cubren esa
detección módulo por módulo."""

import pytest

from src.exceptions import RegistroBorradoExistente
from src.modules.administrar.branches.logic import borrar_sucursal, crear_sucursal
from src.modules.administrar.clients.logic import borrar_cliente, crear_cliente
from src.modules.administrar.employees.logic import borrar_empleado, crear_empleado
from src.modules.administrar.products.logic import borrar_producto, crear_producto
from src.modules.administrar.user.logic import borrar_usuario, crear_usuario
from src.modules.administrar.validaciones.claim_statuses.logic import borrar_estado, crear_estado
from src.modules.administrar.validaciones.insurance_companies.logic import (
    borrar_aseguradora,
    crear_aseguradora,
)
from src.modules.administrar.validaciones.vehicle_brands.logic import borrar_marca, crear_marca
from src.modules.administrar.vehicles.logic import borrar_vehiculo, crear_vehiculo
from tests.conftest import extraer_csrf


def _login(client, username, role, branch_ids=None):
    crear_usuario(username=username, password="clave-segura-123", role=role, branch_ids=branch_ids)
    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": username, "password": "clave-segura-123"},
        follow_redirects=True,
    )
    return client


def test_crear_cliente_con_dni_de_uno_borrado_levanta_registro_borrado_existente(app):
    id_original = crear_cliente(name="Juan", last_name="Perez", dni_cuit="30111450")
    borrar_cliente(id_original)

    try:
        crear_cliente(name="Juan Otra Vez", last_name="Perez", dni_cuit="30111450")
        assert False, "debería haber levantado RegistroBorradoExistente"
    except RegistroBorradoExistente as error:
        assert error.id_existente == id_original


def test_backoffice_recibe_oferta_de_reactivar_por_http(client):
    id_original = crear_cliente(name="Juan", last_name="Perez", dni_cuit="30111451")
    borrar_cliente(id_original)

    backoffice = _login(client, "backoffice_reactiva", "BackOffice")

    resp = backoffice.get("/clientes/nuevo")
    token = extraer_csrf(resp.data)
    resp = backoffice.post(
        "/clientes/nuevo",
        data={
            "csrf_token": token, "name": "Juan Otra Vez", "last_name": "Perez", "dni_cuit": "30111451",
        },
        follow_redirects=True,
    )

    assert "Podés reactivarlo en vez de crear uno nuevo".encode() in resp.data
    assert f'/clientes/{id_original}/reactivar'.encode() in resp.data

    resp = backoffice.post(
        f"/clientes/{id_original}/reactivar",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    assert b"Cliente reactivado" in resp.data


def test_asesor_de_otra_sucursal_no_ve_oferta_de_reactivar(client):
    sucursal_b = crear_sucursal(name="Sucursal Reactivar B")
    id_original = crear_cliente(
        name="Juan", last_name="Perez", dni_cuit="30111452", branch_ids=[sucursal_b]
    )
    borrar_cliente(id_original)

    sucursal_a = crear_sucursal(name="Sucursal Reactivar A")
    asesor_a = _login(client, "asesor_reactiva_a", "Asesor", [sucursal_a])

    resp = asesor_a.get("/clientes/nuevo")
    token = extraer_csrf(resp.data)
    resp = asesor_a.post(
        "/clientes/nuevo",
        data={
            "csrf_token": token, "name": "Juan Otra Vez", "last_name": "Perez", "dni_cuit": "30111452",
        },
        follow_redirects=True,
    )

    assert "Ya existe un cliente con ese DNI/CUIT.".encode() in resp.data
    assert "Podés reactivarlo".encode() not in resp.data
    assert f'/clientes/{id_original}/reactivar'.encode() not in resp.data


def test_crear_sucursal_con_code_de_una_borrada_levanta_registro_borrado_existente(app):
    id_original = crear_sucursal(name="Sucursal Original", code="SUC1")
    borrar_sucursal(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_sucursal(name="Sucursal Nueva", code="SUC1")
    assert excinfo.value.id_existente == id_original


def test_crear_producto_con_code_de_uno_borrado_levanta_registro_borrado_existente(app):
    id_original = crear_producto(
        code="PROD1", name="Producto Original", category="Cat", brand="Marca",
        description="Desc", stock=5, wholesale_price=10.0, retail_price=15.0,
    )
    borrar_producto(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_producto(
            code="PROD1", name="Producto Nuevo", category="Cat", brand="Marca",
            description="Desc", stock=5, wholesale_price=10.0, retail_price=15.0,
        )
    assert excinfo.value.id_existente == id_original


def test_crear_vehiculo_con_dominio_de_uno_borrado_levanta_registro_borrado_existente(app):
    marca = crear_marca("MarcaReactivar")
    id_original = crear_vehiculo(brand_id=marca, model="Modelo Original", year=2020, license_plate="ABC199")
    borrar_vehiculo(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_vehiculo(brand_id=marca, model="Modelo Nuevo", year=2021, license_plate="ABC199")
    assert excinfo.value.id_existente == id_original


def test_crear_empleado_con_dni_de_uno_borrado_levanta_registro_borrado_existente(app):
    id_original = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111460")
    borrar_empleado(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_empleado(position="Pintor", name="Juan Otro", last_name="Perez", dni="30111460")
    assert excinfo.value.id_existente == id_original


def test_crear_usuario_con_username_de_uno_borrado_levanta_registro_borrado_existente(app):
    id_original = crear_usuario(username="reactivar_test", password="clave-segura-123")
    borrar_usuario(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_usuario(username="reactivar_test", password="otra-clave-456")
    assert excinfo.value.id_existente == id_original


def test_crear_marca_con_nombre_de_una_borrada_levanta_registro_borrado_existente(app):
    id_original = crear_marca("MarcaBorrable")
    borrar_marca(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_marca("MarcaBorrable")
    assert excinfo.value.id_existente == id_original


def test_crear_aseguradora_con_nombre_de_una_borrada_levanta_registro_borrado_existente(app):
    id_original = crear_aseguradora("AseguradoraBorrable")
    borrar_aseguradora(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_aseguradora("AseguradoraBorrable")
    assert excinfo.value.id_existente == id_original


def test_crear_estado_con_nombre_de_uno_borrado_levanta_registro_borrado_existente(app):
    id_original = crear_estado("EstadoBorrable")
    borrar_estado(id_original)

    with pytest.raises(RegistroBorradoExistente) as excinfo:
        crear_estado("EstadoBorrable")
    assert excinfo.value.id_existente == id_original


def test_it_recibe_oferta_de_reactivar_marca_por_http(client):
    id_original = crear_marca("MarcaHTTPReactivar")
    borrar_marca(id_original)

    it_user = _login(client, "it_reactiva_marca", "IT")

    resp = it_user.get("/marcas-vehiculos/nuevo")
    token = extraer_csrf(resp.data)
    resp = it_user.post(
        "/marcas-vehiculos/nuevo",
        data={"csrf_token": token, "name": "MarcaHTTPReactivar"},
        follow_redirects=True,
    )

    assert "Podés reactivarla en vez de crear una nueva".encode() in resp.data
    assert f'/marcas-vehiculos/{id_original}/reactivar'.encode() in resp.data
