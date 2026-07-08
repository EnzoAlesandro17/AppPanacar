from src.db.connection import obtener_conexion

TABLA = "users"


def crear_tabla():
    """Crea la tabla de usuarios si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                dni TEXT NOT NULL UNIQUE,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                birth_date TEXT,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'Asesor',
                branch_id INTEGER REFERENCES branches(id),
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA})")]
        columnas_nuevas = {
            "branch_id": "INTEGER REFERENCES branches(id)",
            "failed_attempts": "INTEGER NOT NULL DEFAULT 0",
            "locked_until": "TEXT",
        }
        for columna, definicion in columnas_nuevas.items():
            if columna not in columnas:
                conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN {columna} {definicion}")

        conexion.commit()
