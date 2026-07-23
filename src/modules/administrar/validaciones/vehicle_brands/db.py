from src.db.connection import columnas_existentes, obtener_conexion

TABLA = "vehicle_brands"

# Carga inicial de marcas conocidas en el mercado argentino. Se insertan solo
# si no existen (ON CONFLICT DO NOTHING), así no duplica las que ya estén
# cargadas ni pisa las que el usuario haya borrado o editado.
_MARCAS_INICIALES = (
    "Alfa Romeo", "Audi", "BAIC", "BMW", "BYD", "Chery", "Chevrolet",
    "Chrysler", "Citroën", "DFSK", "Dodge", "DS", "Fiat", "Ford", "Foton",
    "Geely", "Great Wall", "Haval", "Honda", "Hyundai", "Isuzu", "Iveco",
    "JAC", "Jeep", "JMC", "Kia", "Lifan", "Mercedes-Benz", "MG", "Mini",
    "Mitsubishi", "Nissan", "Peugeot", "Porsche", "RAM", "Renault", "SEAT",
    "Škoda", "Smart", "SsangYong", "Subaru", "Suzuki", "Toyota",
    "Volkswagen", "Volvo",
)


def crear_tabla():
    """Crea la tabla de marcas de vehículos si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = columnas_existentes(conexion, TABLA)
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

        conexion.executemany(
            f"""
            INSERT INTO {TABLA} (name, sort_order)
            VALUES (?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
            ON CONFLICT(name) DO NOTHING
            """,
            [(nombre,) for nombre in _MARCAS_INICIALES],
        )

        conexion.commit()
