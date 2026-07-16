from src.db.connection import obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.employees.db import TABLA as TABLA_EMPLOYEES

TABLA = "users"
TABLA_SUCURSALES = "user_branches"

_COLUMNAS_FINALES = f"""
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA})")]

        # Migración única: antes `users` mezclaba los datos personales
        # (name/last_name/dni/code/email/birth_date/phone/branch_id) con el
        # login. Ahora esos datos viven en employees y cada usuario se
        # linkea vía employee_id. Corre una sola vez, si detecta el esquema
        # viejo (columna `name` todavía presente).
        if "name" in columnas:
            _migrar_tabla_vieja(conexion)
        else:
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                UNIQUE(user_id, branch_id)
            )
            """
        )

        conexion.commit()


def _migrar_tabla_vieja(conexion):
    """`dni` y `code` tenían UNIQUE, y SQLite no permite DROP COLUMN sobre una
    columna con esa restricción — hay que reconstruir la tabla entera.

    Por cada fila vieja se da de alta un empleado con sus datos personales
    (Puesto queda "Sin especificar", a completar después). Las filas que
    tenían username y contraseña cargados pasan a la tabla nueva, linkeadas
    a su empleado nuevo vía employee_id; las que no, quedan solo como
    empleados (no correspondía que siguieran siendo un "usuario" del
    sistema)."""
    filas = conexion.execute(f"SELECT * FROM {TABLA} ORDER BY id").fetchall()

    filas_con_login = []
    for fila in filas:
        cursor = conexion.execute(
            f"""
            INSERT INTO {TABLA_EMPLOYEES}
                (position, name, last_name, dni, email, birth_date, phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("Sin especificar", fila["name"], fila["last_name"], fila["dni"],
             fila["email"], fila["birth_date"], fila["phone"], fila["status"]),
        )
        id_empleado = cursor.lastrowid
        if fila["username"] and fila["password"]:
            filas_con_login.append((fila, id_empleado))

    conexion.execute(f"ALTER TABLE {TABLA} RENAME TO {TABLA}_viejo")
    conexion.execute(f"CREATE TABLE {TABLA} ({_COLUMNAS_FINALES})")

    for fila, id_empleado in filas_con_login:
        conexion.execute(
            f"""
            INSERT INTO {TABLA}
                (id, username, password, role, employee_id, failed_attempts, locked_until,
                 sort_order, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fila["id"], fila["username"], fila["password"], fila["role"], id_empleado,
             fila["failed_attempts"], fila["locked_until"], fila["sort_order"], fila["status"]),
        )

    conexion.execute(f"DROP TABLE {TABLA}_viejo")
