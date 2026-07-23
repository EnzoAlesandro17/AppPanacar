from src.db.connection import obtener_conexion

TABLA = "claim_types"

# Carga inicial de tipos de siniestro habituales en un taller de chapería/pintura.
# Se insertan solo si no existen (ON CONFLICT DO NOTHING), mismo criterio que
# insurance_companies: no duplica los que ya estén cargados ni pisa los que el
# usuario haya borrado o editado.
_TIPOS_INICIALES = ("Choque", "Robo/Hurto", "Granizo", "Cristales", "Incendio", "Otro")


def crear_tabla():
    """Crea la tabla de tipos de siniestro si no existe todavía."""
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

        conexion.executemany(
            f"""
            INSERT INTO {TABLA} (name, sort_order)
            VALUES (?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM {TABLA}))
            ON CONFLICT(name) DO NOTHING
            """,
            [(nombre,) for nombre in _TIPOS_INICIALES],
        )

        conexion.commit()
