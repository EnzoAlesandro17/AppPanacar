from src.db.connection import obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.validaciones.vehicle_brands.db import TABLA as TABLA_VEHICLE_BRANDS

TABLA = "vehicles"
TABLA_SUCURSALES = "vehicle_branches"


def crear_tabla():
    """Crea la tabla de vehículos si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                brand_id INTEGER NOT NULL REFERENCES {TABLA_VEHICLE_BRANDS}(id),
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                license_plate TEXT NOT NULL UNIQUE,
                color TEXT,
                chassis_number TEXT,
                engine_number TEXT,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_SUCURSALES} (
                id SERIAL PRIMARY KEY,
                vehicle_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                UNIQUE(vehicle_id, branch_id)
            )
            """
        )

        conexion.commit()
