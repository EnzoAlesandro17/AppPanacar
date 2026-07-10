from src.modules.administrar.branches.logic import crear_sucursal
from src.modules.administrar.tasks.logic import (
    agregar_comentario,
    cerrar_tarea,
    contar_no_vistas,
    crear_tarea,
    listar_comentarios,
    listar_tareas,
    marcar_vista,
    obtener_por_id,
    reabrir_tarea,
    visible_para_sucursales,
)
from src.modules.administrar.user.logic import crear_usuario
from tests.conftest import extraer_csrf


def _crear_usuario_id(username="ana"):
    return crear_usuario(username=username, password="clave-segura-123", role="Asesor")


def _login(client, username, role="Asesor", branch_ids=None, password="clave-segura-123"):
    crear_usuario(username=username, password=password, role=role, branch_ids=branch_ids)
    resp = client.get("/usuarios/login")
    token = extraer_csrf(resp.data)
    client.post(
        "/usuarios/login",
        data={"csrf_token": token, "username": username, "password": password},
        follow_redirects=True,
    )
    return client


def test_crear_tarea_y_listarla(app):
    id_ana = _crear_usuario_id("ana")
    id_tarea = crear_tarea(
        title="Revisar stock de pastillas de freno", description="Falta cargar el nuevo lote",
        created_by=id_ana, created_by_username="ana",
    )

    tareas = listar_tareas()
    assert len(tareas) == 1
    assert tareas[0]["id"] == id_tarea
    assert tareas[0]["closed_at"] is None


def test_agregar_comentario_actualiza_updated_at_y_queda_en_el_hilo(app):
    id_ana = _crear_usuario_id("ana")
    id_tarea = crear_tarea(title="Pedido a proveedor", description=None, created_by=id_ana, created_by_username="ana")
    tarea_original = obtener_por_id(id_tarea)

    agregar_comentario(id_tarea, user_id=id_ana, username="ana", message="Ya lo pedí, llega el jueves.")

    comentarios = listar_comentarios(id_tarea)
    assert len(comentarios) == 1
    assert comentarios[0]["message"] == "Ya lo pedí, llega el jueves."

    tarea_actualizada = obtener_por_id(id_tarea)
    assert tarea_actualizada["updated_at"] >= tarea_original["updated_at"]


def test_cerrar_y_reabrir_tarea(app):
    id_ana = _crear_usuario_id("ana")
    id_tarea = crear_tarea(
        title="Arreglar la puerta del depósito", description=None, created_by=id_ana, created_by_username="ana"
    )

    cerrar_tarea(id_tarea)
    assert obtener_por_id(id_tarea)["closed_at"] is not None
    assert listar_tareas() == []
    assert len(listar_tareas(incluir_cerradas=True)) == 1

    reabrir_tarea(id_tarea)
    assert obtener_por_id(id_tarea)["closed_at"] is None
    assert len(listar_tareas()) == 1


def test_tarea_sin_sucursales_es_visible_para_cualquier_lista(app):
    id_ana = _crear_usuario_id("ana")
    sucursal = crear_sucursal(name="Sucursal Ajena Tarea")
    id_tarea = crear_tarea(title="Tarea general", description=None, created_by=id_ana, created_by_username="ana")

    assert visible_para_sucursales(id_tarea, [sucursal])
    assert visible_para_sucursales(id_tarea, [])


def test_tarea_con_sucursal_solo_visible_si_comparte_alguna(app):
    id_ana = _crear_usuario_id("ana")
    sucursal_propia = crear_sucursal(name="Sucursal Propia Tarea")
    sucursal_ajena = crear_sucursal(name="Sucursal Ajena Tarea Dos")
    id_tarea = crear_tarea(
        title="Tarea de sucursal", description=None, created_by=id_ana, created_by_username="ana",
        branch_ids=[sucursal_propia],
    )

    assert visible_para_sucursales(id_tarea, [sucursal_propia])
    assert not visible_para_sucursales(id_tarea, [sucursal_ajena])


