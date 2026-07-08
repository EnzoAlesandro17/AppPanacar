from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.validaciones.vehicle_brands.logic import listar_marcas
from src.modules.administrar.vehicles.logic import (
    actualizar_vehiculo,
    borrar_vehiculo,
    crear_vehiculo,
    listar_vehiculos,
    obtener_por_id,
    reactivar_vehiculo,
)

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")


def _parsear_numero(valor, campo, tipo):
    valor = valor.strip()
    if not valor:
        return None
    try:
        return tipo(valor)
    except ValueError:
        raise ValidationError(f"{campo} debe ser un número.")


def _datos_del_form():
    return {
        "brand_id": _parsear_numero(request.form.get("brand_id", ""), "brand_id", int),
        "model": request.form.get("model", "").strip(),
        "year": _parsear_numero(request.form.get("year", ""), "year", int),
        "license_plate": request.form.get("license_plate", "").strip(),
        "color": request.form.get("color", "").strip() or None,
        "chassis_number": request.form.get("chassis_number", "").strip() or None,
        "engine_number": request.form.get("engine_number", "").strip() or None,
    }


@vehicles_bp.route("/")
@login_required
def listar():
    vehiculos = listar_vehiculos()
    return render_template("vehicles/listar.html", vehiculos=vehiculos)


@vehicles_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_vehiculo(**datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "vehicles/formulario.html", vehiculo=datos, accion="nueva", marcas=listar_marcas()
            )
        flash("Vehículo creado.", "success")
        return redirect(url_for("vehicles.listar"))

    return render_template("vehicles/formulario.html", vehiculo=None, accion="nueva", marcas=listar_marcas())


@vehicles_bp.route("/<int:id_vehiculo>/editar", methods=["GET", "POST"])
@login_required
def editar(id_vehiculo):
    vehiculo = obtener_por_id(id_vehiculo)
    if vehiculo is None:
        flash("El vehículo no existe.", "error")
        return redirect(url_for("vehicles.listar"))

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            actualizar_vehiculo(id_vehiculo, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "vehicles/formulario.html",
                vehiculo={**datos, "id": id_vehiculo},
                accion="editar",
                marcas=listar_marcas(),
            )
        flash("Vehículo actualizado.", "success")
        return redirect(url_for("vehicles.listar"))

    return render_template(
        "vehicles/formulario.html", vehiculo=dict(vehiculo), accion="editar", marcas=listar_marcas()
    )


@vehicles_bp.route("/<int:id_vehiculo>/borrar", methods=["POST"])
@login_required
def borrar(id_vehiculo):
    if obtener_por_id(id_vehiculo) is None:
        flash("El vehículo no existe.", "error")
        return redirect(url_for("vehicles.listar"))

    borrar_vehiculo(id_vehiculo)
    flash("Vehículo borrado.", "success")
    return redirect(url_for("vehicles.listar"))


@vehicles_bp.route("/borrados")
@login_required
def borrados():
    vehiculos = [v for v in listar_vehiculos(incluir_borrados=True) if v["status"] == 0]
    return render_template("vehicles/borrados.html", vehiculos=vehiculos)


@vehicles_bp.route("/<int:id_vehiculo>/reactivar", methods=["POST"])
@login_required
def reactivar(id_vehiculo):
    if obtener_por_id(id_vehiculo) is None:
        flash("El vehículo no existe.", "error")
        return redirect(url_for("vehicles.borrados"))

    reactivar_vehiculo(id_vehiculo)
    flash("Vehículo reactivado.", "success")
    return redirect(url_for("vehicles.borrados"))
