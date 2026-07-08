from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.clients.logic import (
    actualizar_cliente,
    borrar_cliente,
    crear_cliente,
    listar_clientes,
    obtener_por_id,
    reactivar_cliente,
)
from src.modules.administrar.validaciones.insurance_companies.logic import listar_aseguradoras

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


def _datos_del_form():
    insurance_company_id = request.form.get("insurance_company_id", "").strip()
    return {
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "dni_cuit": request.form.get("dni_cuit", "").strip(),
        "phone": request.form.get("phone", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "insurance_company_id": int(insurance_company_id) if insurance_company_id else None,
    }


@clients_bp.route("/")
@login_required
def listar():
    clientes = listar_clientes()
    return render_template("clients/listar.html", clientes=clientes)


@clients_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    aseguradoras = listar_aseguradoras()

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_cliente(**datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "clients/formulario.html", cliente=datos, accion="nueva", aseguradoras=aseguradoras
            )
        flash("Cliente creado.", "success")
        return redirect(url_for("clients.listar"))

    return render_template(
        "clients/formulario.html", cliente=None, accion="nueva", aseguradoras=aseguradoras
    )


@clients_bp.route("/<int:id_cliente>/editar", methods=["GET", "POST"])
@login_required
def editar(id_cliente):
    cliente = obtener_por_id(id_cliente)
    if cliente is None:
        flash("El cliente no existe.", "error")
        return redirect(url_for("clients.listar"))

    aseguradoras = listar_aseguradoras()

    if request.method == "POST":
        datos = _datos_del_form()
        quitar_insurance_company_id = not request.form.get("insurance_company_id", "").strip()
        try:
            actualizar_cliente(
                id_cliente, quitar_insurance_company_id=quitar_insurance_company_id, **datos
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "clients/formulario.html",
                cliente={**datos, "id": id_cliente},
                accion="editar",
                aseguradoras=aseguradoras,
            )
        flash("Cliente actualizado.", "success")
        return redirect(url_for("clients.listar"))

    return render_template(
        "clients/formulario.html", cliente=dict(cliente), accion="editar", aseguradoras=aseguradoras
    )


@clients_bp.route("/<int:id_cliente>/borrar", methods=["POST"])
@login_required
def borrar(id_cliente):
    if obtener_por_id(id_cliente) is None:
        flash("El cliente no existe.", "error")
        return redirect(url_for("clients.listar"))

    borrar_cliente(id_cliente)
    flash("Cliente borrado.", "success")
    return redirect(url_for("clients.listar"))


@clients_bp.route("/borrados")
@login_required
def borrados():
    clientes = [c for c in listar_clientes(incluir_borrados=True) if c["status"] == 0]
    return render_template("clients/borrados.html", clientes=clientes)


@clients_bp.route("/<int:id_cliente>/reactivar", methods=["POST"])
@login_required
def reactivar(id_cliente):
    if obtener_por_id(id_cliente) is None:
        flash("El cliente no existe.", "error")
        return redirect(url_for("clients.borrados"))

    reactivar_cliente(id_cliente)
    flash("Cliente reactivado.", "success")
    return redirect(url_for("clients.borrados"))
