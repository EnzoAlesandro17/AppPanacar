import pytest

from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import (
    actualizar_sucursal,
    borrar_sucursal,
    crear_sucursal,
    listar_sucursales,
    obtener_por_id,
    reactivar_sucursal,
    reordenar_sucursales,
)


def test_crear_sucursal_devuelve_id_y_queda_activa(app):
    id_sucursal = crear_sucursal(name="Sucursal Centro")

    sucursal = obtener_por_id(id_sucursal)
    assert sucursal["name"] == "Sucursal Centro"
    assert sucursal["status"] == 1


def test_crear_sucursal_sin_nombre_falla():
    with pytest.raises(ValidationError):
        crear_sucursal(name="")


def test_crear_sucursal_con_code_duplicado_falla(app):
    crear_sucursal(name="Sucursal A", code="A1")

    with pytest.raises(ValidationError, match="Ya existe una sucursal"):
        crear_sucursal(name="Sucursal B", code="A1")


def test_listar_sucursales_excluye_borradas_por_defecto(app):
    id_activa = crear_sucursal(name="Activa")
    id_borrada = crear_sucursal(name="Borrada")
    borrar_sucursal(id_borrada)

    ids_listados = [s["id"] for s in listar_sucursales()]

    assert id_activa in ids_listados
    assert id_borrada not in ids_listados


def test_listar_sucursales_incluir_borrados_las_trae_a_todas(app):
    id_activa = crear_sucursal(name="Activa")
    id_borrada = crear_sucursal(name="Borrada")
    borrar_sucursal(id_borrada)

    ids_listados = [s["id"] for s in listar_sucursales(incluir_borrados=True)]

    assert id_activa in ids_listados
    assert id_borrada in ids_listados


def test_actualizar_sucursal_pisa_solo_los_campos_recibidos(app):
    id_sucursal = crear_sucursal(name="Original", city="Rosario")

    actualizar_sucursal(id_sucursal, name="Nuevo nombre")

    sucursal = obtener_por_id(id_sucursal)
    assert sucursal["name"] == "Nuevo nombre"
    assert sucursal["city"] == "Rosario"


def test_actualizar_sucursal_inexistente_falla():
    with pytest.raises(ValidationError, match="no existe"):
        actualizar_sucursal(9999, name="No existe")


def test_borrar_sucursal_es_logico_no_elimina_la_fila(app):
    id_sucursal = crear_sucursal(name="Para borrar")

    borrar_sucursal(id_sucursal)

    sucursal = obtener_por_id(id_sucursal)
    assert sucursal is not None
    assert sucursal["status"] == 0


def test_reactivar_sucursal_vuelve_a_marcarla_activa(app):
    id_sucursal = crear_sucursal(name="Para reactivar")
    borrar_sucursal(id_sucursal)

    reactivar_sucursal(id_sucursal)

    assert obtener_por_id(id_sucursal)["status"] == 1


def test_sucursales_nuevas_se_agregan_al_final(app):
    primera = crear_sucursal(name="Primera")
    segunda = crear_sucursal(name="Segunda")

    orden = [s["id"] for s in listar_sucursales()]
    assert orden == [primera, segunda]


def test_reordenar_sucursales_aplica_el_orden_recibido(app):
    primera = crear_sucursal(name="Primera")
    segunda = crear_sucursal(name="Segunda")

    reordenar_sucursales([segunda, primera])

    orden = [s["id"] for s in listar_sucursales()]
    assert orden == [segunda, primera]


def test_reordenar_sucursales_ignora_ids_de_sucursales_borradas(app):
    """No debería poder colarse en el orden una sucursal que ya no está activa."""
    activa = crear_sucursal(name="Activa")
    borrada = crear_sucursal(name="Borrada")
    borrar_sucursal(borrada)

    reordenar_sucursales([borrada, activa])

    sucursal_borrada = obtener_por_id(borrada)
    assert sucursal_borrada["sort_order"] != 1
