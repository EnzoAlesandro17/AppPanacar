from src.db.connection import obtener_conexion

TABLA = "clients"


def crear_tabla():
    """Crea la tabla de clientes si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                dni_cuit TEXT NOT NULL UNIQUE,
                phone TEXT,
                email TEXT,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conexion.commit()
