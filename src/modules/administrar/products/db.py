from src.db.connection import obtener_conexion

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
                brand_vehicle TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER
            )
            """
        )
        conexion.commit()
