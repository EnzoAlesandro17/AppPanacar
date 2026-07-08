from src.db.connection import obtener_conexion
from src.modules.administrar.validaciones.vehicle_brands.db import TABLA as TABLA_VEHICLE_BRANDS

TABLA = "products"
TABLA_COMPATIBILIDAD = "product_compatibility"


def crear_tabla():
    """Crea la tabla de productos si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT NOT NULL,
                description TEXT NOT NULL,
                stock INTEGER,
                wholesale_price REAL NOT NULL,
                retail_price REAL NOT NULL,
                product_type TEXT NOT NULL DEFAULT 'Autoparte',
                oem_code TEXT,
                side TEXT,
                condition TEXT,
                supplier TEXT,
                location TEXT,
                purchase_date TEXT,
                purchase_price REAL,
                status INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA})")]
        columnas_nuevas = {
            "product_type": "TEXT NOT NULL DEFAULT 'Autoparte'",
            "oem_code": "TEXT",
            "side": "TEXT",
            "condition": "TEXT",
            "supplier": "TEXT",
            "location": "TEXT",
            "purchase_date": "TEXT",
            "purchase_price": "REAL",
        }
        for columna, definicion in columnas_nuevas.items():
            if columna not in columnas:
                conexion.execute(f"ALTER TABLE {TABLA} ADD COLUMN {columna} {definicion}")

        conexion.commit()


def crear_tabla_compatibilidad():
    """Crea la tabla de compatibilidad producto-vehículo si no existe todavía."""
    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA_COMPATIBILIDAD} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES {TABLA}(id),
                brand_vehicle_id INTEGER NOT NULL REFERENCES {TABLA_VEHICLE_BRANDS}(id),
                model TEXT NOT NULL,
                year INTEGER
            )
            """
        )

        columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({TABLA_COMPATIBILIDAD})")]
        if "brand_vehicle" in columnas and "brand_vehicle_id" not in columnas:
            # Migración: brand_vehicle era texto libre; pasa a ser una FK a vehicle_brands,
            # dando de alta en el catálogo cualquier marca que ya estuviera cargada como texto.
            conexion.execute(
                f"ALTER TABLE {TABLA_COMPATIBILIDAD} "
                f"ADD COLUMN brand_vehicle_id INTEGER REFERENCES {TABLA_VEHICLE_BRANDS}(id)"
            )
            marcas_existentes = conexion.execute(
                f"SELECT DISTINCT brand_vehicle FROM {TABLA_COMPATIBILIDAD}"
            ).fetchall()
            for fila in marcas_existentes:
                conexion.execute(
                    f"INSERT INTO {TABLA_VEHICLE_BRANDS} (name) VALUES (?) ON CONFLICT(name) DO NOTHING",
                    (fila["brand_vehicle"],),
                )
            conexion.execute(
                f"""
                UPDATE {TABLA_COMPATIBILIDAD}
                SET brand_vehicle_id = (
                    SELECT id FROM {TABLA_VEHICLE_BRANDS}
                    WHERE name = {TABLA_COMPATIBILIDAD}.brand_vehicle
                )
                """
            )
            conexion.execute(f"ALTER TABLE {TABLA_COMPATIBILIDAD} DROP COLUMN brand_vehicle")

        conexion.commit()
