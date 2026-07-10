import sqlite3

from src.constants.validations import (
    validar_campos_obligatorios,
    validar_dni,
    validar_email,
    validar_fecha,
    validar_mayor_edad,
    validar_telefono,
)
from src.db.connection import obtener_conexion
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.employees.db import TABLA, TABLA_SUCURSALES


def _validar_datos(position, name, last_name, dni, birth_date, email, phone,
                    emergency_contact_name, emergency_contact_phone):
    validar_campos_obligatorios({"position": position, "name": name, "last_name": last_name, "dni": dni})
    validar_dni(dni)

    if email:
        validar_email(email)

    telefono_normalizado = validar_telefono(phone) if phone else None
    contacto_telefono_normalizado = (
        validar_telefono(emergency_contact_phone) if emergency_contact_phone else None
    )

    if birth_date:
        fecha = validar_fecha(birth_date)
        validar_mayor_edad(fecha)

    return telefono_normalizado, contacto_telefono_normalizado


def _traducir_error_integridad(error):
    return ValidationError("Ya existe un empleado con ese DNI.")


def _sincronizar_sucursales(conexion, id_empleado, branch_ids):
    """Reemplaza el set de sucursales asociadas a un empleado por branch_ids.
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

    conexion.execute(f"DELETE FROM {TABLA_SUCURSALES} WHERE employee_id = ?", (id_empleado,))
    for branch_id in branch_ids:
        conexion.execute(
            f"INSERT INTO {TABLA_SUCURSALES} (employee_id, branch_id) VALUES (?, ?)",
            (id_empleado, branch_id),
        )


def obtener_sucursales_ids(id_empleado):
    """Ids de las sucursales asociadas a un empleado."""
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            f"SELECT branch_id FROM {TABLA_SUCURSALES} WHERE employee_id = ?", (id_empleado,)
        ).fetchall()
        return [fila["branch_id"] for fila in filas]


def obtener_sucursales(id_empleado):
    """Filas completas de las sucursales asociadas a un empleado (para mostrar nombre, etc.)."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT {TABLA_BRANCHES}.*
            FROM {TABLA_SUCURSALES}
            JOIN {TABLA_BRANCHES} ON {TABLA_BRANCHES}.id = {TABLA_SUCURSALES}.branch_id
            WHERE {TABLA_SUCURSALES}.employee_id = ?
            ORDER BY {TABLA_BRANCHES}.name
            """,
            (id_empleado,),
        ).fetchall()


def _buscar_borrado_por_dni(conexion, dni):
    return conexion.execute(f"SELECT id FROM {TABLA} WHERE dni = ? AND status = 0", (dni,)).fetchone()


def crear_empleado(position, name, last_name, dni, birth_date=None, email=None, phone=None,
                    emergency_contact_name=None, emergency_contact_phone=None, branch_ids=None):
    """Valida y crea un empleado nuevo. Devuelve el id generado.

    Si ya existe un empleado borrado con ese mismo DNI, no crea uno nuevo:
    levanta RegistroBorradoExistente para que la vista ofrezca reactivar el
    que ya estaba en vez de chocar con el UNIQUE."""
    telefono_normalizado, contacto_telefono_normalizado = _validar_datos(
        position, name, last_name, dni, birth_date, email, phone,
        emergency_contact_name, emergency_contact_phone,
    )

    with obtener_conexion() as conexion:
        borrado = _buscar_borrado_por_dni(conexion, dni)
        if borrado is not None:
            raise RegistroBorradoExistente(borrado["id"])

        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA}
                    (position, name, last_name, dni, birth_date, email, phone,
                     emergency_contact_name, emergency_contact_phone, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
                """,
                (position, name, last_name, dni, birth_date, email, telefono_normalizado,
                 emergency_contact_name, contacto_telefono_normalizado),
            )
            id_empleado = cursor.lastrowid
            _sincronizar_sucursales(conexion, id_empleado, branch_ids if branch_ids is not None else [])
            conexion.commit()
            return id_empleado
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_empleado):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_empleado,)).fetchone()


def listar_empleados(incluir_borrados=False):
    consulta = f"""
        SELECT {TABLA}.*, GROUP_CONCAT({TABLA_BRANCHES}.name, ', ') AS branch_names
        FROM {TABLA}
        LEFT JOIN {TABLA_SUCURSALES} ON {TABLA_SUCURSALES}.employee_id = {TABLA}.id
        LEFT JOIN {TABLA_BRANCHES}
            ON {TABLA_BRANCHES}.id = {TABLA_SUCURSALES}.branch_id AND {TABLA_BRANCHES}.status = 1
    """
    if not incluir_borrados:
        consulta += f" WHERE {TABLA}.status = 1"
    consulta += f" GROUP BY {TABLA}.id ORDER BY {TABLA}.sort_order"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_empleado(id_empleado, position=None, name=None, last_name=None, dni=None,
                         birth_date=None, email=None, phone=None,
                         emergency_contact_name=None, emergency_contact_phone=None, branch_ids=None):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su
    valor actual. branch_ids=None mantiene las sucursales actuales; para
    vaciarlas pasar branch_ids=[]."""
    empleado_actual = obtener_por_id(id_empleado)
    if empleado_actual is None:
        raise ValidationError("El empleado no existe.")

    nuevos = {
        "position": position if position is not None else empleado_actual["position"],
        "name": name if name is not None else empleado_actual["name"],
        "last_name": last_name if last_name is not None else empleado_actual["last_name"],
        "dni": dni if dni is not None else empleado_actual["dni"],
        "birth_date": birth_date if birth_date is not None else empleado_actual["birth_date"],
        "email": email if email is not None else empleado_actual["email"],
        "phone": phone if phone is not None else empleado_actual["phone"],
        "emergency_contact_name": (
            emergency_contact_name if emergency_contact_name is not None
            else empleado_actual["emergency_contact_name"]
        ),
        "emergency_contact_phone": (
            emergency_contact_phone if emergency_contact_phone is not None
            else empleado_actual["emergency_contact_phone"]
        ),
    }

    telefono_normalizado, contacto_telefono_normalizado = _validar_datos(
        nuevos["position"], nuevos["name"], nuevos["last_name"], nuevos["dni"], nuevos["birth_date"],
        nuevos["email"], nuevos["phone"], nuevos["emergency_contact_name"], nuevos["emergency_contact_phone"],
    )

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET position = ?, name = ?, last_name = ?, dni = ?, birth_date = ?, email = ?,
                    phone = ?, emergency_contact_name = ?, emergency_contact_phone = ?
                WHERE id = ?
                """,
                (nuevos["position"], nuevos["name"], nuevos["last_name"], nuevos["dni"],
                 nuevos["birth_date"], nuevos["email"], telefono_normalizado,
                 nuevos["emergency_contact_name"], contacto_telefono_normalizado, id_empleado),
            )
            _sincronizar_sucursales(conexion, id_empleado, branch_ids)
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_empleado(id_empleado):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_empleado,))
        conexion.commit()


def reactivar_empleado(id_empleado):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_empleado,))
        conexion.commit()


def reordenar_empleados(orden_ids):
    """Reasigna sort_order según el orden recibido (lista de ids), de arriba hacia abajo."""
    with obtener_conexion() as conexion:
        for posicion, id_empleado in enumerate(orden_ids, start=1):
            conexion.execute(
                f"UPDATE {TABLA} SET sort_order = ? WHERE id = ? AND status = 1", (posicion, id_empleado)
            )
        conexion.commit()
