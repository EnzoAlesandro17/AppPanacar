from tests.conftest import extraer_csrf


def _id_por_username(username):
    from src.db.connection import obtener_conexion

    with obtener_conexion() as conexion:
        return conexion.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()["id"]


def test_asesor_puede_entrar_a_su_propio_perfil(asesor):
    """A diferencia de /usuarios/<id>/editar, /perfil no exige gestión de usuarios."""
    resp = asesor.get("/usuarios/perfil")

    assert resp.status_code == 200
    assert b"Mi cuenta" in resp.data


def test_asesor_no_puede_entrar_a_editar_otro_usuario(asesor):
    id_asesor = _id_por_username("asesor_test")

    resp = asesor.get(f"/usuarios/{id_asesor}/editar", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_perfil_no_muestra_el_campo_rol(asesor):
    resp = asesor.get("/usuarios/perfil")

    assert b'name="role"' not in resp.data


def test_perfil_actualiza_datos_propios(asesor):
    resp = asesor.get("/usuarios/perfil")
    token = extraer_csrf(resp.data)

    asesor.post(
        "/usuarios/perfil",
        data={
            "csrf_token": token, "name": "Ana", "last_name": "Editada",
            "dni": "20000001", "phone": "3415551234",
        },
        follow_redirects=True,
    )

    from src.db.connection import obtener_conexion
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            "SELECT last_name, phone FROM users WHERE username = 'asesor_test'"
        ).fetchone()

    assert fila["last_name"] == "Editada"
    assert fila["phone"] == "3415551234"


def test_perfil_ignora_intento_de_escalar_rol_y_sucursal(asesor):
    """Aunque se mande role/branch_id a mano (form manipulado), no deben tocarse."""
    resp = asesor.get("/usuarios/perfil")
    token = extraer_csrf(resp.data)

    asesor.post(
        "/usuarios/perfil",
        data={
            "csrf_token": token, "name": "Ana", "last_name": "Asesora",
            "dni": "20000001", "role": "Admin", "branch_id": "999",
        },
        follow_redirects=True,
    )

    from src.db.connection import obtener_conexion
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            "SELECT role, branch_id FROM users WHERE username = 'asesor_test'"
        ).fetchone()

    assert fila["role"] == "Asesor"
    assert fila["branch_id"] is None


def test_perfil_requiere_login(client):
    resp = client.get("/usuarios/perfil", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/usuarios/login"
