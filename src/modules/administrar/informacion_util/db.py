from src.db.connection import columnas_existentes, obtener_conexion

TABLA = "useful_links"


def crear_tabla():
    """Crea la tabla de Links útiles si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                label TEXT NOT NULL,
                url TEXT NOT NULL,
                observations TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = columnas_existentes(conexion, TABLA)
        if "observations" not in columnas:
            conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN observations TEXT")

        conexion.commit()
