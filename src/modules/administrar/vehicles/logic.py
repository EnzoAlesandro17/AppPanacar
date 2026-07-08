import sqlite3

from src.constants.validations import validar_anio_vehiculo, validar_campos_obligatorios, validar_dominio
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.vehicle_brands.db import TABLA as TABLA_VEHICLE_BRANDS
from src.modules.administrar.validaciones.vehicle_brands.logic import obtener_por_id as obtener_marca_por_id
from src.modules.administrar.vehicles.db import TABLA


def _validar_datos(brand_id, model, year, license_plate):
    validar_campos_obligatorios(
        {"brand_id": brand_id, "model": model, "year": year, "license_plate": license_plate}
    )

    marca = obtener_marca_por_id(brand_id)
    if marca is None or marca["status"] == 0:
        raise ValidationError("La marca de vehículo indicada no existe.")

    year_normalizado = validar_anio_vehiculo(year)
    dominio_normalizado = validar_dominio(license_plate)
    return year_normalizado, dominio_normalizado


def _traducir_error_integridad(error):
    return ValidationError("Ya existe un vehículo con ese dominio.")


def crear_vehiculo(brand_id, model, year, license_plate, color=None, chassis_number=None, engine_number=None):
    """Valida y crea un vehículo nuevo. Devuelve el id generado."""
    year_normalizado, dominio_normalizado = _validar_datos(brand_id, model, year, license_plate)

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (brand_id, model, year, license_plate, color, chassis_number, engine_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (brand_id, model, year_normalizado, dominio_normalizado, color, chassis_number, engine_number),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_vehiculo):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_vehiculo,)).fetchone()


def listar_vehiculos(incluir_borrados=False):
    consulta = f"""
        SELECT {TABLA}.*, {TABLA_VEHICLE_BRANDS}.name AS brand_name
        FROM {TABLA}
        JOIN {TABLA_VEHICLE_BRANDS} ON {TABLA_VEHICLE_BRANDS}.id = {TABLA}.brand_id
    """
    if not incluir_borrados:
        consulta += f" WHERE {TABLA}.status = 1"
    consulta += f" ORDER BY {TABLA_VEHICLE_BRANDS}.name, {TABLA}.model"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_vehiculo(
    id_vehiculo, brand_id=None, model=None, year=None, license_plate=None,
    color=None, chassis_number=None, engine_number=None,
):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual."""
    vehiculo_actual = obtener_por_id(id_vehiculo)
    if vehiculo_actual is None:
        raise ValidationError("El vehículo no existe.")

    nuevos = {
        "brand_id": brand_id if brand_id is not None else vehiculo_actual["brand_id"],
        "model": model if model is not None else vehiculo_actual["model"],
        "year": year if year is not None else vehiculo_actual["year"],
        "license_plate": license_plate if license_plate is not None else vehiculo_actual["license_plate"],
        "color": color if color is not None else vehiculo_actual["color"],
        "chassis_number": chassis_number if chassis_number is not None else vehiculo_actual["chassis_number"],
        "engine_number": engine_number if engine_number is not None else vehiculo_actual["engine_number"],
    }

    year_normalizado, dominio_normalizado = _validar_datos(
        nuevos["brand_id"], nuevos["model"], nuevos["year"], nuevos["license_plate"],
    )

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET brand_id = ?, model = ?, year = ?, license_plate = ?,
                    color = ?, chassis_number = ?, engine_number = ?
                WHERE id = ?
                """,
                (nuevos["brand_id"], nuevos["model"], year_normalizado, dominio_normalizado,
                 nuevos["color"], nuevos["chassis_number"], nuevos["engine_number"], id_vehiculo),
            )
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_vehiculo(id_vehiculo):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_vehiculo,))
        conexion.commit()


def reactivar_vehiculo(id_vehiculo):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_vehiculo,))
        conexion.commit()
