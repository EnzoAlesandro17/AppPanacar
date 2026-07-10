from datetime import datetime

from src.constants.validations import validar_campos_obligatorios
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.tasks.db import (
    TABLA,
    TABLA_ASIGNADOS,
    TABLA_COMENTARIOS,
    TABLA_SUCURSALES,
    TABLA_VISTAS,
)
from src.modules.administrar.user.db import TABLA as TABLA_USERS


def _ahora():
    return datetime.now().isoformat()


def _sincronizar_sucursales_tarea(conexion, id_tarea, branch_ids):
    """Reemplaza el set de sucursales asociadas a una tarea por branch_ids.
    branch_ids=None no toca nada; una lista vacía borra todas las asociaciones."""
    if branch_ids is None:
        return

    for branch_id in branch_ids:
        sucursal = conexion.execute(
            f"SELECT id FROM {TABLA_BRANCHES} WHERE id = ? AND status = 1", (branch_id,)
        ).fetchone()
        if sucursal is None:
            raise ValidationError("Una de las sucursales indicadas no existe.")

    conexion.execute(f"DELETE FROM {TABLA_SUCURSALES} WHERE task_id = ?", (id_tarea,))
    for branch_id in branch_ids:
        conexion.execute(
            f"INSERT INTO {TABLA_SUCURSALES} (task_id, branch_id) VALUES (?, ?)",
            (id_tarea, branch_id),
        )


def _sincronizar_asignados(conexion, id_tarea, assignee_ids):
    """Reemplaza el set de usuarios asignados a una tarea por assignee_ids.
    assignee_ids=None no toca nada; una lista vacía borra todas las asociaciones."""
    if assignee_ids is None:
        return

    for user_id in assignee_ids:
        usuario = conexion.execute(
            f"SELECT id FROM {TABLA_USERS} WHERE id = ? AND status = 1", (user_id,)
        ).fetchone()
        if usuario is None:
            raise ValidationError("Uno de los usuarios asignados no existe.")

    conexion.execute(f"DELETE FROM {TABLA_ASIGNADOS} WHERE task_id = ?", (id_tarea,))
    for user_id in assignee_ids:
        conexion.execute(
            f"INSERT INTO {TABLA_ASIGNADOS} (task_id, user_id) VALUES (?, ?)",
            (id_tarea, user_id),
        )


def obtener_sucursales_ids_tarea(id_tarea):
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            f"SELECT branch_id FROM {TABLA_SUCURSALES} WHERE task_id = ?", (id_tarea,)
        ).fetchall()
        return [fila["branch_id"] for fila in filas]


def obtener_asignados_ids(id_tarea):
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            f"SELECT user_id FROM {TABLA_ASIGNADOS} WHERE task_id = ?", (id_tarea,)
        ).fetchall()
        return [fila["user_id"] for fila in filas]


def visible_para_sucursales(id_tarea, branch_ids_sesion):
    """True si la tarea debería ser visible para alguien con esas sucursales.

    Una tarea sin ninguna sucursal asignada queda visible para todos (dato
    sin asignar, no oculto); si tiene alguna, hace falta compartir al menos
    una con la sesión. branch_ids_sesion=None significa sin restricción."""
    if branch_ids_sesion is None:
        return True
    sucursales_tarea = obtener_sucursales_ids_tarea(id_tarea)
    if not sucursales_tarea:
        return True
    return any(branch_id in branch_ids_sesion for branch_id in sucursales_tarea)


