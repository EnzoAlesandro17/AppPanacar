import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timedelta

from src.constants.settings import Settings
from src.constants.validations import validar_campos_obligatorios, validar_password
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.employees.db import TABLA as TABLA_EMPLOYEES
from src.modules.administrar.employees.logic import obtener_por_id as obtener_empleado_por_id
from src.modules.administrar.user.db import TABLA

_ITERACIONES_HASH = 100_000

ROLES = ("Admin", "BackOffice", "Asesor")


def _hashear_contrasena(contrasena):
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), salt, _ITERACIONES_HASH)
    return f"{salt.hex()}${hash_bytes.hex()}"


def _verificar_hash(contrasena, contrasena_guardada):
    salt_hex, hash_hex = contrasena_guardada.split("$")
    salt = bytes.fromhex(salt_hex)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), salt, _ITERACIONES_HASH)
    return hmac.compare_digest(hash_bytes.hex(), hash_hex)


def _validar_employee_id(employee_id):
    if employee_id is None:
        return
    empleado = obtener_empleado_por_id(employee_id)
    if empleado is None or empleado["status"] == 0:
        raise ValidationError("El empleado indicado no existe.")


def _validar_datos(username, password, role, employee_id):
    validar_campos_obligatorios({"username": username, "password": password})

    if role not in ROLES:
        raise ValidationError(f"El rol debe ser uno de: {', '.join(ROLES)}.")

    _validar_employee_id(employee_id)


def _traducir_error_integridad(error):
    return ValidationError("Ese nombre de usuario ya está en uso.")


def crear_usuario(username, password, role="Asesor", employee_id=None):
    """Valida y crea un usuario nuevo. Devuelve el id generado."""
    _validar_datos(username, password, role, employee_id)
    validar_password(password)

    contrasena_hasheada = _hashear_contrasena(password)

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (username, password, role, employee_id, sort_order)
                VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
                """,
                (username, contrasena_hasheada, role, employee_id),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_usuario):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_usuario,)).fetchone()


def obtener_por_username(username):
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"SELECT * FROM {TABLA} WHERE username = ?", (username,)
        ).fetchone()


def listar_usuarios(incluir_borrados=False):
    consulta = f"""
        SELECT {TABLA}.*, {TABLA_EMPLOYEES}.name AS employee_name,
               {TABLA_EMPLOYEES}.last_name AS employee_last_name
        FROM {TABLA}
        LEFT JOIN {TABLA_EMPLOYEES} ON {TABLA_EMPLOYEES}.id = {TABLA}.employee_id
    """
    if not incluir_borrados:
        consulta += f" WHERE {TABLA}.status = 1"
    consulta += f" ORDER BY {TABLA}.sort_order"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_usuario(id_usuario, username=None, password=None, role=None, employee_id=None,
                        quitar_employee_id=False):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual.

    employee_id=None mantiene el vínculo actual; para desvincularlo
    explícitamente pasar quitar_employee_id=True.
    """
    usuario_actual = obtener_por_id(id_usuario)
    if usuario_actual is None:
        raise ValidationError("El usuario no existe.")

    nuevos = {
        "username": username if username is not None else usuario_actual["username"],
        "role": role if role is not None else usuario_actual["role"],
        "employee_id": None if quitar_employee_id else (
            employee_id if employee_id is not None else usuario_actual["employee_id"]
        ),
    }
    password_efectivo = password if password is not None else usuario_actual["password"]

    _validar_datos(nuevos["username"], password_efectivo, nuevos["role"], nuevos["employee_id"])
    if password:
        validar_password(password)

    contrasena_hasheada = _hashear_contrasena(password) if password else usuario_actual["password"]

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"UPDATE {TABLA} SET username = ?, password = ?, role = ?, employee_id = ? WHERE id = ?",
                (nuevos["username"], contrasena_hasheada, nuevos["role"], nuevos["employee_id"], id_usuario),
            )
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_usuario(id_usuario):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_usuario,))
        conexion.commit()


def reactivar_usuario(id_usuario):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_usuario,))
        conexion.commit()


def reordenar_usuarios(orden_ids):
    """Reasigna sort_order según el orden recibido (lista de ids), de arriba hacia abajo."""
    with obtener_conexion() as conexion:
        for posicion, id_usuario in enumerate(orden_ids, start=1):
            conexion.execute(
                f"UPDATE {TABLA} SET sort_order = ? WHERE id = ? AND status = 1", (posicion, id_usuario)
            )
        conexion.commit()


def verificar_contrasena(username, password):
    """Para el futuro login: True si la contraseña coincide con la del usuario."""
    usuario = obtener_por_username(username)
    if usuario is None or usuario["password"] is None:
        return False
    return _verificar_hash(password, usuario["password"])


def _esta_bloqueado(usuario):
    """True si la cuenta sigue bloqueada por intentos fallidos.

    Si el bloqueo ya venció, limpia el contador y devuelve False.
    """
    if not usuario["locked_until"]:
        return False
    if datetime.now() < datetime.fromisoformat(usuario["locked_until"]):
        return True
    _resetear_intentos(usuario["id"])
    return False


def _registrar_intento_fallido(usuario):
    intentos = usuario["failed_attempts"] + 1
    locked_until = (
        (datetime.now() + timedelta(seconds=Settings.TIMEOUT_SECONDS)).isoformat()
        if intentos >= Settings.MAX_LOGIN_ATTEMPTS
        else None
    )
    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET failed_attempts = ?, locked_until = ? WHERE id = ?",
            (intentos, locked_until, usuario["id"]),
        )
        conexion.commit()


def _resetear_intentos(id_usuario):
    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (id_usuario,),
        )
        conexion.commit()


def iniciar_sesion(username, password):
    """Valida credenciales de login. Devuelve la fila del usuario si son correctas.

    Mensaje de error genérico a propósito, para no filtrar si falló el
    usuario o la contraseña. Tras MAX_LOGIN_ATTEMPTS intentos fallidos
    seguidos, la cuenta queda bloqueada por TIMEOUT_SECONDS.
    """
    usuario = obtener_por_username(username)
    if usuario is None or usuario["status"] == 0:
        raise ValidationError("Usuario o contraseña incorrectos.")

    if _esta_bloqueado(usuario):
        raise ValidationError(
            "Cuenta bloqueada temporalmente por demasiados intentos fallidos. Probá de nuevo en unos segundos."
        )

    if usuario["password"] is None or not _verificar_hash(password, usuario["password"]):
        _registrar_intento_fallido(usuario)
        raise ValidationError("Usuario o contraseña incorrectos.")

    _resetear_intentos(usuario["id"])
    return usuario
