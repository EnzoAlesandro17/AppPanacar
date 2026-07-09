import pytest

from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.employees.logic import (
    actualizar_empleado,
    borrar_empleado,
    crear_empleado,
    listar_empleados,
    obtener_por_id,
    obtener_sucursales,
    obtener_sucursales_ids,
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


def test_crear_empleado_con_varias_sucursales(app):
    sucursal_1 = crear_sucursal(name="Sucursal Norte")
    sucursal_2 = crear_sucursal(name="Sucursal Sur")

    id_empleado = crear_empleado(
        position="Chapista", name="Juan", last_name="Perez", dni="30111231",
        branch_ids=[sucursal_1, sucursal_2],
    )

    ids = obtener_sucursales_ids(id_empleado)
    assert set(ids) == {sucursal_1, sucursal_2}

    nombres = [s["name"] for s in obtener_sucursales(id_empleado)]
    assert nombres == ["Sucursal Norte", "Sucursal Sur"]


def test_crear_empleado_sin_branch_ids_no_asocia_sucursales(app):
    id_empleado = crear_empleado(position="Chapista", name="Juan", last_name="Perez", dni="30111232")

    assert obtener_sucursales_ids(id_empleado) == []


def test_crear_empleado_con_sucursal_inexistente_falla(app):
    with pytest.raises(ValidationError, match="Una de las sucursales indicadas no existe"):
        crear_empleado(
            position="Chapista", name="Juan", last_name="Perez", dni="30111233",
            branch_ids=[999],
        )


def test_actualizar_empleado_cambia_sucursales(app):
    sucursal_1 = crear_sucursal(name="Sucursal Este")
    sucursal_2 = crear_sucursal(name="Sucursal Oeste")
    id_empleado = crear_empleado(
        position="Chapista", name="Juan", last_name="Perez", dni="30111234",
        branch_ids=[sucursal_1],
    )

    actualizar_empleado(id_empleado, branch_ids=[sucursal_2])

    assert obtener_sucursales_ids(id_empleado) == [sucursal_2]


def test_actualizar_empleado_sin_branch_ids_no_toca_sucursales(app):
    sucursal = crear_sucursal(name="Sucursal Centro")
    id_empleado = crear_empleado(
        position="Chapista", name="Juan", last_name="Perez", dni="30111235",
        branch_ids=[sucursal],
    )

    actualizar_empleado(id_empleado, position="Encargado")

    assert obtener_sucursales_ids(id_empleado) == [sucursal]


def test_actualizar_empleado_con_lista_vacia_borra_sucursales(app):
    sucursal = crear_sucursal(name="Sucursal Vacía")
    id_empleado = crear_empleado(
        position="Chapista", name="Juan", last_name="Perez", dni="30111236",
        branch_ids=[sucursal],
    )

    actualizar_empleado(id_empleado, branch_ids=[])

    assert obtener_sucursales_ids(id_empleado) == []


def test_listar_empleados_incluye_branch_names(app):
    sucursal_1 = crear_sucursal(name="Sucursal Alfa")
    sucursal_2 = crear_sucursal(name="Sucursal Beta")
    id_empleado = crear_empleado(
        position="Chapista", name="Juan", last_name="Perez", dni="30111237",
        branch_ids=[sucursal_1, sucursal_2],
    )

    fila = next(e for e in listar_empleados() if e["id"] == id_empleado)
    assert fila["branch_names"] == "Sucursal Alfa, Sucursal Beta"


def test_crud_empleados_por_http_con_varias_sucursales(admin):
    sucursal_1 = crear_sucursal(name="Sucursal HTTP Uno")
    sucursal_2 = crear_sucursal(name="Sucursal HTTP Dos")

    resp = admin.get("/empleados/nuevo")
    token = extraer_csrf(resp.data)

    resp = admin.post(
        "/empleados/nuevo",
        data={
            "csrf_token": token, "position": "Chapista", "name": "Multi", "last_name": "Sucursal",
            "dni": "30111238", "branch_ids": [str(sucursal_1), str(sucursal_2)],
        },
        follow_redirects=True,
    )
    assert b"Empleado creado" in resp.data

    resp = admin.get("/empleados/")
    assert b"Sucursal HTTP Uno, Sucursal HTTP Dos" in resp.data
