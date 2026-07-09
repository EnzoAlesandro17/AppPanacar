from src.constants.validations import validar_campos_obligatorios
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.informacion_util.db import TABLA


def crear_enlace(label, url, observations=None):
    """Valida y crea un enlace nuevo. Devuelve el id generado."""
    validar_campos_obligatorios({"label": label, "url": url})

    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            f"""
            INSERT INTO {TABLA} (label, url, observations, sort_order)
            VALUES (?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
            """,
            (label, url, observations),
        )
        conexion.commit()
        return cursor.lastrowid


def obtener_por_id(id_enlace):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_enlace,)).fetchone()


def listar_enlaces(incluir_borrados=False):
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY sort_order"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def actualizar_enlace(id_enlace, label, url, observations=None):
    """Actualiza el texto, el link y las observaciones de un enlace existente."""
    if obtener_por_id(id_enlace) is None:
        raise ValidationError("El enlace no existe.")

    validar_campos_obligatorios({"label": label, "url": url})

    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET label = ?, url = ?, observations = ? WHERE id = ?",
            (label, url, observations, id_enlace),
        )
        conexion.commit()


def borrar_enlace(id_enlace):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_enlace,))
        conexion.commit()


def reactivar_enlace(id_enlace):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_enlace,))
        conexion.commit()


def reordenar_enlaces(orden_ids):
    """Reasigna sort_order según el orden recibido (lista de ids), de arriba hacia abajo."""
    with obtener_conexion() as conexion:
        for posicion, id_enlace in enumerate(orden_ids, start=1):
            conexion.execute(
                f"UPDATE {TABLA} SET sort_order = ? WHERE id = ? AND status = 1", (posicion, id_enlace)
            )
        conexion.commit()
