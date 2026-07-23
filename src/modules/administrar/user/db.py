from src.db.connection import columnas_existentes, obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.employees.db import TABLA as TABLA_EMPLOYEES

TABLA = "users"
TABLA_SUCURSALES = "user_branches"

_COLUMNAS_FINALES = f"""
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT NOT NULL DEFAULT 'Asesor',
    employee_id INTEGER REFERENCES {TABLA_EMPLOYEES}(id),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    theme TEXT NOT NULL DEFAULT 'light',
    status INTEGER NOT NULL DEFAULT 1
"""


def crear_tabla():
    """Crea la tabla de usuarios (acceso al sistema) si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(f"CREATE TABLE IF NOT EXISTS {TABLA} ({_COLUMNAS_FINALES})")

        columnas = columnas_existentes(conexion, TABLA)
        if "employee_id" not in columnas:
            conexion.execute(
                f"ALTER TABLE {TABLA} ADD COLUMN employee_id INTEGER REFERENCES {TABLA_EMPLOYEES}(id)"
            )
        if "sort_order" not in columnas:
            conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
        if "theme" not in columnas:
            conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN theme TEXT NOT NULL DEFAULT 'light'")

        # Rename de rol: "Admin" pasó a llamarse "IT". Update idempotente,
        # no hace nada una vez que ya no quedan filas con el nombre viejo.
        conexion.execute(f"UPDATE {TABLA} SET role = 'IT' WHERE role = 'Admin'")

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_SUCURSALES} (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                UNIQUE(user_id, branch_id)
            )
            """
        )

        conexion.commit()
