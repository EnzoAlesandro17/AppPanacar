from src.db.connection import obtener_conexion

TABLA = "insurance_companies"


def crear_tabla():
    """Crea la tabla de compañías de seguro si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conexion.commit()
