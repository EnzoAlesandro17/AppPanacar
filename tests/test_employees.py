import pytest

from src.exceptions import ValidationError
from src.modules.administrar.employees.logic import (
    actualizar_empleado,
    borrar_empleado,
    crear_empleado,
    listar_empleados,
    obtener_por_id,
    reactivar_empleado,
)
from tests.conftest import extraer_csrf


def test_crear_empleado_devuelve_id_y_queda_activo(app):
    id_empleado = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111222")

    empleado = obtener_por_id(id_empleado)
    assert empleado["position"] == "Chapista"
    assert empleado["name"] == "Juan"
    assert empleado["last_name"] == "Perez"
    assert empleado["dni"] == "30111222"
    assert empleado["status"] == 1


@pytest.mark.parametrize(
    "campos",
    [
        {"position": "", "name": "Juan", "last_name": "Perez", "dni": "30111222"},
        {"position": "Chapista", "name": "", "last_name": "Perez", "dni": "30111222"},
        {"position": "Chapista", "name": "Juan", "last_name": "", "dni": "30111222"},
        {"position": "Chapista", "name": "Juan", "last_name": "Perez", "dni": ""},
    ],
)
def test_crear_empleado_exige_campos_obligatorios(app, campos):
    with pytest.raises(ValidationError):
        crear_empleado(**campos)


def test_crear_empleado_valida_dni():
    with pytest.raises(ValidationError):
        crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="123")


def test_crear_empleado_con_dni_duplicado_falla(app):
    crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111222")

    with pytest.raises(ValidationError, match="Ya existe un empleado"):
        crear_empleado(position="Pintor", name="Otro", last_name="Persona", dni="30111222")


def test_crear_empleado_con_campos_opcionales(app):
    id_empleado = crear_empleado(
        position="Pintor", name="Ana", last_name="Gomez", dni="30111223",
        email="ana@ejemplo.com", phone="3415551234",
        emergency_contact_name="Marcos Gomez", emergency_contact_phone="3415559999",
    )

    empleado = obtener_por_id(id_empleado)
    assert empleado["email"] == "ana@ejemplo.com"
    assert empleado["emergency_contact_name"] == "Marcos Gomez"
    assert empleado["emergency_contact_phone"] == "3415559999"


def test_listar_empleados_excluye_borrados_por_defecto(app):
    activo = crear_empleado(position="Chapista", name="Activo", last_name="Uno", dni="30111224")
    borrado = crear_empleado(position="Chapista", name="Borrado", last_name="Dos", dni="30111225")
    borrar_empleado(borrado)

    ids = [e["id"] for e in listar_empleados()]
    assert activo in ids
    assert borrado not in ids


def test_actualizar_empleado(app):
    id_empleado = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111226")

    actualizar_empleado(id_empleado, position="Encargado")

    assert obtener_por_id(id_empleado)["position"] == "Encargado"
    assert obtener_por_id(id_empleado)["name"] == "Juan"


def test_borrar_y_reactivar_empleado(app):
    id_empleado = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111227")

    borrar_empleado(id_empleado)
    assert obtener_por_id(id_empleado)["status"] == 0

    reactivar_empleado(id_empleado)
    assert obtener_por_id(id_empleado)["status"] == 1


def test_tile_empleados_en_administracion(admin):
    resp = admin.get("/administracion/")

    assert b"Empleados" in resp.data


def test_crud_empleados_por_http(admin):
    resp = admin.get("/empleados/nuevo")
    token = extraer_csrf(resp.data)

    resp = admin.post(
        "/empleados/nuevo",
        data={
            "csrf_token": token, "position": "Chapista", "name": "Http", "last_name": "Test",
            "dni": "30111228",
        },
        follow_redirects=True,
    )
    assert b"Empleado creado" in resp.data

    resp = admin.get("/empleados/")
    assert b"Http Test" in resp.data
    assert b"Chapista" in resp.data


def test_usuario_se_puede_vincular_a_un_empleado(app):
    from src.modules.administrar.user.logic import crear_usuario, obtener_por_id as obtener_usuario

    id_empleado = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111229")
    id_usuario = crear_usuario(
        username="juanp", password="clave-segura-123", role="Asesor", employee_id=id_empleado
    )

    assert obtener_usuario(id_usuario)["employee_id"] == id_empleado


def test_usuario_con_employee_id_inexistente_falla(app):
    from src.modules.administrar.user.logic import crear_usuario

    with pytest.raises(ValidationError, match="El empleado indicado no existe"):
        crear_usuario(username="juanp", password="clave-segura-123", role="Asesor", employee_id=999)


def test_usuario_sin_username_o_password_falla(app):
    from src.modules.administrar.user.logic import crear_usuario

    with pytest.raises(ValidationError):
        crear_usuario(username="", password="clave-segura-123")

    with pytest.raises(ValidationError):
        crear_usuario(username="juanp", password="")


def test_login_usa_nombre_del_empleado_vinculado(app, client):
    id_empleado = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111230")
    from src.modules.administrar.user.logic import crear_usuario
    crear_usuario(username="juanp", password="clave-segura-123", role="Asesor", employee_id=id_empleado)

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    resp = client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "juanp", "password": "clave-segura-123"},
        follow_redirects=True,
    )
    assert b"Juan Perez" in resp.data


def test_login_sin_empleado_vinculado_usa_el_username(app, client):
    from src.modules.administrar.user.logic import crear_usuario
    crear_usuario(username="soloacceso", password="clave-segura-123", role="Asesor")

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    resp = client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "soloacceso", "password": "clave-segura-123"},
        follow_redirects=True,
    )
    assert b"soloacceso" in resp.data
