import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    """App Flask con una base SQLite nueva y vacía por test, aislada de data/database.db."""
    monkeypatch.setattr("src.db.connection.DB_PATH", str(tmp_path / "test.db"))

    from src.app import create_app

    application = create_app()
    application.config.update(TESTING=True)
    return application


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
