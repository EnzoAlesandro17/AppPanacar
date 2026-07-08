from src.db.connection import obtener_conexion
from src.modules.administrar.validaciones.insurance_companies.db import TABLA as TABLA_INSURANCE_COMPANIES

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
                insurance_company_id INTEGER REFERENCES {TABLA_INSURANCE_COMPANIES}(id),
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA})")]
        if "insurance_company_id" not in columnas:
            conexion.execute(
                f"ALTER TABLE {TABLA} "
                f"ADD COLUMN insurance_company_id INTEGER REFERENCES {TABLA_INSURANCE_COMPANIES}(id)"
            )

        conexion.commit()
