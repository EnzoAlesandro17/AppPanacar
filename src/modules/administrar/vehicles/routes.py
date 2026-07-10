from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados
from src.breadcrumbs import migas
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.validaciones.vehicle_brands.logic import listar_marcas
from src.modules.administrar.vehicles.logic import (
    actualizar_vehiculo,
    borrar_vehiculo,
    crear_vehiculo,
    listar_vehiculos,
    obtener_por_id,
    obtener_sucursales_ids_vehiculo,
    reactivar_vehiculo,
    visible_para_sucursales,
)
from src.permissions import puede_ver_eliminados

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/vehiculos")


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index")]
    piezas.append(("Vehículos", "vehicles.listar") if ultimos else "Vehículos")
    piezas.extend(ultimos)
    return migas(*piezas)


def _parsear_numero(valor, campo, tipo):
    valor = valor.strip()
    if not valor:
        return None
    try:
        return tipo(valor)
    except ValueError:
        raise ValidationError(f"{campo} debe ser un número.")


def _branch_ids_del_form():
    return [int(valor) for valor in request.form.getlist("branch_ids") if valor.strip()]


def _sucursales_seleccionables():
    """IT puede asignar cualquier sucursal; los demás roles solo las propias."""
    if session.get("role") == "IT":
        return listar_sucursales()
    propias = set(session.get("branch_ids") or [])
    return [sucursal for sucursal in listar_sucursales() if sucursal["id"] in propias]


def _requiere_acceso_al_vehiculo(id_vehiculo):
    """None si el vehículo es visible para las sucursales de la sesión; si no, un redirect listo para devolver."""
    if not visible_para_sucursales(id_vehiculo, session.get("branch_ids")):
        flash("No tenés acceso a ese vehículo.", "error")
        return redirect(url_for("vehicles.listar"))
    return None


def _datos_del_form():
    return {
        "brand_id": _parsear_numero(request.form.get("brand_id", ""), "brand_id", int),
        "model": request.form.get("model", "").strip(),
        "year": _parsear_numero(request.form.get("year", ""), "year", int),
        "license_plate": request.form.get("license_plate", "").strip(),
        "color": request.form.get("color", "").strip() or None,
        "chassis_number": request.form.get("chassis_number", "").strip() or None,
        "engine_number": request.form.get("engine_number", "").strip() or None,
        "branch_ids": _branch_ids_del_form(),
    }


@vehicles_bp.route("/")
@login_required
def listar():
    vehiculos = listar_vehiculos(branch_ids=session.get("branch_ids"))
    return render_template("vehicles/listar.html", vehiculos=vehiculos, migas=_migas())


@vehicles_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    sucursales = _sucursales_seleccionables()

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_vehiculo(**datos)
        except RegistroBorradoExistente as error:
            borrado_existente_id = None
            if visible_para_sucursales(error.id_existente, session.get("branch_ids")):
                flash(
                    "Ya existe un vehículo borrado con ese dominio. Podés reactivarlo en vez de crear uno nuevo.",
                    "error",
                )
                borrado_existente_id = error.id_existente
            else:
                flash("Ya existe un vehículo con ese dominio.", "error")
            return render_template(
                "vehicles/formulario.html", vehiculo=datos, accion="nueva", marcas=listar_marcas(),
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                borrado_existente_id=borrado_existente_id, migas=_migas("Nuevo vehículo"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "vehicles/formulario.html", vehiculo=datos, accion="nueva", marcas=listar_marcas(),
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Nuevo vehículo"),
            )
        flash("Vehículo creado.", "success")
        return redirect(url_for("vehicles.listar"))

    return render_template(
        "vehicles/formulario.html", vehiculo=None, accion="nueva", marcas=listar_marcas(),
        sucursales=sucursales, sucursales_seleccionadas=[], migas=_migas("Nuevo vehículo"),
    )


@vehicles_bp.route("/<int:id_vehiculo>/editar", methods=["GET", "POST"])
@login_required
def editar(id_vehiculo):
    vehiculo = obtener_por_id(id_vehiculo)
    if vehiculo is None:
        flash("El vehículo no existe.", "error")
        return redirect(url_for("vehicles.listar"))

    redireccion = _requiere_acceso_al_vehiculo(id_vehiculo)
    if redireccion:
        return redireccion

    sucursales = _sucursales_seleccionables()

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
                sucursales=sucursales,
                sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Editar vehículo"),
            )
        flash("Vehículo actualizado.", "success")
        return redirect(url_for("vehicles.listar"))

    return render_template(
        "vehicles/formulario.html", vehiculo=dict(vehiculo), accion="editar", marcas=listar_marcas(),
        sucursales=sucursales, sucursales_seleccionadas=obtener_sucursales_ids_vehiculo(id_vehiculo),
        migas=_migas("Editar vehículo"),
    )


@vehicles_bp.route("/<int:id_vehiculo>/borrar", methods=["POST"])
@login_required
def borrar(id_vehiculo):
    if obtener_por_id(id_vehiculo) is None:
        flash("El vehículo no existe.", "error")
        return redirect(url_for("vehicles.listar"))

    redireccion = _requiere_acceso_al_vehiculo(id_vehiculo)
    if redireccion:
        return redireccion

    borrar_vehiculo(id_vehiculo)
    flash("Vehículo borrado.", "success")
    return redirect(url_for("vehicles.listar"))


@vehicles_bp.route("/borrados")
@login_required
@requiere_ver_eliminados
def borrados():
    vehiculos = [v for v in listar_vehiculos(incluir_borrados=True) if v["status"] == 0]
    return render_template("vehicles/borrados.html", vehiculos=vehiculos, migas=_migas("Borrados"))


@vehicles_bp.route("/<int:id_vehiculo>/reactivar", methods=["POST"])
@login_required
def reactivar(id_vehiculo):
    destino = "vehicles.borrados" if puede_ver_eliminados(session.get("role")) else "vehicles.listar"

    if obtener_por_id(id_vehiculo) is None:
        flash("El vehículo no existe.", "error")
        return redirect(url_for(destino))

    redireccion = _requiere_acceso_al_vehiculo(id_vehiculo)
    if redireccion:
        return redireccion

    reactivar_vehiculo(id_vehiculo)
    flash("Vehículo reactivado.", "success")
    return redirect(url_for(destino))
