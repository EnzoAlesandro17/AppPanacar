import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg
import pytest

from src.config import DATABASE_URL


@pytest.fixture
def app(monkeypatch):
    """App Flask con su propio schema de Postgres, vacío y aislado del resto
    (mismo rol que cumplía el archivo SQLite temporal antes de Postgres)."""
    schema = f"test_{uuid.uuid4().hex[:16]}"

    with psycopg.connect(DATABASE_URL, autocommit=True) as admin_conexion:
        admin_conexion.execute(f'CREATE SCHEMA "{schema}"')

    monkeypatch.setattr("src.db.connection.SCHEMA", schema)

    from src.app import create_app

    application = create_app()
    application.config.update(TESTING=True)

    yield application

    with psycopg.connect(DATABASE_URL, autocommit=True) as admin_conexion:
        admin_conexion.execute(f'DROP SCHEMA "{schema}" CASCADE')


@pytest.fixture
def client(app):
    return app.test_client()


def extraer_csrf(html):
    """Extrae el csrf_token de un <input type="hidden" name="csrf_token" ...> de la respuesta."""
    match = re.search(rb'name="csrf_token" value="([^"]+)"', html)
    return match.group(1).decode()


def extraer_csrf_meta(html):
    """Extrae el csrf-token de la <meta> de base.html (el que usa reorder.js por header)."""
    match = re.search(rb'name="csrf-token" content="([^"]+)"', html)
    return match.group(1).decode()


@pytest.fixture
def admin(client):
    """Crea un usuario IT directo en la base (sin pasar por /usuarios/nuevo) y lo loguea. Devuelve el client logueado."""
    from src.modules.administrar.user.logic import crear_usuario

    crear_usuario(username="admin_test", password="clave-segura-123", role="IT")

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "admin_test", "password": "clave-segura-123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def asesor(client):
    """Crea un Asesor (sin permiso de gestión de usuarios) y lo loguea. Devuelve el client logueado."""
    from src.modules.administrar.user.logic import crear_usuario

    crear_usuario(username="asesor_test", password="clave-segura-123", role="Asesor")

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "asesor_test", "password": "clave-segura-123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def backoffice(client):
    """Crea un BackOffice y lo loguea. Devuelve el client logueado."""
    from src.modules.administrar.user.logic import crear_usuario

    crear_usuario(username="backoffice_test", password="clave-segura-123", role="BackOffice")

    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": "backoffice_test", "password": "clave-segura-123"},
        follow_redirects=True,
    )
    return client
