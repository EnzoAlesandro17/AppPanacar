from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import (
    actualizar_sucursal,
    borrar_sucursal,
    crear_sucursal,
    listar_sucursales,
    obtener_por_id,
    reactivar_sucursal,
)

branches_bp = Blueprint("branches", __name__, url_prefix="/branches")


def _datos_del_form():
    return {
        "name": request.form.get("name", "").strip(),
        "code": request.form.get("code", "").strip() or None,
        "country": request.form.get("country", "").strip() or None,
        "city": request.form.get("city", "").strip() or None,
        "address": request.form.get("address", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "phone": request.form.get("phone", "").strip() or None,
    }


@branches_bp.route("/")
@login_required
def listar():
    sucursales = listar_sucursales()
    return render_template("branches/listar.html", sucursales=sucursales)


@branches_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_sucursal(**datos)
        except ValidationError as error:
            flash(str(error))
            return render_template("branches/formulario.html", sucursal=datos, accion="nueva")
        flash("Sucursal creada.")
        return redirect(url_for("branches.listar"))

    return render_template("branches/formulario.html", sucursal=None, accion="nueva")


@branches_bp.route("/<int:id_sucursal>/editar", methods=["GET", "POST"])
@login_required
def editar(id_sucursal):
    sucursal = obtener_por_id(id_sucursal)
    if sucursal is None:
        flash("La sucursal no existe.")
        return redirect(url_for("branches.listar"))

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            actualizar_sucursal(id_sucursal, **datos)
        except ValidationError as error:
            flash(str(error))
            return render_template(
                "branches/formulario.html", sucursal={**datos, "id": id_sucursal}, accion="editar"
            )
        flash("Sucursal actualizada.")
        return redirect(url_for("branches.listar"))

    return render_template("branches/formulario.html", sucursal=dict(sucursal), accion="editar")


@branches_bp.route("/<int:id_sucursal>/borrar", methods=["POST"])
@login_required
def borrar(id_sucursal):
    if obtener_por_id(id_sucursal) is None:
        flash("La sucursal no existe.")
        return redirect(url_for("branches.listar"))

    borrar_sucursal(id_sucursal)
    flash("Sucursal borrada.")
    return redirect(url_for("branches.listar"))


@branches_bp.route("/borrados")
@login_required
def borrados():
    sucursales = [s for s in listar_sucursales(incluir_borrados=True) if s["status"] == 0]
    return render_template("branches/borrados.html", sucursales=sucursales)


@branches_bp.route("/<int:id_sucursal>/reactivar", methods=["POST"])
@login_required
def reactivar(id_sucursal):
    if obtener_por_id(id_sucursal) is None:
        flash("La sucursal no existe.")
        return redirect(url_for("branches.borrados"))

    reactivar_sucursal(id_sucursal)
    flash("Sucursal reactivada.")
    return redirect(url_for("branches.borrados"))
