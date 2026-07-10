from datetime import datetime

from src.db.connection import obtener_conexion
from src.modules.administrar.bitacora.db import TABLA


def registrar_evento(user_id, username, ip_address, method, path, category=None, message=None):
    """Graba una fila en la bitácora. No valida ni falla: un problema acá no
    debería tirar abajo el request real que se está atendiendo."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            INSERT INTO {TABLA} (created_at, user_id, username, ip_address, method, path, category, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (datetime.now().isoformat(), user_id, username, ip_address, method, path, category, message),
        )
        conexion.commit()


def listar_eventos(limite=200):
    """Últimos eventos, más reciente primero."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"SELECT * FROM {TABLA} ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
