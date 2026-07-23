from src.db.connection import obtener_conexion
from src.modules.administrar.user.db import TABLA as TABLA_USERS

TABLA = "audit_log"


def crear_tabla():
    """Crea la tabla de bitácora (registro de actividad) si no existe todavía.

    No tiene borrado lógico ni CRUD: solo se inserta (registrar_evento) y se
    lista (listar_eventos), nunca se edita ni se borra un evento ya grabado.
    """
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                created_at TEXT NOT NULL,
                user_id INTEGER REFERENCES {TABLA_USERS}(id),
                username TEXT,
                ip_address TEXT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                category TEXT,
                message TEXT
            )
            """
        )
        conexion.commit()
