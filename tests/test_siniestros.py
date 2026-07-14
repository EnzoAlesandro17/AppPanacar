from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.clients.logic import crear_cliente
from src.modules.administrar.siniestros.logic import (
    actualizar_siniestro,
    borrar_siniestro,
    crear_siniestro,
    listar_historial,
    listar_siniestros,
    obtener_por_id,
    reactivar_siniestro,
)
from src.modules.administrar.user.logic import crear_usuario
from src.modules.administrar.validaciones.claim_statuses.logic import crear_estado
from src.modules.administrar.validaciones.insurance_companies.logic import crear_aseguradora
from src.modules.administrar.validaciones.vehicle_brands.logic import crear_marca
from src.modules.administrar.vehicles.logic import crear_vehiculo
from tests.conftest import extraer_csrf


def _dependencias():
    """Crea cliente, vehículo, aseguradora, estado y sucursal básicos para armar un siniestro."""
    sucursal = crear_sucursal(name="Sucursal Siniestro")
    cliente = crear_cliente(name="Ana", last_name="Gomez", dni_cuit="30123456")
    marca = crear_marca("MarcaSiniestro")
    vehiculo = crear_vehiculo(brand_id=marca, model="Modelo X", year=2020, license_plate="ABC123")
    aseguradora = crear_aseguradora("Aseguradora Test")
    estado = crear_estado("Abierto")
    return {
        "sucursal": sucursal, "cliente": cliente, "vehiculo": vehiculo, "marca": marca,
        "aseguradora": aseguradora, "estado": estado,
    }


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


def test_crear_siniestro_registra_paso_inicial_del_historial(app):
    d = _dependencias()
    id_siniestro = crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=d["sucursal"], opened_date="2026-01-10", insurance_company_id=d["aseguradora"],
        changed_by_user_id=None, changed_by_username="tester",
    )

    historial = listar_historial(id_siniestro)
    assert len(historial) == 1
    assert historial[0]["previous_status_id"] is None
    assert historial[0]["new_status_id"] == d["estado"]
    assert historial[0]["changed_by_username"] == "tester"


def test_actualizar_siniestro_cambia_estado_agrega_paso_al_historial(app):
    d = _dependencias()
    otro_estado = crear_estado("En reparación")
    id_siniestro = crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=d["sucursal"], opened_date="2026-01-10",
    )

    actualizar_siniestro(id_siniestro, claim_status_id=otro_estado, changed_by_username="tester2")

    historial = listar_historial(id_siniestro)
    assert len(historial) == 2
    assert historial[1]["previous_status_id"] == d["estado"]
    assert historial[1]["new_status_id"] == otro_estado
    assert historial[1]["changed_by_username"] == "tester2"


def test_actualizar_siniestro_sin_cambiar_estado_no_duplica_historial(app):
    d = _dependencias()
    id_siniestro = crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=d["sucursal"], opened_date="2026-01-10",
    )

    actualizar_siniestro(id_siniestro, description="Nueva descripción")

    assert len(listar_historial(id_siniestro)) == 1


def test_quitar_aseguradora_la_desvincula(app):
    d = _dependencias()
    id_siniestro = crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=d["sucursal"], opened_date="2026-01-10", insurance_company_id=d["aseguradora"],
    )

    actualizar_siniestro(id_siniestro, quitar_aseguradora=True)

    assert obtener_por_id(id_siniestro)["insurance_company_id"] is None


def test_listar_siniestros_filtra_por_sucursal_unica(app):
    d = _dependencias()
    otra_sucursal = crear_sucursal(name="Otra Sucursal Siniestro")
    crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=d["sucursal"], opened_date="2026-01-10",
    )
    crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=otra_sucursal, opened_date="2026-01-11",
    )

    propios = listar_siniestros(branch_ids=[d["sucursal"]])

    assert len(propios) == 1
    assert propios[0]["branch_id"] == d["sucursal"]


def test_borrar_y_reactivar_siniestro(app):
    d = _dependencias()
    id_siniestro = crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=d["sucursal"], opened_date="2026-01-10",
    )

    borrar_siniestro(id_siniestro)
    assert obtener_por_id(id_siniestro)["status"] == 0

    reactivar_siniestro(id_siniestro)
    assert obtener_por_id(id_siniestro)["status"] == 1


def test_alta_inline_de_cliente_y_vehiculo_nuevos_por_http(client):
    d = _dependencias()
    logueado = _login(client, "asesor_siniestro", "Asesor", [d["sucursal"]])

    resp = logueado.get("/siniestros/nuevo")
    token = extraer_csrf(resp.data)
    resp = logueado.post(
        "/siniestros/nuevo",
        data={
            "csrf_token": token,
            "modo_cliente": "nuevo",
            "cliente_name": "Carlos", "cliente_last_name": "Ruiz", "cliente_dni_cuit": "30999888",
            "modo_vehiculo": "nuevo",
            "vehiculo_brand_id": str(d["marca"]), "vehiculo_model": "Modelo Nuevo",
            "vehiculo_year": "2022", "vehiculo_license_plate": "AB999CD",
            "claim_status_id": str(d["estado"]), "branch_id": str(d["sucursal"]),
            "opened_date": "10/01/2026",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "Siniestro creado.".encode() in resp.data
    assert "Ruiz, Carlos".encode() in resp.data


def test_asesor_no_ve_por_http_siniestro_de_otra_sucursal(client):
    d = _dependencias()
    otra_sucursal = crear_sucursal(name="Sucursal HTTP Siniestro Ajena")
    id_siniestro = crear_siniestro(
        client_id=d["cliente"], vehicle_id=d["vehiculo"], claim_status_id=d["estado"],
        branch_id=otra_sucursal, opened_date="2026-01-10",
    )

    logueado = _login(client, "asesor_siniestro_ajeno", "Asesor", [d["sucursal"]])

    resp = logueado.get("/siniestros/")
    assert b"Modelo X" not in resp.data

    resp = logueado.get(f"/siniestros/{id_siniestro}/editar", follow_redirects=True)
    assert "No tenés acceso a ese siniestro.".encode() in resp.data
