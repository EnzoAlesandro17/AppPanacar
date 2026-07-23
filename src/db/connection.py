import os
import re
import sqlite3
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from src.config import DATABASE_URL

# Permite aislar cada test en su propio schema de Postgres (ver tests/conftest.py):
# antes cada test usaba un archivo SQLite temporal propio, un schema cumple el
# mismo rol de "base vacía y aislada" sin pagar el costo de crear una base física.
SCHEMA = os.environ.get("DB_SCHEMA", "public")

_INSERT_RE = re.compile(r"^\s*INSERT\s+INTO", re.IGNORECASE)
_RETURNING_RE = re.compile(r"\bRETURNING\b", re.IGNORECASE)
_UNIQUE_KEY_RE = re.compile(r"^Key \(([^)]+)\)=")


def _mensaje_unique_sqlite_like(error):
    """Arma un mensaje con el formato de sqlite3 ("UNIQUE constraint failed:
    tabla.columna") a partir del error de Postgres, para que
    _traducir_error_integridad() de cada módulo (escrito para sqlite3) siga
    funcionando sin cambios."""
    tabla = error.diag.table_name or "?"
    detalle = error.diag.message_detail or ""
    match = _UNIQUE_KEY_RE.match(detalle)
    columnas = match.group(1) if match else "?"
    columnas = columnas.replace(", ", ".").replace(",", ".")
    return f"UNIQUE constraint failed: {tabla}.{columnas}"


class _CursorCompatible:
    """Envoltorio fino sobre el cursor de psycopg: mismo cursor, solo suma
    `.lastrowid` (que psycopg no tiene) para que crear_x() en cada módulo
    siga leyendo el id generado igual que con sqlite3."""

    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor)


class _ConexionCompatible:
    """Envoltorio sobre la conexión de psycopg para que el resto del código
    (escrito en su momento contra sqlite3.Connection) no tenga que cambiar:
    placeholders `?` en vez de `%s`, `conexion.execute(...).lastrowid`
    después de un INSERT, y `except sqlite3.IntegrityError` en los catches."""

    def __init__(self, conexion):
        self._conexion = conexion

    def execute(self, sql, parametros=()):
        sql_pg = sql.replace("?", "%s")
        agrega_returning = bool(_INSERT_RE.match(sql_pg)) and not _RETURNING_RE.search(sql_pg)
        if agrega_returning:
            sql_pg = f"{sql_pg.rstrip().rstrip(';')} RETURNING id"

        try:
            cursor = self._conexion.execute(sql_pg, parametros)
        except psycopg.errors.UniqueViolation as error:
            self._conexion.rollback()
            raise sqlite3.IntegrityError(_mensaje_unique_sqlite_like(error)) from error

        lastrowid = None
        if agrega_returning:
            fila = cursor.fetchone()
            lastrowid = fila["id"] if fila else None
        return _CursorCompatible(cursor, lastrowid)

    def executemany(self, sql, secuencia_parametros):
        sql_pg = sql.replace("?", "%s")
        try:
            with self._conexion.cursor() as cursor:
                cursor.executemany(sql_pg, list(secuencia_parametros))
        except psycopg.errors.UniqueViolation as error:
            self._conexion.rollback()
            raise sqlite3.IntegrityError(_mensaje_unique_sqlite_like(error)) from error

    def commit(self):
        self._conexion.commit()

    def close(self):
        self._conexion.close()


class GestorDB:
    @staticmethod
    def conectar():
        conexion = psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)
        conexion.execute(f'SET search_path TO "{SCHEMA}"')
        return _ConexionCompatible(conexion)


@contextmanager
def obtener_conexion():
    """Context manager que cierra la conexión automáticamente al salir del bloque."""
    conexion = GestorDB.conectar()
    try:
        yield conexion
    finally:
        conexion.close()


def columnas_existentes(conexion, tabla):
    """Nombres de columna de una tabla ya creada (reemplaza a `PRAGMA
    table_info` de sqlite3), para las migraciones idempotentes de cada
    módulo: agregar/quitar una columna en crear_tabla() solo si hace falta."""
    filas = conexion.execute(
        "SELECT column_name AS name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = ?",
        (tabla,),
    )
    return [fila["name"] for fila in filas]
