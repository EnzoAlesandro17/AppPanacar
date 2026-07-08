from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.insurance_companies.logic import (
    actualizar_aseguradora,
    borrar_aseguradora,
    crear_aseguradora,
    listar_aseguradoras,
    obtener_por_id,
    reactivar_aseguradora,
)

insurance_companies_bp = Blueprint("insurance_companies", __name__, url_prefix="/insurance-companies")


@insurance_companies_bp.route("/")
@login_required
def listar():
    aseguradoras = listar_aseguradoras()
    return render_template("insurance_companies/listar.html", aseguradoras=aseguradoras)


@insurance_companies_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            crear_aseguradora(name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "insurance_companies/formulario.html", aseguradora={"name": name}, accion="nueva"
            )
        flash("Compañía de seguro creada.", "success")
        return redirect(url_for("insurance_companies.listar"))

    return render_template("insurance_companies/formulario.html", aseguradora=None, accion="nueva")


@insurance_companies_bp.route("/<int:id_aseguradora>/editar", methods=["GET", "POST"])
@login_required
def editar(id_aseguradora):
    aseguradora = obtener_por_id(id_aseguradora)
    if aseguradora is None:
        flash("La compañía de seguro no existe.", "error")
        return redirect(url_for("insurance_companies.listar"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            actualizar_aseguradora(id_aseguradora, name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "insurance_companies/formulario.html",
                aseguradora={"id": id_aseguradora, "name": name},
                accion="editar",
            )
        flash("Compañía de seguro actualizada.", "success")
        return redirect(url_for("insurance_companies.listar"))

    return render_template(
        "insurance_companies/formulario.html", aseguradora=dict(aseguradora), accion="editar"
    )


@insurance_companies_bp.route("/<int:id_aseguradora>/borrar", methods=["POST"])
@login_required
def borrar(id_aseguradora):
    if obtener_por_id(id_aseguradora) is None:
        flash("La compañía de seguro no existe.", "error")
        return redirect(url_for("insurance_companies.listar"))

    borrar_aseguradora(id_aseguradora)
    flash("Compañía de seguro borrada.", "success")
    return redirect(url_for("insurance_companies.listar"))


@insurance_companies_bp.route("/borrados")
@login_required
def borrados():
    aseguradoras = [a for a in listar_aseguradoras(incluir_borrados=True) if a["status"] == 0]
    return render_template("insurance_companies/borrados.html", aseguradoras=aseguradoras)


@insurance_companies_bp.route("/<int:id_aseguradora>/reactivar", methods=["POST"])
@login_required
def reactivar(id_aseguradora):
    if obtener_por_id(id_aseguradora) is None:
        flash("La compañía de seguro no existe.", "error")
        return redirect(url_for("insurance_companies.borrados"))

    reactivar_aseguradora(id_aseguradora)
    flash("Compañía de seguro reactivada.", "success")
    return redirect(url_for("insurance_companies.borrados"))