def crear_tarea(title, description, created_by, created_by_username, branch_ids=None, assignee_ids=None):
    """Valida y crea una tarea nueva. Devuelve el id generado."""
    validar_campos_obligatorios({"title": title})

    ahora = _ahora()
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            f"""
            INSERT INTO {TABLA} (title, description, created_by, created_by_username, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, created_by, created_by_username, ahora, ahora),
        )
        id_tarea = cursor.lastrowid
        _sincronizar_sucursales_tarea(conexion, id_tarea, branch_ids if branch_ids is not None else [])
        _sincronizar_asignados(conexion, id_tarea, assignee_ids if assignee_ids is not None else [])
        conexion.commit()
        return id_tarea


def obtener_por_id(id_tarea):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_tarea,)).fetchone()


def listar_tareas(incluir_cerradas=False, branch_ids=None):
    """branch_ids=None no filtra por sucursal. Si se pasa una lista, solo
    devuelve tareas sin ninguna sucursal asignada (visibles para todos) o
    que comparten alguna con branch_ids."""
    condiciones = []
    parametros = []

    if not incluir_cerradas:
        condiciones.append(f"{TABLA}.closed_at IS NULL")
    else:
        condiciones.append(f"{TABLA}.closed_at IS NOT NULL")

    if branch_ids is not None:
        placeholders = ", ".join("?" for _ in branch_ids) if branch_ids else "NULL"
        condiciones.append(
            f"""(
                NOT EXISTS (SELECT 1 FROM {TABLA_SUCURSALES} WHERE {TABLA_SUCURSALES}.task_id = {TABLA}.id)
                OR EXISTS (
                    SELECT 1 FROM {TABLA_SUCURSALES}
                    WHERE {TABLA_SUCURSALES}.task_id = {TABLA}.id
                        AND {TABLA_SUCURSALES}.branch_id IN ({placeholders})
                )
            )"""
        )
        parametros.extend(branch_ids)

    consulta = f"""
        SELECT {TABLA}.*, GROUP_CONCAT(DISTINCT {TABLA_BRANCHES}.name) AS branch_names,
               GROUP_CONCAT(DISTINCT {TABLA_USERS}.username) AS assignee_names
        FROM {TABLA}
        LEFT JOIN {TABLA_SUCURSALES} ON {TABLA_SUCURSALES}.task_id = {TABLA}.id
        LEFT JOIN {TABLA_BRANCHES}
            ON {TABLA_BRANCHES}.id = {TABLA_SUCURSALES}.branch_id AND {TABLA_BRANCHES}.status = 1
        LEFT JOIN {TABLA_ASIGNADOS} ON {TABLA_ASIGNADOS}.task_id = {TABLA}.id
        LEFT JOIN {TABLA_USERS}
            ON {TABLA_USERS}.id = {TABLA_ASIGNADOS}.user_id AND {TABLA_USERS}.status = 1
    """
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += f" GROUP BY {TABLA}.id ORDER BY {TABLA}.updated_at DESC"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def agregar_comentario(task_id, user_id, username, message):
    validar_campos_obligatorios({"message": message})
    if obtener_por_id(task_id) is None:
        raise ValidationError("La tarea no existe.")

    ahora = _ahora()
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            INSERT INTO {TABLA_COMENTARIOS} (task_id, user_id, username, created_at, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, user_id, username, ahora, message),
        )
        conexion.execute(f"UPDATE {TABLA} SET updated_at = ? WHERE id = ?", (ahora, task_id))
        conexion.commit()


def listar_comentarios(task_id):
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"SELECT * FROM {TABLA_COMENTARIOS} WHERE task_id = ? ORDER BY id", (task_id,)
        ).fetchall()


def cerrar_tarea(task_id):
    """Cierra la tarea (queda disponible reabrir_tarea para revertir)."""
    ahora = _ahora()
    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET closed_at = ?, updated_at = ? WHERE id = ?", (ahora, ahora, task_id)
        )
        conexion.commit()


def reabrir_tarea(task_id):
    """Revierte el cierre: vuelve a marcar la tarea como abierta."""
    ahora = _ahora()
    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET closed_at = NULL, updated_at = ? WHERE id = ?", (ahora, task_id)
        )
        conexion.commit()


def marcar_vista(task_id, user_id):
    """Registra que user_id vio la tarea recién ahora (upsert)."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            INSERT INTO {TABLA_VISTAS} (task_id, user_id, last_seen_at)
            VALUES (?, ?, ?)
            ON CONFLICT(task_id, user_id) DO UPDATE SET last_seen_at = excluded.last_seen_at
            """,
            (task_id, user_id, _ahora()),
        )
        conexion.commit()


def contar_no_vistas(user_id, branch_ids=None):
    """Cantidad de tareas visibles para el usuario (según sus sucursales) con
    actividad posterior a la última vez que las vio (o nunca vistas)."""
    condiciones = ["1 = 1"]
    parametros = []

    if branch_ids is not None:
        placeholders = ", ".join("?" for _ in branch_ids) if branch_ids else "NULL"
        condiciones.append(
            f"""(
                NOT EXISTS (SELECT 1 FROM {TABLA_SUCURSALES} WHERE {TABLA_SUCURSALES}.task_id = {TABLA}.id)
                OR EXISTS (
                    SELECT 1 FROM {TABLA_SUCURSALES}
                    WHERE {TABLA_SUCURSALES}.task_id = {TABLA}.id
                        AND {TABLA_SUCURSALES}.branch_id IN ({placeholders})
                )
            )"""
        )
        parametros.extend(branch_ids)

    consulta = f"""
        SELECT COUNT(*) AS cantidad
        FROM {TABLA}
        LEFT JOIN {TABLA_VISTAS} ON {TABLA_VISTAS}.task_id = {TABLA}.id AND {TABLA_VISTAS}.user_id = ?
        WHERE {" AND ".join(condiciones)}
            AND (
                {TABLA_VISTAS}.last_seen_at IS NULL
                OR {TABLA}.updated_at > {TABLA_VISTAS}.last_seen_at
            )
    """

    with obtener_conexion() as conexion:
        fila = conexion.execute(consulta, [user_id, *parametros]).fetchone()
        return fila["cantidad"]