def test_listar_tareas_filtra_por_sucursal(app):
    id_ana = _crear_usuario_id("ana")
    sucursal_a = crear_sucursal(name="Sucursal Filtro Tarea A")
    sucursal_b = crear_sucursal(name="Sucursal Filtro Tarea B")
    crear_tarea(title="Solo A", description=None, created_by=id_ana, created_by_username="ana", branch_ids=[sucursal_a])
    crear_tarea(title="Solo B", description=None, created_by=id_ana, created_by_username="ana", branch_ids=[sucursal_b])
    crear_tarea(title="Sin sucursal", description=None, created_by=id_ana, created_by_username="ana")

    titulos = {t["title"] for t in listar_tareas(branch_ids=[sucursal_a])}

    assert titulos == {"Solo A", "Sin sucursal"}


def test_contar_no_vistas_baja_al_marcar_vista(app):
    id_ana = _crear_usuario_id("ana")
    id_espectador = _crear_usuario_id("espectador")
    id_tarea = crear_tarea(title="Tarea nueva", description=None, created_by=id_ana, created_by_username="ana")

    assert contar_no_vistas(user_id=id_espectador) == 1

    marcar_vista(id_tarea, user_id=id_espectador)
    assert contar_no_vistas(user_id=id_espectador) == 0

    agregar_comentario(id_tarea, user_id=id_ana, username="ana", message="Novedad")
    assert contar_no_vistas(user_id=id_espectador) == 1


def test_crear_tarea_por_http_y_comentar(client):
    _login(client, "creador_tarea", role="Asesor")

    resp = client.get("/tareas/nueva")
    token = extraer_csrf(resp.data)
    resp = client.post(
        "/tareas/nueva",
        data={"csrf_token": token, "title": "Cambiar cubierta del auto de cortesía", "description": ""},
        follow_redirects=True,
    )
    assert b"Tarea creada" in resp.data

    id_tarea = obtener_por_id(1)["id"]
    resp = client.get(f"/tareas/{id_tarea}")
    token = extraer_csrf(resp.data)
    resp = client.post(
        f"/tareas/{id_tarea}/comentario",
        data={"csrf_token": token, "message": "Ya se consiguió la cubierta."},
        follow_redirects=True,
    )
    assert "Ya se consiguió la cubierta.".encode() in resp.data


def test_badge_sube_y_baja_por_http(client):
    sucursal = crear_sucursal(name="Sucursal Badge")
    creador = _login(client, "creador_badge", role="Asesor", branch_ids=[sucursal])

    resp = creador.get("/tareas/nueva")
    token = extraer_csrf(resp.data)
    creador.post(
        "/tareas/nueva",
        data={"csrf_token": token, "title": "Tarea con badge", "description": "", "branch_ids": [str(sucursal)]},
        follow_redirects=True,
    )

    otro_cliente = client
    espectador = _login(otro_cliente, "espectador_badge", role="Asesor", branch_ids=[sucursal])
    resp = espectador.get("/")
    assert b'class="badge-tareas"' in resp.data

    id_tarea = listar_tareas(branch_ids=[sucursal])[0]["id"]
    espectador.get(f"/tareas/{id_tarea}")

    resp = espectador.get("/")
    assert b'class="badge-tareas"' not in resp.data


def test_asesor_de_otra_sucursal_no_ve_tarea_ajena_por_http(client):
    sucursal_a = crear_sucursal(name="Sucursal Tarea HTTP A")
    sucursal_b = crear_sucursal(name="Sucursal Tarea HTTP B")

    creador = _login(client, "creador_tarea_b", role="Asesor", branch_ids=[sucursal_b])
    resp = creador.get("/tareas/nueva")
    token = extraer_csrf(resp.data)
    creador.post(
        "/tareas/nueva",
        data={"csrf_token": token, "title": "Exclusiva de B", "description": "", "branch_ids": [str(sucursal_b)]},
        follow_redirects=True,
    )
    id_tarea = listar_tareas(branch_ids=[sucursal_b])[0]["id"]

    asesor_a = _login(client, "asesor_tarea_a", role="Asesor", branch_ids=[sucursal_a])
    resp = asesor_a.get("/tareas/")
    assert b"Exclusiva de B" not in resp.data

    resp = asesor_a.get(f"/tareas/{id_tarea}", follow_redirects=True)
    assert "No tenés acceso a esa tarea.".encode() in resp.data
