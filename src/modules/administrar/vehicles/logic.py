import sqlite3

from src.constants.validations import validar_anio_vehiculo, validar_campos_obligatorios, validar_dominio
from src.db.connection import obtener_conexion
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.validaciones.vehicle_brands.db import TABLA as TABLA_VEHICLE_BRANDS
from src.modules.administrar.validaciones.vehicle_brands.logic import obtener_por_id as obtener_marca_por_id
from src.modules.administrar.vehicles.db import TABLA, TABLA_SUCURSALES


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


def _sincronizar_sucursales_vehiculo(conexion, id_vehiculo, branch_ids):
    """Reemplaza el set de sucursales asociadas a un vehículo por branch_ids.
    branch_ids=None no toca nada (se usa en updates parciales); una lista
    vacía borra todas las asociaciones."""
    if branch_ids is None:
        return

    for branch_id in branch_ids:
        sucursal = conexion.execute(
            f"SELECT id FROM {TABLA_BRANCHES} WHERE id = ? AND status = 1", (branch_id,)
        ).fetchone()
        if sucursal is None:
            raise ValidationError("Una de las sucursales indicadas no existe.")

    conexion.execute(f"DELETE FROM {TABLA_SUCURSALES} WHERE vehicle_id = ?", (id_vehiculo,))
    for branch_id in branch_ids:
        conexion.execute(
            f"INSERT INTO {TABLA_SUCURSALES} (vehicle_id, branch_id) VALUES (?, ?)",
            (id_vehiculo, branch_id),
        )


def obtener_sucursales_ids_vehiculo(id_vehiculo):
    """Ids de las sucursales asociadas a un vehículo."""
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            f"SELECT branch_id FROM {TABLA_SUCURSALES} WHERE vehicle_id = ?", (id_vehiculo,)
        ).fetchall()
        return [fila["branch_id"] for fila in filas]


def visible_para_sucursales(id_vehiculo, branch_ids_sesion):
    """True si el vehículo debería ser visible para alguien con esas sucursales.

    Un vehículo sin ninguna sucursal asignada queda visible para todos (dato
    sin asignar, no oculto); si tiene alguna, hace falta compartir al menos
    una con la sesión. branch_ids_sesion=None significa sin restricción."""
    if branch_ids_sesion is None:
        return True
    sucursales_vehiculo = obtener_sucursales_ids_vehiculo(id_vehiculo)
    if not sucursales_vehiculo:
        return True
    return any(branch_id in branch_ids_sesion for branch_id in sucursales_vehiculo)


def _buscar_borrado_por_dominio(conexion, dominio_normalizado):
    return conexion.execute(
        f"SELECT id FROM {TABLA} WHERE license_plate = ? AND status = 0", (dominio_normalizado,)
    ).fetchone()


def crear_vehiculo(brand_id, model, year, license_plate, color=None, chassis_number=None, engine_number=None,
                    branch_ids=None):
    """Valida y crea un vehículo nuevo. Devuelve el id generado.

    Si ya existe un vehículo borrado con ese mismo dominio, no crea uno
    nuevo: levanta RegistroBorradoExistente para que la vista ofrezca
    reactivar el que ya estaba en vez de chocar con el UNIQUE."""
    year_normalizado, dominio_normalizado = _validar_datos(brand_id, model, year, license_plate)

    with obtener_conexion() as conexion:
        borrado = _buscar_borrado_por_dominio(conexion, dominio_normalizado)
        if borrado is not None:
            raise RegistroBorradoExistente(borrado["id"])

        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (brand_id, model, year, license_plate, color, chassis_number, engine_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (brand_id, model, year_normalizado, dominio_normalizado, color, chassis_number, engine_number),
            )
            id_vehiculo = cursor.lastrowid
            _sincronizar_sucursales_vehiculo(conexion, id_vehiculo, branch_ids if branch_ids is not None else [])
            conexion.commit()
            return id_vehiculo
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_vehiculo):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_vehiculo,)).fetchone()


def listar_vehiculos(incluir_borrados=False, branch_ids=None):
    """branch_ids=None no filtra por sucursal. Si se pasa una lista, solo
    devuelve vehículos sin ninguna sucursal asignada (dato sin asignar,
    visible para todos) o que comparten alguna con branch_ids."""
    condiciones = []
    parametros = []

    if not incluir_borrados:
        condiciones.append(f"{TABLA}.status = 1")

    if branch_ids is not None:
        placeholders = ", ".join("?" for _ in branch_ids) if branch_ids else "NULL"
        condiciones.append(
            f"""(
                NOT EXISTS (SELECT 1 FROM {TABLA_SUCURSALES} WHERE {TABLA_SUCURSALES}.vehicle_id = {TABLA}.id)
                OR EXISTS (
                    SELECT 1 FROM {TABLA_SUCURSALES}
                    WHERE {TABLA_SUCURSALES}.vehicle_id = {TABLA}.id
                        AND {TABLA_SUCURSALES}.branch_id IN ({placeholders})
                )
            )"""
        )
        parametros.extend(branch_ids)

    consulta = f"""
        SELECT {TABLA}.*, {TABLA_VEHICLE_BRANDS}.name AS brand_name,
               GROUP_CONCAT({TABLA_BRANCHES}.name, ', ') AS branch_names
        FROM {TABLA}
        JOIN {TABLA_VEHICLE_BRANDS} ON {TABLA_VEHICLE_BRANDS}.id = {TABLA}.brand_id
        LEFT JOIN {TABLA_SUCURSALES} ON {TABLA_SUCURSALES}.vehicle_id = {TABLA}.id
        LEFT JOIN {TABLA_BRANCHES}
            ON {TABLA_BRANCHES}.id = {TABLA_SUCURSALES}.branch_id AND {TABLA_BRANCHES}.status = 1
    """
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += f" GROUP BY {TABLA}.id ORDER BY {TABLA_VEHICLE_BRANDS}.name, {TABLA}.model"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def actualizar_vehiculo(
    id_vehiculo, brand_id=None, model=None, year=None, license_plate=None,
    color=None, chassis_number=None, engine_number=None, branch_ids=None,
):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su
    valor actual. branch_ids=None mantiene las sucursales actuales; para
    vaciarlas pasar branch_ids=[]."""
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
            _sincronizar_sucursales_vehiculo(conexion, id_vehiculo, branch_ids)
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
