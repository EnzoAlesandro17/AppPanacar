import sqlite3

from src.constants.validations import validar_campos_obligatorios
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.claim_statuses.db import TABLA


def _traducir_error_integridad(error):
    return ValidationError("Ya existe un estado con ese nombre.")


def crear_estado(name):
    """Valida y crea un estado de siniestro nuevo. Devuelve el id generado."""
    validar_campos_obligatorios({"name": name})

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (name, sort_order)
                VALUES (?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
                """,
                (name,),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_estado):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_estado,)).fetchone()


def listar_estados(incluir_borrados=False):
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY sort_order"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_estado(id_estado, name):
    """Actualiza el nombre de un estado existente."""
    if obtener_por_id(id_estado) is None:
        raise ValidationError("El estado no existe.")

    validar_campos_obligatorios({"name": name})

    with obtener_conexion() as conexion:
        try:
            conexion.execute(f"UPDATE {TABLA} SET name = ? WHERE id = ?", (name, id_estado))
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_estado(id_estado):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_estado,))
        conexion.commit()


def reactivar_estado(id_estado):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_estado,))
        conexion.commit()


def reordenar_estados(orden_ids):
    """Reasigna sort_order según el orden recibido (lista de ids), de arriba hacia abajo."""
    with obtener_conexion() as conexion:
        for posicion, id_estado in enumerate(orden_ids, start=1):
            conexion.execute(
                f"UPDATE {TABLA} SET sort_order = ? WHERE id = ? AND status = 1", (posicion, id_estado)
            )
        conexion.commit()
