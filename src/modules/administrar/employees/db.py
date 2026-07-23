from src.db.connection import columnas_existentes, obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES

TABLA = "employees"
TABLA_SUCURSALES = "employee_branches"


def crear_tabla():
    """Crea la tabla de empleados y la de su relación con sucursales (un
    empleado puede estar en una o varias) si no existen todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                position TEXT NOT NULL,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                dni TEXT NOT NULL UNIQUE,
                birth_date TEXT,
                email TEXT,
                phone TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = columnas_existentes(conexion, TABLA)
        if "sort_order" not in columnas:
            # Orden editable a mano (ver logic.py reordenar_*, drag&drop en el listado); arranca
            # respetando el orden alfabético (apellido, nombre) que tenía la lista hasta ahora.
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

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_SUCURSALES} (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                UNIQUE(employee_id, branch_id)
            )
            """
        )

        conexion.commit()
