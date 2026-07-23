from src.db.connection import columnas_existentes, obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.clients.db import TABLA as TABLA_CLIENTS
from src.modules.administrar.user.db import TABLA as TABLA_USERS
from src.modules.administrar.validaciones.claim_statuses.db import TABLA as TABLA_CLAIM_STATUSES
from src.modules.administrar.validaciones.claim_types.db import TABLA as TABLA_CLAIM_TYPES
from src.modules.administrar.validaciones.insurance_companies.db import TABLA as TABLA_INSURANCE_COMPANIES
from src.modules.administrar.vehicles.db import TABLA as TABLA_VEHICLES

TABLA = "siniestros"
TABLA_HISTORIAL = "siniestro_status_history"
TABLA_COMENTARIOS = "siniestro_comentarios"


def crear_tabla():
    """Crea la tabla de siniestros y la de historial de estados si no existen todavía.

    A diferencia de Clientes/Vehículos/Stock, la sucursal es una FK simple (no
    N:N): un siniestro se abre y se gestiona desde un único lugar concreto
    (ver RODO.txt)."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES {TABLA_CLIENTS}(id),
                vehicle_id INTEGER NOT NULL REFERENCES {TABLA_VEHICLES}(id),
                insurance_company_id INTEGER REFERENCES {TABLA_INSURANCE_COMPANIES}(id),
                claim_type_id INTEGER REFERENCES {TABLA_CLAIM_TYPES}(id),
                claim_status_id INTEGER NOT NULL REFERENCES {TABLA_CLAIM_STATUSES}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                opened_date TEXT NOT NULL,
                description TEXT,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = columnas_existentes(conexion, TABLA)
        if "claim_type_id" not in columnas:
            conexion.execute(
                f"ALTER TABLE {TABLA} ADD COLUMN claim_type_id INTEGER REFERENCES {TABLA_CLAIM_TYPES}(id)"
            )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_HISTORIAL} (
                id SERIAL PRIMARY KEY,
                siniestro_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                previous_status_id INTEGER REFERENCES {TABLA_CLAIM_STATUSES}(id),
                new_status_id INTEGER NOT NULL REFERENCES {TABLA_CLAIM_STATUSES}(id),
                changed_by INTEGER REFERENCES {TABLA_USERS}(id),
                changed_by_username TEXT,
                changed_at TEXT NOT NULL
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_COMENTARIOS} (
                id SERIAL PRIMARY KEY,
                siniestro_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                comentario TEXT NOT NULL,
                changed_by INTEGER REFERENCES {TABLA_USERS}(id),
                changed_by_username TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        conexion.commit()
