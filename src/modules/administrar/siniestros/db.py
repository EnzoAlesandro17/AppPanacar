from src.db.connection import obtener_conexion
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.clients.db import TABLA as TABLA_CLIENTS
from src.modules.administrar.user.db import TABLA as TABLA_USERS
from src.modules.administrar.validaciones.claim_statuses.db import TABLA as TABLA_CLAIM_STATUSES
from src.modules.administrar.validaciones.insurance_companies.db import TABLA as TABLA_INSURANCE_COMPANIES
from src.modules.administrar.vehicles.db import TABLA as TABLA_VEHICLES

TABLA = "siniestros"
TABLA_HISTORIAL = "siniestro_status_history"


def crear_tabla():
    """Crea la tabla de siniestros y la de historial de estados si no existen todavía.

    A diferencia de Clientes/Vehículos/Stock, la sucursal es una FK simple (no
    N:N): un siniestro se abre y se gestiona desde un único lugar concreto
    (ver RODO.txt)."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES {TABLA_CLIENTS}(id),
                vehicle_id INTEGER NOT NULL REFERENCES {TABLA_VEHICLES}(id),
                insurance_company_id INTEGER REFERENCES {TABLA_INSURANCE_COMPANIES}(id),
                claim_status_id INTEGER NOT NULL REFERENCES {TABLA_CLAIM_STATUSES}(id),
                branch_id INTEGER NOT NULL REFERENCES {TABLA_BRANCHES}(id),
                opened_date TEXT NOT NULL,
                description TEXT,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_HISTORIAL} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siniestro_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                previous_status_id INTEGER REFERENCES {TABLA_CLAIM_STATUSES}(id),
                new_status_id INTEGER NOT NULL REFERENCES {TABLA_CLAIM_STATUSES}(id),
                changed_by INTEGER REFERENCES {TABLA_USERS}(id),
                changed_by_username TEXT,
                changed_at TEXT NOT NULL
            )
            """
        )

        conexion.commit()
