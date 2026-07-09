from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.breadcrumbs import migas
from src.constants.validations import parsear_fecha_visual
from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.employees.logic import (
    actualizar_empleado,
    borrar_empleado,
    crear_empleado,
    listar_empleados,
    obtener_por_id,
    obtener_sucursales_ids,
    reactivar_empleado,
)

employees_bp = Blueprint("employees", __name__, url_prefix="/empleados")


def _migas(*ultimos):
    piezas = [
        ("Sistema de gestión", "administrar.index"),
        ("Administración", "administracion.index"),
    ]
    piezas.append(("Empleados", "employees.listar") if ultimos else "Empleados")
    piezas.extend(ultimos)
    return migas(*piezas)


def _fecha_nacimiento_del_form():
    cadena = request.form.get("birth_date", "").strip()
    return parsear_fecha_visual(cadena) if cadena else None


def _branch_ids_del_form():
    return [int(valor) for valor in request.form.getlist("branch_ids") if valor.strip()]


def _datos_del_form():
    return {
        "position": request.form.get("position", "").strip(),
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "dni": request.form.get("dni", "").strip(),
        "birth_date": _fecha_nacimiento_del_form(),
        "email": request.form.get("email", "").strip() or None,
        "phone": request.form.get("phone", "").strip() or None,
        "emergency_contact_name": request.form.get("emergency_contact_name", "").strip() or None,
        "emergency_contact_phone": request.form.get("emergency_contact_phone", "").strip() or None,
        "branch_ids": _branch_ids_del_form(),
    }


@employees_bp.route("/")
@login_required
def listar():
    empleados = listar_empleados()
    return render_template("employees/listar.html", empleados=empleados, migas=_migas())


@employees_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    sucursales = listar_sucursales()

    if request.method == "POST":
        try:
            datos = _datos_del_form()
            crear_empleado(**datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "employees/formulario.html",
                empleado={**dict(request.form), "id": None},
                accion="nueva",
                sucursales=sucursales,
                sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Nuevo empleado"),
            )
        flash("Empleado creado.", "success")
        return redirect(url_for("employees.listar"))

    return render_template(
        "employees/formulario.html", empleado=None, accion="nueva", sucursales=sucursales,
        sucursales_seleccionadas=[], migas=_migas("Nuevo empleado"),
    )


@employees_bp.route("/<int:id_empleado>/editar", methods=["GET", "POST"])
@login_required
def editar(id_empleado):
    empleado = obtener_por_id(id_empleado)
    if empleado is None:
        flash("El empleado no existe.", "error")
        return redirect(url_for("employees.listar"))

    sucursales = listar_sucursales()

    if request.method == "POST":
        try:
            datos = _datos_del_form()
            actualizar_empleado(id_empleado, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "employees/formulario.html",
                empleado={**dict(request.form), "id": id_empleado},
                accion="editar",
                sucursales=sucursales,
                sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Editar empleado"),
            )
        flash("Empleado actualizado.", "success")
        return redirect(url_for("employees.listar"))

    return render_template(
        "employees/formulario.html", empleado=dict(empleado), accion="editar", sucursales=sucursales,
        sucursales_seleccionadas=obtener_sucursales_ids(id_empleado), migas=_migas("Editar empleado"),
    )


@employees_bp.route("/<int:id_empleado>/borrar", methods=["POST"])
@login_required
def borrar(id_empleado):
    if obtener_por_id(id_empleado) is None:
        flash("El empleado no existe.", "error")
        return redirect(url_for("employees.listar"))

    borrar_empleado(id_empleado)
    flash("Empleado borrado.", "success")
    return redirect(url_for("employees.listar"))


@employees_bp.route("/borrados")
@login_required
def borrados():
    empleados = [e for e in listar_empleados(incluir_borrados=True) if e["status"] == 0]
    return render_template("employees/borrados.html", empleados=empleados, migas=_migas("Borrados"))


@employees_bp.route("/<int:id_empleado>/reactivar", methods=["POST"])
@login_required
def reactivar(id_empleado):
    if obtener_por_id(id_empleado) is None:
        flash("El empleado no existe.", "error")
        return redirect(url_for("employees.borrados"))

    reactivar_empleado(id_empleado)
    flash("Empleado reactivado.", "success")
    return redirect(url_for("employees.borrados"))
