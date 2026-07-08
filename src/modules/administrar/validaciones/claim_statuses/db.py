from src.db.connection import obtener_conexion

TABLA = "claim_statuses"


def crear_tabla():
    """Crea la tabla de estados de siniestro si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA})")]
        if "sort_order" not in columnas:
            # Orden editable a mano (ver logic.py reordenar_*, drag&drop en el listado); arranca
            # respetando el orden alfabético que tenía la lista hasta ahora.
            conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
            conexion.execute(
                f"""
                UPDATE {TABLA} SET sort_order = (
                    SELECT COUNT(*) FROM {TABLA} AS otra
                    WHERE otra.name < {TABLA}.name
                       OR (otra.name = {TABLA}.name AND otra.id < {TABLA}.id)
                ) + 1
                """
            )

        conexion.commit()
