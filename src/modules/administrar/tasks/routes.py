from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required
from src.breadcrumbs import migas
from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.tasks.logic import (
    agregar_comentario,
    cerrar_tarea,
    crear_tarea,
    listar_comentarios,
    listar_tareas,
    marcar_vista,
    obtener_asignados_ids,
    obtener_por_id,
    obtener_sucursales_ids_tarea,
    reabrir_tarea,
    visible_para_sucursales,
)
from src.modules.administrar.user.logic import listar_usuarios

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tareas")


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index")]
    piezas.append(("Tareas", "tasks.listar") if ultimos else "Tareas")
    piezas.extend(ultimos)
    return migas(*piezas)


def _branch_ids_del_form():
    return [int(valor) for valor in request.form.getlist("branch_ids") if valor.strip()]


def _assignee_ids_del_form():
    return [int(valor) for valor in request.form.getlist("assignee_ids") if valor.strip()]


def _sucursales_seleccionables():
    """IT puede asignar cualquier sucursal; los demás roles solo las propias."""
    if session.get("role") == "IT":
        return listar_sucursales()
    propias = set(session.get("branch_ids") or [])
    return [sucursal for sucursal in listar_sucursales() if sucursal["id"] in propias]


def _requiere_acceso_a_la_tarea(id_tarea):
    """None si la tarea es visible para las sucursales de la sesión; si no, un redirect listo para devolver."""
    if not visible_para_sucursales(id_tarea, session.get("branch_ids")):
        flash("No tenés acceso a esa tarea.", "error")
        return redirect(url_for("tasks.listar"))
    return None


@tasks_bp.route("/")
@login_required
def listar():
    tareas = listar_tareas(branch_ids=session.get("branch_ids"))
    return render_template("tasks/listar.html", tareas=tareas, migas=_migas())


@tasks_bp.route("/cerradas")
@login_required
def cerradas():
    tareas = listar_tareas(incluir_cerradas=True, branch_ids=session.get("branch_ids"))
    return render_template("tasks/cerradas.html", tareas=tareas, migas=_migas("Cerradas"))


@tasks_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    sucursales = _sucursales_seleccionables()
    usuarios = listar_usuarios()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip() or None
        try:
            id_tarea = crear_tarea(
                title=title,
                description=description,
                created_by=session["user_id"],
                created_by_username=session.get("username"),
                branch_ids=_branch_ids_del_form(),
                assignee_ids=_assignee_ids_del_form(),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "tasks/formulario.html",
                sucursales=sucursales,
                sucursales_seleccionadas=_branch_ids_del_form(),
                usuarios=usuarios,
                asignados_seleccionados=_assignee_ids_del_form(),
                title=title,
                description=description,
                migas=_migas("Nueva tarea"),
            )
        flash("Tarea creada.", "success")
        return redirect(url_for("tasks.detalle", id_tarea=id_tarea))

    return render_template(
        "tasks/formulario.html",
        sucursales=sucursales,
        sucursales_seleccionadas=[],
        usuarios=usuarios,
        asignados_seleccionados=[],
        title="",
        description="",
        migas=_migas("Nueva tarea"),
    )


@tasks_bp.route("/<int:id_tarea>")
@login_required
def detalle(id_tarea):
    tarea = obtener_por_id(id_tarea)
    if tarea is None:
        flash("La tarea no existe.", "error")
        return redirect(url_for("tasks.listar"))

    redireccion = _requiere_acceso_a_la_tarea(id_tarea)
    if redireccion:
        return redireccion

    marcar_vista(id_tarea, session["user_id"])

    ids_sucursales = obtener_sucursales_ids_tarea(id_tarea)
    ids_asignados = obtener_asignados_ids(id_tarea)

    return render_template(
        "tasks/detalle.html",
        tarea=tarea,
        comentarios=listar_comentarios(id_tarea),
        sucursales_nombres=", ".join(
            sucursal["name"] for sucursal in listar_sucursales() if sucursal["id"] in ids_sucursales
        ),
        asignados_nombres=", ".join(
            usuario["username"] for usuario in listar_usuarios() if usuario["id"] in ids_asignados
        ),
        migas=_migas(tarea["title"]),
    )


@tasks_bp.route("/<int:id_tarea>/comentario", methods=["POST"])
@login_required
def comentar(id_tarea):
    if obtener_por_id(id_tarea) is None:
        flash("La tarea no existe.", "error")
        return redirect(url_for("tasks.listar"))

    redireccion = _requiere_acceso_a_la_tarea(id_tarea)
    if redireccion:
        return redireccion

    mensaje = request.form.get("message", "").strip()
    try:
        agregar_comentario(id_tarea, session["user_id"], session.get("username"), mensaje)
    except ValidationError as error:
        flash(str(error), "error")

    return redirect(url_for("tasks.detalle", id_tarea=id_tarea))


@tasks_bp.route("/<int:id_tarea>/cerrar", methods=["POST"])
@login_required
def cerrar(id_tarea):
    if obtener_por_id(id_tarea) is None:
        flash("La tarea no existe.", "error")
        return redirect(url_for("tasks.listar"))

    redireccion = _requiere_acceso_a_la_tarea(id_tarea)
    if redireccion:
        return redireccion

    cerrar_tarea(id_tarea)
    flash("Tarea cerrada.", "success")
    return redirect(url_for("tasks.detalle", id_tarea=id_tarea))


@tasks_bp.route("/<int:id_tarea>/reabrir", methods=["POST"])
@login_required
def reabrir(id_tarea):
    if obtener_por_id(id_tarea) is None:
        flash("La tarea no existe.", "error")
        return redirect(url_for("tasks.listar"))

    redireccion = _requiere_acceso_a_la_tarea(id_tarea)
    if redireccion:
        return redireccion

    reabrir_tarea(id_tarea)
    flash("Tarea reabierta.", "success")
    return redirect(url_for("tasks.detalle", id_tarea=id_tarea))
