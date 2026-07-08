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
                sort_order INTEGER NOT NULL DEFAULT 0,
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

        if "sort_order" not in columnas:
            # Orden editable a mano (ver logic.py reordenar_*, drag&drop en el listado); arranca
            # respetando el orden alfabético (apellido, nombre) que tenía la lista.
            conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
            conexion.execute(
                f"""
                UPDATE {TABLA} SET sort_order = (
                    SELECT COUNT(*) FROM {TABLA} AS otra
                    WHERE otra.last_name < {TABLA}.last_name
                       OR (otra.last_name = {TABLA}.last_name AND otra.name < {TABLA}.name)
                       OR (otra.last_name = {TABLA}.last_name AND otra.name = {TABLA}.name
                           AND otra.id < {TABLA}.id)
                ) + 1
                """
            )

        conexion.commit()
