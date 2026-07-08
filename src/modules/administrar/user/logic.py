import hashlib
import os
import sqlite3
from datetime import datetime, timedelta

from src.constants.settings import Settings
from src.constants.validations import (
    validar_campos_obligatorios,
    validar_dni,
    validar_email,
    validar_fecha,
    validar_mayor_edad,
    validar_password,
    validar_telefono,
)
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import obtener_por_id as obtener_sucursal_por_id
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
    return hash_bytes.hex() == hash_hex


def _validar_branch_id(branch_id):
    if branch_id is None:
        return
    sucursal = obtener_sucursal_por_id(branch_id)
    if sucursal is None or sucursal["status"] == 0:
        raise ValidationError("La sucursal indicada no existe.")


def _validar_datos(name, last_name, dni, username, password, email, birth_date, phone, role, branch_id):
    validar_campos_obligatorios({"name": name, "last_name": last_name, "dni": dni})
    validar_dni(dni)

    if role not in ROLES:
        raise ValidationError(f"El rol debe ser uno de: {', '.join(ROLES)}.")

    if bool(username) != bool(password):
        raise ValidationError("Usuario y contraseña deben cargarse juntos, o dejarse los dos vacíos.")

    _validar_branch_id(branch_id)

    if email:
        validar_email(email)

    telefono_normalizado = validar_telefono(phone) if phone else None

    if birth_date:
        fecha = validar_fecha(birth_date)
        validar_mayor_edad(fecha)

    return telefono_normalizado


def _traducir_error_integridad(error):
    mensaje = str(error)
    if "code" in mensaje:
        return ValidationError("Ya existe un usuario con ese code.")
    if "dni" in mensaje:
        return ValidationError("Ya existe un usuario con ese DNI.")
    if "username" in mensaje:
        return ValidationError("Ese nombre de usuario ya está en uso.")
    return ValidationError("Ya existe un usuario con alguno de esos datos únicos.")


def crear_usuario(name, last_name, dni, code=None, username=None, password=None,
                   email=None, birth_date=None, phone=None, role="Asesor", branch_id=None):
    """Valida y crea un usuario nuevo. Devuelve el id generado."""
    telefono_normalizado = _validar_datos(
        name, last_name, dni, username, password, email, birth_date, phone, role, branch_id
    )
    if password:
        validar_password(password)

    contrasena_hasheada = _hashear_contrasena(password) if password else None

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA}
                    (code, name, last_name, dni, username, password, email, birth_date, phone, role,
                     branch_id, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
                """,
                (code, name, last_name, dni, username, contrasena_hasheada, email, birth_date,
                 telefono_normalizado, role, branch_id),
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
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY sort_order"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_usuario(id_usuario, name=None, last_name=None, dni=None, code=None,
                        username=None, password=None, email=None, birth_date=None, phone=None,
                        role=None, branch_id=None, quitar_branch_id=False):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual.

    branch_id=None mantiene la sucursal actual; para desasignarla explícitamente
    pasar quitar_branch_id=True.
    """
    usuario_actual = obtener_por_id(id_usuario)
    if usuario_actual is None:
        raise ValidationError("El usuario no existe.")

    nuevos = {
        "name": name if name is not None else usuario_actual["name"],
        "last_name": last_name if last_name is not None else usuario_actual["last_name"],
        "dni": dni if dni is not None else usuario_actual["dni"],
        "code": code if code is not None else usuario_actual["code"],
        "username": username if username is not None else usuario_actual["username"],
        "email": email if email is not None else usuario_actual["email"],
        "birth_date": birth_date if birth_date is not None else usuario_actual["birth_date"],
        "phone": phone if phone is not None else usuario_actual["phone"],
        "role": role if role is not None else usuario_actual["role"],
        "branch_id": None if quitar_branch_id else (
            branch_id if branch_id is not None else usuario_actual["branch_id"]
        ),
    }
    password_efectivo = password if password is not None else usuario_actual["password"]

    telefono_normalizado = _validar_datos(
        nuevos["name"], nuevos["last_name"], nuevos["dni"], nuevos["username"],
        password_efectivo, nuevos["email"], nuevos["birth_date"], nuevos["phone"], nuevos["role"],
        nuevos["branch_id"],
    )
    if password:
        validar_password(password)

    contrasena_hasheada = _hashear_contrasena(password) if password else usuario_actual["password"]

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET code = ?, name = ?, last_name = ?, dni = ?, username = ?,
                    password = ?, email = ?, birth_date = ?, phone = ?, role = ?, branch_id = ?
                WHERE id = ?
                """,
                (
                    nuevos["code"], nuevos["name"], nuevos["last_name"], nuevos["dni"],
                    nuevos["username"], contrasena_hasheada, nuevos["email"],
                    nuevos["birth_date"], telefono_normalizado, nuevos["role"], nuevos["branch_id"],
                    id_usuario,
                ),
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
