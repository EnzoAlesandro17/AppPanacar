from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.breadcrumbs import migas
from src.exceptions import ValidationError
from src.modules.administrar.informacion_util.logic import (
    actualizar_enlace,
    borrar_enlace,
    crear_enlace,
    listar_enlaces,
    obtener_por_id,
    reactivar_enlace,
    reordenar_enlaces,
)

informacion_util_bp = Blueprint("informacion_util", __name__, url_prefix="/links-utiles")


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index")]
    piezas.append(("Links útiles", "informacion_util.listar") if ultimos else "Links útiles")
    piezas.extend(ultimos)
    return migas(*piezas)


def _datos_del_form():
    return {
        "label": request.form.get("label", "").strip(),
        "url": request.form.get("url", "").strip(),
        "observations": request.form.get("observations", "").strip() or None,
    }


@informacion_util_bp.route("/")
@login_required
def listar():
    enlaces = listar_enlaces()
    return render_template("informacion_util/listar.html", enlaces=enlaces, migas=_migas())


@informacion_util_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_enlace(**datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "informacion_util/formulario.html", enlace=datos, accion="nueva",
                migas=_migas("Nuevo enlace"),
            )
        flash("Enlace creado.", "success")
        return redirect(url_for("informacion_util.listar"))

    return render_template(
        "informacion_util/formulario.html", enlace=None, accion="nueva", migas=_migas("Nuevo enlace")
    )


@informacion_util_bp.route("/<int:id_enlace>/editar", methods=["GET", "POST"])
@login_required
def editar(id_enlace):
    enlace = obtener_por_id(id_enlace)
    if enlace is None:
        flash("El enlace no existe.", "error")
        return redirect(url_for("informacion_util.listar"))

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            actualizar_enlace(id_enlace, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "informacion_util/formulario.html", enlace={**datos, "id": id_enlace}, accion="editar",
                migas=_migas("Editar enlace"),
            )
        flash("Enlace actualizado.", "success")
        return redirect(url_for("informacion_util.listar"))

    return render_template(
        "informacion_util/formulario.html", enlace=dict(enlace), accion="editar",
        migas=_migas("Editar enlace"),
    )


@informacion_util_bp.route("/<int:id_enlace>/borrar", methods=["POST"])
@login_required
def borrar(id_enlace):
    if obtener_por_id(id_enlace) is None:
        flash("El enlace no existe.", "error")
        return redirect(url_for("informacion_util.listar"))

    borrar_enlace(id_enlace)
    flash("Enlace borrado.", "success")
    return redirect(url_for("informacion_util.listar"))


@informacion_util_bp.route("/borrados")
@login_required
def borrados():
    enlaces = [e for e in listar_enlaces(incluir_borrados=True) if e["status"] == 0]
    return render_template("informacion_util/borrados.html", enlaces=enlaces, migas=_migas("Borrados"))


@informacion_util_bp.route("/<int:id_enlace>/reactivar", methods=["POST"])
@login_required
def reactivar(id_enlace):
    if obtener_por_id(id_enlace) is None:
        flash("El enlace no existe.", "error")
        return redirect(url_for("informacion_util.borrados"))

    reactivar_enlace(id_enlace)
    flash("Enlace reactivado.", "success")
    return redirect(url_for("informacion_util.borrados"))


@informacion_util_bp.route("/reordenar", methods=["POST"])
@login_required
def reordenar():
    datos = request.get_json(silent=True) or {}
    reordenar_enlaces(datos.get("orden", []))
    return "", 204
