import sqlite3

from src.constants.validations import (
    limpiar_documento,
    validar_campos_obligatorios,
    validar_documento,
    validar_email,
    validar_telefono,
)
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.clients.db import TABLA
from src.modules.administrar.validaciones.insurance_companies.db import TABLA as TABLA_INSURANCE_COMPANIES
from src.modules.administrar.validaciones.insurance_companies.logic import (
    obtener_por_id as obtener_aseguradora_por_id,
)


def _validar_insurance_company_id(insurance_company_id):
    if insurance_company_id is None:
        return
    aseguradora = obtener_aseguradora_por_id(insurance_company_id)
    if aseguradora is None or aseguradora["status"] == 0:
        raise ValidationError("La compañía de seguro indicada no existe.")


def _validar_datos(name, last_name, dni_cuit, phone, email, insurance_company_id):
    validar_campos_obligatorios({"name": name, "last_name": last_name, "dni_cuit": dni_cuit})

    dni_cuit_normalizado = validar_documento(dni_cuit)

    if email:
        validar_email(email)

    telefono_normalizado = validar_telefono(phone) if phone else None

    _validar_insurance_company_id(insurance_company_id)

    return dni_cuit_normalizado, telefono_normalizado


def _traducir_error_integridad(error):
    mensaje = str(error)
    if "dni_cuit" in mensaje:
        return ValidationError("Ya existe un cliente con ese DNI/CUIT.")
    return ValidationError("Ya existe un cliente con alguno de esos datos únicos.")


def crear_cliente(name, last_name, dni_cuit, phone=None, email=None, insurance_company_id=None):
    """Valida y crea un cliente nuevo. Devuelve el id generado."""
    dni_cuit_normalizado, telefono_normalizado = _validar_datos(
        name, last_name, dni_cuit, phone, email, insurance_company_id
    )

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (name, last_name, dni_cuit, phone, email, insurance_company_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, last_name, dni_cuit_normalizado, telefono_normalizado, email, insurance_company_id),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_cliente):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_cliente,)).fetchone()


def obtener_por_dni_cuit(dni_cuit):
    limpio = limpiar_documento(dni_cuit)
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE dni_cuit = ?", (limpio,)).fetchone()


def listar_clientes(incluir_borrados=False):
    consulta = f"""
        SELECT {TABLA}.*, {TABLA_INSURANCE_COMPANIES}.name AS insurance_company_name
        FROM {TABLA}
        LEFT JOIN {TABLA_INSURANCE_COMPANIES}
            ON {TABLA_INSURANCE_COMPANIES}.id = {TABLA}.insurance_company_id
    """
    if not incluir_borrados:
        consulta += f" WHERE {TABLA}.status = 1"
    consulta += f" ORDER BY {TABLA}.last_name, {TABLA}.name"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def buscar_por_nombre(texto):
    """Busca clientes activos por coincidencia parcial en nombre o apellido."""
    patron = f"%{texto}%"
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT * FROM {TABLA}
            WHERE status = 1 AND (name LIKE ? OR last_name LIKE ?)
            ORDER BY last_name, name
            """,
            (patron, patron),
        ).fetchall()


def actualizar_cliente(id_cliente, name=None, last_name=None, dni_cuit=None, phone=None, email=None,
                        insurance_company_id=None, quitar_insurance_company_id=False):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual.

    insurance_company_id=None mantiene la aseguradora actual; para desasignarla
    explícitamente pasar quitar_insurance_company_id=True.
    """
    cliente_actual = obtener_por_id(id_cliente)
    if cliente_actual is None:
        raise ValidationError("El cliente no existe.")

    nuevos = {
        "name": name if name is not None else cliente_actual["name"],
        "last_name": last_name if last_name is not None else cliente_actual["last_name"],
        "dni_cuit": dni_cuit if dni_cuit is not None else cliente_actual["dni_cuit"],
        "phone": phone if phone is not None else cliente_actual["phone"],
        "email": email if email is not None else cliente_actual["email"],
        "insurance_company_id": None if quitar_insurance_company_id else (
            insurance_company_id if insurance_company_id is not None else cliente_actual["insurance_company_id"]
        ),
    }

    dni_cuit_normalizado, telefono_normalizado = _validar_datos(
        nuevos["name"], nuevos["last_name"], nuevos["dni_cuit"], nuevos["phone"], nuevos["email"],
        nuevos["insurance_company_id"],
    )

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET name = ?, last_name = ?, dni_cuit = ?, phone = ?, email = ?, insurance_company_id = ?
                WHERE id = ?
                """,
                (nuevos["name"], nuevos["last_name"], dni_cuit_normalizado, telefono_normalizado,
                 nuevos["email"], nuevos["insurance_company_id"], id_cliente),
            )
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_cliente(id_cliente):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_cliente,))
        conexion.commit()


def reactivar_cliente(id_cliente):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_cliente,))
        conexion.commit()
