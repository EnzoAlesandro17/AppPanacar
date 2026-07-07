from src.db.connection import obtener_conexion

TABLA = "branches"


def crear_tabla():
    """Crea la tabla de sucursales si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                country TEXT,
                city TEXT,
                address TEXT,
                email TEXT,
                phone TEXT,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conexion.commit()
