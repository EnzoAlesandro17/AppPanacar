from src.db.connection import obtener_conexion

TABLA = "products"


def crear_tabla():
    """Crea la tabla de productos si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT NOT NULL,
                description TEXT NOT NULL,
                stock INTEGER,
                wholesale_price REAL NOT NULL,
                retail_price REAL NOT NULL,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conexion.commit()
