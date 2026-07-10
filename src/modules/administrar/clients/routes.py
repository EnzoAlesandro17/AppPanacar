from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados
from src.breadcrumbs import migas
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.clients.logic import (
    actualizar_cliente,
    borrar_cliente,
    crear_cliente,
    listar_clientes,
    obtener_por_id,
    obtener_sucursales_ids_cliente,
    reactivar_cliente,
    visible_para_sucursales,
)
from src.permissions import puede_ver_eliminados

clients_bp = Blueprint("clients", __name__, url_prefix="/clientes")


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index")]
    piezas.append(("Clientes", "clients.listar") if ultimos else "Clientes")
    piezas.extend(ultimos)
    return migas(*piezas)


def _branch_ids_del_form():
    return [int(valor) for valor in request.form.getlist("branch_ids") if valor.strip()]


def _sucursales_seleccionables():
    """IT puede asignar cualquier sucursal; los demás roles solo las propias."""
    if session.get("role") == "IT":
        return listar_sucursales()
    propias = set(session.get("branch_ids") or [])
    return [sucursal for sucursal in listar_sucursales() if sucursal["id"] in propias]


def _requiere_acceso_al_cliente(id_cliente):
    """None si el cliente es visible para las sucursales de la sesión; si no, un redirect listo para devolver."""
    if not visible_para_sucursales(id_cliente, session.get("branch_ids")):
        flash("No tenés acceso a ese cliente.", "error")
        return redirect(url_for("clients.listar"))
    return None


def _datos_del_form():
    return {
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "dni_cuit": request.form.get("dni_cuit", "").strip(),
        "phone": request.form.get("phone", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "branch_ids": _branch_ids_del_form(),
    }


@clients_bp.route("/")
@login_required
def listar():
    clientes = listar_clientes(branch_ids=session.get("branch_ids"))
    return render_template("clients/listar.html", clientes=clientes, migas=_migas())


@clients_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    sucursales = _sucursales_seleccionables()

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_cliente(**datos)
        except RegistroBorradoExistente as error:
            borrado_existente_id = None
            if visible_para_sucursales(error.id_existente, session.get("branch_ids")):
                flash(
                    "Ya existe un cliente borrado con ese DNI/CUIT. Podés reactivarlo en vez de crear uno nuevo.",
                    "error",
                )
                borrado_existente_id = error.id_existente
            else:
                flash("Ya existe un cliente con ese DNI/CUIT.", "error")
            return render_template(
                "clients/formulario.html", cliente=datos, accion="nueva",
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                borrado_existente_id=borrado_existente_id, migas=_migas("Nuevo cliente"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "clients/formulario.html", cliente=datos, accion="nueva",
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Nuevo cliente"),
            )
        flash("Cliente creado.", "success")
        return redirect(url_for("clients.listar"))

    return render_template(
        "clients/formulario.html", cliente=None, accion="nueva",
        sucursales=sucursales, sucursales_seleccionadas=[], migas=_migas("Nuevo cliente")
    )


@clients_bp.route("/<int:id_cliente>/editar", methods=["GET", "POST"])
@login_required
def editar(id_cliente):
    cliente = obtener_por_id(id_cliente)
    if cliente is None:
        flash("El cliente no existe.", "error")
        return redirect(url_for("clients.listar"))

    redireccion = _requiere_acceso_al_cliente(id_cliente)
    if redireccion:
        return redireccion

    sucursales = _sucursales_seleccionables()

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            actualizar_cliente(id_cliente, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "clients/formulario.html", cliente={**datos, "id": id_cliente}, accion="editar",
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Editar cliente"),
            )
        flash("Cliente actualizado.", "success")
        return redirect(url_for("clients.listar"))

    return render_template(
        "clients/formulario.html", cliente=dict(cliente), accion="editar",
        sucursales=sucursales, sucursales_seleccionadas=obtener_sucursales_ids_cliente(id_cliente),
        migas=_migas("Editar cliente"),
    )


@clients_bp.route("/<int:id_cliente>/borrar", methods=["POST"])
@login_required
def borrar(id_cliente):
    if obtener_por_id(id_cliente) is None:
        flash("El cliente no existe.", "error")
        return redirect(url_for("clients.listar"))

    redireccion = _requiere_acceso_al_cliente(id_cliente)
    if redireccion:
        return redireccion

    borrar_cliente(id_cliente)
    flash("Cliente borrado.", "success")
    return redirect(url_for("clients.listar"))


@clients_bp.route("/borrados")
@login_required
@requiere_ver_eliminados
def borrados():
    clientes = [c for c in listar_clientes(incluir_borrados=True) if c["status"] == 0]
    return render_template("clients/borrados.html", clientes=clientes, migas=_migas("Borrados"))


@clients_bp.route("/<int:id_cliente>/reactivar", methods=["POST"])
@login_required
def reactivar(id_cliente):
    destino = "clients.borrados" if puede_ver_eliminados(session.get("role")) else "clients.listar"

    if obtener_por_id(id_cliente) is None:
        flash("El cliente no existe.", "error")
        return redirect(url_for(destino))

    redireccion = _requiere_acceso_al_cliente(id_cliente)
    if redireccion:
        return redireccion

    reactivar_cliente(id_cliente)
    flash("Cliente reactivado.", "success")
    return redirect(url_for(destino))
