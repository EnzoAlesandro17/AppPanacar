from src.db.connection import obtener_conexion

TABLA = "employees"


def crear_tabla():
    """Crea la tabla de empleados si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position TEXT NOT NULL,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                dni TEXT NOT NULL UNIQUE,
                birth_date TEXT,
                email TEXT,
                phone TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conexion.commit()
