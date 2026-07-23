from src.db.connection import obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.user.db import TABLA as TABLA_USERS

TABLA = "tasks"
TABLA_COMENTARIOS = "task_comments"
TABLA_ASIGNADOS = "task_assignees"
TABLA_SUCURSALES = "task_branches"
TABLA_VISTAS = "task_reads"


def crear_tabla():
    """Crea las tablas del tablón de tareas si no existen todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL REFERENCES {TABLA_USERS}(id),
                created_by_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_COMENTARIOS} (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                user_id INTEGER NOT NULL REFERENCES {TABLA_USERS}(id),
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_ASIGNADOS} (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                user_id INTEGER NOT NULL REFERENCES {TABLA_USERS}(id),
                UNIQUE(task_id, user_id)
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_SUCURSALES} (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                UNIQUE(task_id, branch_id)
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_VISTAS} (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                user_id INTEGER NOT NULL REFERENCES {TABLA_USERS}(id),
                last_seen_at TEXT NOT NULL,
                UNIQUE(task_id, user_id)
            )
            """
        )

        conexion.commit()
