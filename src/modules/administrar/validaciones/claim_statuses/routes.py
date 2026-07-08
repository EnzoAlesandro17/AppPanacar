from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.breadcrumbs import migas
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.claim_statuses.logic import (
    actualizar_estado,
    borrar_estado,
    crear_estado,
    listar_estados,
    obtener_por_id,
    reactivar_estado,
    reordenar_estados,
)

claim_statuses_bp = Blueprint("claim_statuses", __name__, url_prefix="/estados-siniestro")


def _migas(*ultimos):
    piezas = [
        ("Sistema de gestión", "administrar.index"),
        ("Administración", "administracion.index"),
        ("Validaciones", "validaciones.index"),
    ]
    piezas.append(("Estados de siniestro", "claim_statuses.listar") if ultimos else "Estados de siniestro")
    piezas.extend(ultimos)
    return migas(*piezas)


@claim_statuses_bp.route("/")
@login_required
def listar():
    estados = listar_estados()
    return render_template("claim_statuses/listar.html", estados=estados, migas=_migas())


@claim_statuses_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            crear_estado(name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "claim_statuses/formulario.html", estado={"name": name}, accion="nueva",
                migas=_migas("Nuevo estado"),
            )
        flash("Estado creado.", "success")
        return redirect(url_for("claim_statuses.listar"))

    return render_template(
        "claim_statuses/formulario.html", estado=None, accion="nueva", migas=_migas("Nuevo estado")
    )


@claim_statuses_bp.route("/<int:id_estado>/editar", methods=["GET", "POST"])
@login_required
def editar(id_estado):
    estado = obtener_por_id(id_estado)
    if estado is None:
        flash("El estado no existe.", "error")
        return redirect(url_for("claim_statuses.listar"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            actualizar_estado(id_estado, name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "claim_statuses/formulario.html", estado={"id": id_estado, "name": name}, accion="editar",
                migas=_migas("Editar estado"),
            )
        flash("Estado actualizado.", "success")
        return redirect(url_for("claim_statuses.listar"))

    return render_template(
        "claim_statuses/formulario.html", estado=dict(estado), accion="editar",
        migas=_migas("Editar estado"),
    )


@claim_statuses_bp.route("/<int:id_estado>/borrar", methods=["POST"])
@login_required
def borrar(id_estado):
    if obtener_por_id(id_estado) is None:
        flash("El estado no existe.", "error")
        return redirect(url_for("claim_statuses.listar"))

    borrar_estado(id_estado)
    flash("Estado borrado.", "success")
    return redirect(url_for("claim_statuses.listar"))


@claim_statuses_bp.route("/borrados")
@login_required
def borrados():
    estados = [e for e in listar_estados(incluir_borrados=True) if e["status"] == 0]
    return render_template("claim_statuses/borrados.html", estados=estados, migas=_migas("Borrados"))


@claim_statuses_bp.route("/<int:id_estado>/reactivar", methods=["POST"])
@login_required
def reactivar(id_estado):
    if obtener_por_id(id_estado) is None:
        flash("El estado no existe.", "error")
        return redirect(url_for("claim_statuses.borrados"))

    reactivar_estado(id_estado)
    flash("Estado reactivado.", "success")
    return redirect(url_for("claim_statuses.borrados"))


@claim_statuses_bp.route("/reordenar", methods=["POST"])
@login_required
def reordenar():
    datos = request.get_json(silent=True) or {}
    reordenar_estados(datos.get("orden", []))
    return "", 204
