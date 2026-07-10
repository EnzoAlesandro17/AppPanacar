from src.db.connection import obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES

TABLA = "clients"
TABLA_SUCURSALES = "client_branches"


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

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA})")]
        if "insurance_company_id" in columnas:
            # La aseguradora se va a asociar al siniestro, no al cliente (ver RODO.txt).
            conexion.execute(f"ALTER TABLE {TABLA} DROP COLUMN insurance_company_id")

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_SUCURSALES} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                UNIQUE(client_id, branch_id)
            )
            """
        )

        conexion.commit()
