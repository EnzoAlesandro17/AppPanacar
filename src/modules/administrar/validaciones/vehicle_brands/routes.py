from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.vehicle_brands.logic import (
    actualizar_marca,
    borrar_marca,
    crear_marca,
    listar_marcas,
    obtener_por_id,
    reactivar_marca,
)

vehicle_brands_bp = Blueprint("vehicle_brands", __name__, url_prefix="/vehicle-brands")


@vehicle_brands_bp.route("/")
@login_required
def listar():
    marcas = listar_marcas()
    return render_template("vehicle_brands/listar.html", marcas=marcas)


@vehicle_brands_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            crear_marca(name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template("vehicle_brands/formulario.html", marca={"name": name}, accion="nueva")
        flash("Marca creada.", "success")
        return redirect(url_for("vehicle_brands.listar"))

    return render_template("vehicle_brands/formulario.html", marca=None, accion="nueva")


@vehicle_brands_bp.route("/<int:id_marca>/editar", methods=["GET", "POST"])
@login_required
def editar(id_marca):
    marca = obtener_por_id(id_marca)
    if marca is None:
        flash("La marca no existe.", "error")
        return redirect(url_for("vehicle_brands.listar"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            actualizar_marca(id_marca, name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "vehicle_brands/formulario.html", marca={"id": id_marca, "name": name}, accion="editar"
            )
        flash("Marca actualizada.", "success")
        return redirect(url_for("vehicle_brands.listar"))

    return render_template("vehicle_brands/formulario.html", marca=dict(marca), accion="editar")


@vehicle_brands_bp.route("/<int:id_marca>/borrar", methods=["POST"])
@login_required
def borrar(id_marca):
    if obtener_por_id(id_marca) is None:
        flash("La marca no existe.", "error")
        return redirect(url_for("vehicle_brands.listar"))

    borrar_marca(id_marca)
    flash("Marca borrada.", "success")
    return redirect(url_for("vehicle_brands.listar"))


@vehicle_brands_bp.route("/borrados")
@login_required
def borrados():
    marcas = [m for m in listar_marcas(incluir_borrados=True) if m["status"] == 0]
    return render_template("vehicle_brands/borrados.html", marcas=marcas)


@vehicle_brands_bp.route("/<int:id_marca>/reactivar", methods=["POST"])
@login_required
def reactivar(id_marca):
    if obtener_por_id(id_marca) is None:
        flash("La marca no existe.", "error")
        return redirect(url_for("vehicle_brands.borrados"))

    reactivar_marca(id_marca)
    flash("Marca reactivada.", "success")
    return redirect(url_for("vehicle_brands.borrados"))
