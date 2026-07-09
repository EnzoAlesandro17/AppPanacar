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
from src.exceptions import ValidationError
from src.modules.administrar.employees.db import TABLA


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


def crear_empleado(position, name, last_name, dni, birth_date=None, email=None, phone=None,
                    emergency_contact_name=None, emergency_contact_phone=None):
    """Valida y crea un empleado nuevo. Devuelve el id generado."""
    telefono_normalizado, contacto_telefono_normalizado = _validar_datos(
        position, name, last_name, dni, birth_date, email, phone,
        emergency_contact_name, emergency_contact_phone,
    )

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA}
                    (position, name, last_name, dni, birth_date, email, phone,
                     emergency_contact_name, emergency_contact_phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (position, name, last_name, dni, birth_date, email, telefono_normalizado,
                 emergency_contact_name, contacto_telefono_normalizado),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_empleado):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_empleado,)).fetchone()


def listar_empleados(incluir_borrados=False):
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY last_name, name"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_empleado(id_empleado, position=None, name=None, last_name=None, dni=None,
                         birth_date=None, email=None, phone=None,
                         emergency_contact_name=None, emergency_contact_phone=None):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual."""
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
