import sqlite3
import os
from contextlib import contextmanager

from src.config import DB_PATH

class GestorDB:
    @staticmethod
    def conectar():
        """Crea la carpeta si no existe, conecta y devuelve la conexión."""
        # Asegura que exista la carpeta 'data' definida en config
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conexion = sqlite3.connect(DB_PATH)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion


@contextmanager
def obtener_conexion():
    """Context manager que cierra la conexión automáticamente al salir del bloque."""
    conexion = GestorDB.conectar()
    try:
        yield conexion
    finally:
        conexion.close()