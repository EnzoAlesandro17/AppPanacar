import sqlite3

from src.constants.validations import validar_campos_obligatorios
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.insurance_companies.db import TABLA


def _traducir_error_integridad(error):
    return ValidationError("Ya existe una compañía de seguro con ese nombre.")


def crear_aseguradora(name):
    """Valida y crea una compañía de seguro nueva. Devuelve el id generado."""
    validar_campos_obligatorios({"name": name})

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(f"INSERT INTO {TABLA} (name) VALUES (?)", (name,))
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_aseguradora):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_aseguradora,)).fetchone()


def listar_aseguradoras(incluir_borrados=False):
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY name"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_aseguradora(id_aseguradora, name):
    """Actualiza el nombre de una compañía de seguro existente."""
    if obtener_por_id(id_aseguradora) is None:
        raise ValidationError("La compañía de seguro no existe.")

    validar_campos_obligatorios({"name": name})

    with obtener_conexion() as conexion:
        try:
            conexion.execute(f"UPDATE {TABLA} SET name = ? WHERE id = ?", (name, id_aseguradora))
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_aseguradora(id_aseguradora):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_aseguradora,))
        conexion.commit()


def reactivar_aseguradora(id_aseguradora):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_aseguradora,))
        conexion.commit()
