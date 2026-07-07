import sqlite3

from src.constants.validations import validar_campos_obligatorios, validar_email, validar_telefono
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.branches.db import TABLA


def _validar_datos(name, email, phone):
    validar_campos_obligatorios({"name": name})

    if email:
        validar_email(email)

    telefono_normalizado = validar_telefono(phone) if phone else None

    return telefono_normalizado


def _traducir_error_integridad(error):
    mensaje = str(error)
    if "code" in mensaje:
        return ValidationError("Ya existe una sucursal con ese code.")
    return ValidationError("Ya existe una sucursal con alguno de esos datos únicos.")


def crear_sucursal(name, code=None, country=None, city=None, address=None, email=None, phone=None):
    """Valida y crea una sucursal nueva. Devuelve el id generado."""
    telefono_normalizado = _validar_datos(name, email, phone)

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (code, name, country, city, address, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (code, name, country, city, address, email, telefono_normalizado),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_sucursal):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_sucursal,)).fetchone()


def obtener_por_code(code):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE code = ?", (code,)).fetchone()


def listar_sucursales(incluir_borrados=False):
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY name"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def buscar_por_nombre(texto):
    """Busca sucursales activas por coincidencia parcial en el nombre."""
    patron = f"%{texto}%"
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT * FROM {TABLA}
            WHERE status = 1 AND name LIKE ?
            ORDER BY name
            """,
            (patron,),
        ).fetchall()


def actualizar_sucursal(id_sucursal, name=None, code=None, country=None, city=None,
                         address=None, email=None, phone=None):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual."""
    sucursal_actual = obtener_por_id(id_sucursal)
    if sucursal_actual is None:
        raise ValidationError("La sucursal no existe.")

    nuevos = {
        "name": name if name is not None else sucursal_actual["name"],
        "code": code if code is not None else sucursal_actual["code"],
        "country": country if country is not None else sucursal_actual["country"],
        "city": city if city is not None else sucursal_actual["city"],
        "address": address if address is not None else sucursal_actual["address"],
        "email": email if email is not None else sucursal_actual["email"],
        "phone": phone if phone is not None else sucursal_actual["phone"],
    }

    telefono_normalizado = _validar_datos(nuevos["name"], nuevos["email"], nuevos["phone"])

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET code = ?, name = ?, country = ?, city = ?, address = ?, email = ?, phone = ?
                WHERE id = ?
                """,
                (nuevos["code"], nuevos["name"], nuevos["country"], nuevos["city"],
                 nuevos["address"], nuevos["email"], telefono_normalizado, id_sucursal),
            )
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_sucursal(id_sucursal):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_sucursal,))
        conexion.commit()


def reactivar_sucursal(id_sucursal):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_sucursal,))
        conexion.commit()
